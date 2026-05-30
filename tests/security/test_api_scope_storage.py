import csv
import io

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.db import IntegrityError, transaction

from modules.accounts.models import (
    ApiScope,
    GroupApiScopeGrant,
    UserApiScopeGrant,
)
from nads26.api_permissions import (
    CANONICAL_API_SCOPES,
    get_effective_api_scope_decision,
    get_effective_api_scopes,
)


@pytest.fixture
def api_scope_storage_cleanup():
    usernames = [
        'api-scope-user',
        'api-effective-user',
        'api-missing-user',
        'api-superuser',
        'api-staff-user',
        'api-report-user',
        'api-plan-user',
        'api-plan-staff',
        'api-plan-superuser',
    ]
    group_names = ['api-scope-group', 'api-effective-group', 'api_hymns_readers']
    User.objects.filter(username__in=usernames).delete()
    Group.objects.filter(name__in=group_names).delete()
    yield
    User.objects.filter(username__in=usernames).delete()
    Group.objects.filter(name__in=group_names).delete()
    ApiScope.objects.filter(scope__in=CANONICAL_API_SCOPES).update(active=True)


@pytest.fixture
def api_scopes(api_scope_storage_cleanup):
    return {
        scope.scope: scope
        for scope in ApiScope.objects.filter(scope__in=CANONICAL_API_SCOPES)
    }


def test_canonical_api_scopes_are_seeded(api_scopes):
    assert set(api_scopes) == {
        'api:hymns:read',
        'api:hymns:write',
        'api:hymns:upload',
        'api:humnos:read',
        'api:humnos:write',
    }
    assert all(scope.active for scope in api_scopes.values())


def test_api_scope_grants_are_unique(api_scopes):
    user = User.objects.create_user(username='api-scope-user')
    group = Group.objects.create(name='api-scope-group')
    scope = api_scopes['api:hymns:read']

    UserApiScopeGrant.objects.create(user=user, scope=scope)
    GroupApiScopeGrant.objects.create(group=group, scope=scope)

    with pytest.raises(IntegrityError), transaction.atomic():
        UserApiScopeGrant.objects.create(user=user, scope=scope)

    with pytest.raises(IntegrityError), transaction.atomic():
        GroupApiScopeGrant.objects.create(group=group, scope=scope)


def test_effective_scopes_merge_enabled_group_and_user_grants(api_scopes):
    user = User.objects.create_user(username='api-effective-user')
    group = Group.objects.create(name='api-effective-group')
    user.groups.add(group)

    UserApiScopeGrant.objects.create(
        user=user,
        scope=api_scopes['api:hymns:write'],
    )
    GroupApiScopeGrant.objects.create(
        group=group,
        scope=api_scopes['api:hymns:read'],
    )
    UserApiScopeGrant.objects.create(
        user=user,
        scope=api_scopes['api:hymns:upload'],
        enabled=False,
    )
    inactive_scope = api_scopes['api:humnos:read']
    inactive_scope.active = False
    inactive_scope.save(update_fields=['active'])
    GroupApiScopeGrant.objects.create(group=group, scope=inactive_scope)

    assert get_effective_api_scopes(user) == frozenset(
        {'api:hymns:read', 'api:hymns:write'}
    )
    decision = get_effective_api_scope_decision(user, 'api:hymns:read')
    assert decision.allowed is True
    assert decision.reason == 'effective_scope'


def test_effective_scope_missing_scope_decision(api_scopes):
    user = User.objects.create_user(username='api-missing-user')

    decision = get_effective_api_scope_decision(user, 'api:hymns:read')

    assert decision.allowed is False
    assert decision.reason == 'missing_scope'
    assert decision.effective_scopes == frozenset()


def test_superuser_bypass_is_audited_without_grants(api_scopes):
    user = User.objects.create_superuser(
        username='api-superuser',
        email='superuser@example.test',
        password='password',
    )

    decision = get_effective_api_scope_decision(user, 'api:hymns:write')

    assert decision.allowed is True
    assert decision.reason == 'superuser'
    assert decision.effective_scopes == frozenset()
    assert get_effective_api_scopes(user) == frozenset()


def test_staff_receives_no_default_api_scope(api_scopes):
    user = User.objects.create_user(username='api-staff-user', is_staff=True)

    decision = get_effective_api_scope_decision(user, 'api:hymns:read')

    assert get_effective_api_scopes(user) == frozenset()
    assert decision.allowed is False
    assert decision.reason == 'missing_scope'


def test_report_api_effective_scopes_command_is_report_only(api_scopes):
    user = User.objects.create_user(username='api-report-user')
    UserApiScopeGrant.objects.create(
        user=user,
        scope=api_scopes['api:hymns:read'],
    )
    output = io.StringIO()

    call_command(
        'report_api_effective_scopes',
        '--username',
        user.username,
        stdout=output,
    )

    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert rows == [
        {
            'username': 'api-report-user',
            'user_id': str(user.id),
            'is_active': 'True',
            'is_staff': 'False',
            'is_superuser': 'False',
            'bypass_reason': '',
            'effective_scopes': 'api:hymns:read',
        }
    ]


def test_plan_api_scope_grants_command_is_report_only(api_scopes, tmp_path):
    user = User.objects.create_user(username='api-plan-user')
    staff = User.objects.create_user(username='api-plan-staff', is_staff=True)
    superuser = User.objects.create_superuser(
        username='api-plan-superuser',
        email='api-plan-superuser@example.test',
        password='password',
    )
    group = Group.objects.create(name='api_hymns_readers')
    staff.groups.add(group)
    GroupApiScopeGrant.objects.create(
        group=group,
        scope=api_scopes['api:hymns:read'],
    )
    report_csv = tmp_path / 'api-permission-review.csv'
    report_csv.write_text(
        '\n'.join(
            [
                'time,user_id,endpoint,method,scope,decision,reason',
                f',{user.id},/api/hymns/,GET,api:hymns:read,deny,missing_scope',
                f',{staff.id},/api/hymns/,GET,api:hymns:read,deny,missing_scope',
                (
                    f',{superuser.id},/api/hymns/,POST,api:hymns:write,'
                    'allow,superuser'
                ),
            ]
        ),
        encoding='utf-8',
    )
    output = io.StringIO()
    counts_before = (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
    )

    call_command(
        'plan_api_scope_grants',
        '--report-csv',
        str(report_csv),
        stdout=output,
    )

    assert counts_before == (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
    )
    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert {
        'plan_type': 'user_review',
        'principal_type': 'user',
        'principal': 'api-plan-user',
        'scope': 'api:hymns:read',
        'action': 'review_need',
        'source': 'report_only_logs',
        'reason': 'missing_scope',
        'notes': (
            'Prefer assigning the user to a reviewed role group; use direct grant '
            'only for exceptions.'
        ),
    } in rows
    assert {
        'plan_type': 'user_review',
        'principal_type': 'user',
        'principal': 'api-plan-staff',
        'scope': 'api:hymns:read',
        'action': 'covered_by_group',
        'source': 'report_only_logs',
        'reason': 'group_grant_preferred',
        'notes': 'User is already covered by enabled group grants.',
    } in rows
    assert {
        'plan_type': 'superuser_bypass',
        'principal_type': 'superuser',
        'principal': '*',
        'scope': 'api:hymns:write',
        'action': 'no_grant',
        'source': 'report_only_logs',
        'reason': 'superuser_bypass',
        'notes': '1 report-only decision(s); keep visible in audit.',
    } in rows
