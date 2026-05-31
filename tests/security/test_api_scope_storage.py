import csv
import io
import uuid

import pytest
from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import IntegrityError, transaction

from modules.accounts.models import (
    ApiScope,
    ApiScopeGrantAudit,
    GroupApiScopeGrant,
    UserApiScopeGrant,
)
from modules.accounts.management.commands.apply_api_scope_reviewed_plan import (
    Command as ApplyApiScopeReviewedPlanCommand,
)
from modules.accounts.management.commands.rollback_api_scope_reviewed_plan import (
    Command as RollbackApiScopeReviewedPlanCommand,
)
from nads26.api_permissions import (
    CANONICAL_API_SCOPES,
    get_effective_api_scope_decision,
    get_effective_api_scopes,
)


pytestmark = [pytest.mark.api_scope, pytest.mark.mutating]


@pytest.fixture
def api_scope_test_namespace():
    suffix = uuid.uuid4().hex[:8]
    prefix = f't_{suffix}'
    ticket_prefix = f'SEC-API-TEST-{suffix.upper()}'

    class Namespace:
        def user(self, name):
            return f'{prefix}_{name}'

        def group(self, name):
            return f'{prefix}_{name}'

        def ticket(self, name):
            return f'{ticket_prefix}-{name}'

        @property
        def user_prefix(self):
            return prefix

        @property
        def group_prefix(self):
            return prefix

        @property
        def ticket_prefix(self):
            return ticket_prefix

    return Namespace()


@pytest.fixture
def api_scope_storage_cleanup(api_scope_test_namespace):
    ApiScopeGrantAudit.objects.filter(
        ticket__startswith=api_scope_test_namespace.ticket_prefix
    ).delete()
    User.objects.filter(
        username__startswith=api_scope_test_namespace.user_prefix
    ).delete()
    Group.objects.filter(name__startswith=api_scope_test_namespace.group_prefix).delete()
    yield
    ApiScopeGrantAudit.objects.filter(
        ticket__startswith=api_scope_test_namespace.ticket_prefix
    ).delete()
    User.objects.filter(
        username__startswith=api_scope_test_namespace.user_prefix
    ).delete()
    Group.objects.filter(name__startswith=api_scope_test_namespace.group_prefix).delete()
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


def test_api_scope_grants_are_unique(api_scopes, api_scope_test_namespace):
    username = api_scope_test_namespace.user('api-scope-user')
    group_name = api_scope_test_namespace.group('api-scope-group')
    user = User.objects.create_user(username=username)
    group = Group.objects.create(name=group_name)
    scope = api_scopes['api:hymns:read']

    UserApiScopeGrant.objects.create(user=user, scope=scope)
    GroupApiScopeGrant.objects.create(group=group, scope=scope)

    with pytest.raises(IntegrityError), transaction.atomic():
        UserApiScopeGrant.objects.create(user=user, scope=scope)

    with pytest.raises(IntegrityError), transaction.atomic():
        GroupApiScopeGrant.objects.create(group=group, scope=scope)


def test_effective_scopes_merge_enabled_group_and_user_grants(
    api_scopes, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-effective-user')
    group_name = api_scope_test_namespace.group('api-effective-group')
    user = User.objects.create_user(username=username)
    group = Group.objects.create(name=group_name)
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


def test_effective_scope_missing_scope_decision(api_scopes, api_scope_test_namespace):
    user = User.objects.create_user(
        username=api_scope_test_namespace.user('api-missing-user')
    )

    decision = get_effective_api_scope_decision(user, 'api:hymns:read')

    assert decision.allowed is False
    assert decision.reason == 'missing_scope'
    assert decision.effective_scopes == frozenset()


def test_superuser_bypass_is_audited_without_grants(
    api_scopes, api_scope_test_namespace
):
    user = User.objects.create_superuser(
        username=api_scope_test_namespace.user('api-superuser'),
        email='superuser@example.test',
        password='password',
    )

    decision = get_effective_api_scope_decision(user, 'api:hymns:write')

    assert decision.allowed is True
    assert decision.reason == 'superuser'
    assert decision.effective_scopes == frozenset()
    assert get_effective_api_scopes(user) == frozenset()


def test_staff_receives_no_default_api_scope(api_scopes, api_scope_test_namespace):
    user = User.objects.create_user(
        username=api_scope_test_namespace.user('api-staff-user'),
        is_staff=True,
    )

    decision = get_effective_api_scope_decision(user, 'api:hymns:read')

    assert get_effective_api_scopes(user) == frozenset()
    assert decision.allowed is False
    assert decision.reason == 'missing_scope'


def test_report_api_effective_scopes_command_is_report_only(
    api_scopes, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-report-user')
    user = User.objects.create_user(username=username)
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
            'username': username,
            'user_id': str(user.id),
            'is_active': 'True',
            'is_staff': 'False',
            'is_superuser': 'False',
            'bypass_reason': '',
            'effective_scopes': 'api:hymns:read',
        }
    ]


def test_plan_api_scope_grants_command_is_report_only(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-plan-user')
    staff_username = api_scope_test_namespace.user('api-plan-staff')
    superuser_username = api_scope_test_namespace.user('api-plan-superuser')
    group_name = api_scope_test_namespace.group('api_hymns_readers')
    user = User.objects.create_user(username=username)
    staff = User.objects.create_user(username=staff_username, is_staff=True)
    superuser = User.objects.create_superuser(
        username=superuser_username,
        email=f'{superuser_username}@example.test',
        password='password',
    )
    group = Group.objects.create(name=group_name)
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
    # TODO(P7 Phase 4): replace global grant counts with namespace-scoped assertions.
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
        'principal': username,
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
        'principal': staff_username,
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


def test_apply_api_scope_reviewed_plan_dry_run_writes_nothing(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-apply-user')
    service_username = api_scope_test_namespace.user('api-apply-service')
    group_name = api_scope_test_namespace.group('api_humnos_readers')
    ticket_1 = api_scope_test_namespace.ticket('001')
    ticket_2 = api_scope_test_namespace.ticket('002')
    user = User.objects.create_user(username=username)
    service_user = User.objects.create_user(username=service_username)
    plan_csv = tmp_path / 'reviewed-api-scope-plan.csv'
    plan_csv.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,'
                    'ticket,rollback_of,notes'
                ),
                (
                    f'create_group,{group_name},,,1,Approved reader role,'
                    f'peter,2026-05-30,{ticket_1},,'
                ),
                (
                    f'create_group_grant,{group_name},,api:humnos:read,'
                    f'1,Approved reader scope,peter,2026-05-30,{ticket_1},,'
                ),
                (
                    f'assign_user_to_group,{group_name},{username},,'
                    f'1,Observed read need,peter,2026-05-30,{ticket_1},,'
                ),
                (
                    f'create_user_grant,,{service_username},api:humnos:read,'
                    '1,Temporary documented exception,peter,2026-05-30,'
                    f'{ticket_2},,'
                ),
            ]
        ),
        encoding='utf-8',
    )
    output = io.StringIO()
    # TODO(P7 Phase 4): replace global object counts with namespace-scoped assertions.
    counts_before = (
        Group.objects.count(),
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
        user.groups.count(),
        service_user.groups.count(),
    )

    call_command(
        'apply_api_scope_reviewed_plan',
        '--plan-file',
        str(plan_csv),
        stdout=output,
    )

    assert counts_before == (
        Group.objects.count(),
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
        user.groups.count(),
        service_user.groups.count(),
    )
    assert Group.objects.filter(name=group_name).exists() is False
    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert len(rows) == 4
    assert {row['dry_run'] for row in rows} == {'true'}
    assert {row['status'] for row in rows} == {'ok'}
    assert {row['plan_version'] for row in rows} == {'1'}
    assert all(len(row['plan_checksum']) == 64 for row in rows)
    assert all(len(row['audit_event']) == 32 for row in rows)
    assert {
        'create_group',
        'create_group_grant',
        'assign_user_to_group',
        'create_user_grant',
    } == {row['action'] for row in rows}
    assert all('dry-run only' in row['notes'] for row in rows)


def test_apply_api_scope_reviewed_plan_apply_without_confirm_writes_nothing(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-apply-user')
    group_name = api_scope_test_namespace.group('api_humnos_readers')
    ticket = api_scope_test_namespace.ticket('001')
    user = User.objects.create_user(username=username)
    group = Group.objects.create(name=group_name)
    plan_csv = tmp_path / 'reviewed-api-scope-plan.csv'
    plan_csv.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,'
                    'ticket,rollback_of,notes'
                ),
                (
                    f'assign_user_to_group,{group_name},{username},,'
                    f'1,Observed read need,peter,2026-05-30,{ticket},,'
                ),
            ]
        ),
        encoding='utf-8',
    )
    # TODO(P7 Phase 4): replace global grant/audit counts with scoped assertions.
    counts_before = (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
        user.groups.count(),
    )

    with pytest.raises(CommandError, match='--apply requires --confirm-apply'):
        call_command(
            'apply_api_scope_reviewed_plan',
            '--plan-file',
            str(plan_csv),
            '--apply',
        )

    assert counts_before == (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
        user.groups.count(),
    )
    assert user.groups.filter(name=group.name).exists() is False


def test_apply_api_scope_reviewed_plan_apply_with_confirm_writes_audit_and_grants(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-apply-user')
    service_username = api_scope_test_namespace.user('api-apply-service')
    group_name = api_scope_test_namespace.group('api_humnos_readers')
    ticket_1 = api_scope_test_namespace.ticket('001')
    ticket_2 = api_scope_test_namespace.ticket('002')
    user = User.objects.create_user(username=username)
    service_user = User.objects.create_user(username=service_username)
    plan_csv = tmp_path / 'reviewed-api-scope-plan.csv'
    plan_csv.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,'
                    'ticket,rollback_of,notes'
                ),
                (
                    f'create_group,{group_name},,,1,Approved reader role,'
                    f'peter,2026-05-30,{ticket_1},,'
                ),
                (
                    f'create_group_grant,{group_name},,api:humnos:read,'
                    f'1,Approved reader scope,peter,2026-05-30,{ticket_1},,'
                ),
                (
                    f'assign_user_to_group,{group_name},{username},,'
                    f'1,Observed read need,peter,2026-05-30,{ticket_1},,'
                ),
                (
                    f'create_user_grant,,{service_username},api:humnos:read,'
                    '1,Temporary documented exception,peter,2026-05-30,'
                    f'{ticket_2},,'
                ),
            ]
        ),
        encoding='utf-8',
    )
    output = io.StringIO()

    call_command(
        'apply_api_scope_reviewed_plan',
        '--plan-file',
        str(plan_csv),
        '--apply',
        '--confirm-apply',
        stdout=output,
    )

    group = Group.objects.get(name=group_name)
    assert user.groups.filter(name=group_name).exists() is True
    assert GroupApiScopeGrant.objects.filter(
        group=group,
        scope=api_scopes['api:humnos:read'],
        enabled=True,
    ).exists()
    assert UserApiScopeGrant.objects.filter(
        user=service_user,
        scope=api_scopes['api:humnos:read'],
        enabled=True,
    ).exists()

    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert len(rows) == 4
    assert {row['dry_run'] for row in rows} == {'false'}
    assert {row['status'] for row in rows} == {'applied'}

    audit_rows = ApiScopeGrantAudit.objects.filter(
        ticket__in=[ticket_1, ticket_2]
    ).order_by('row_number')
    assert audit_rows.count() == 4
    assert {audit.status for audit in audit_rows} == {'applied'}
    assert {audit.dry_run for audit in audit_rows} == {False}
    assert {audit.action for audit in audit_rows} == {
        'create_group',
        'create_group_grant',
        'assign_user_to_group',
        'create_user_grant',
    }
    assert all(audit.previous_state is not None for audit in audit_rows)
    assert all(audit.planned_state is not None for audit in audit_rows)
    assert all(audit.result for audit in audit_rows)


def test_apply_api_scope_reviewed_plan_transaction_failure_rolls_back(
    api_scopes, tmp_path, monkeypatch, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-apply-tx-user')
    group_name = api_scope_test_namespace.group('api_apply_tx_group')
    ticket = api_scope_test_namespace.ticket('TX')
    user = User.objects.create_user(username=username)
    plan_csv = tmp_path / 'reviewed-api-scope-plan.csv'
    plan_csv.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,'
                    'ticket,rollback_of,notes'
                ),
                (
                    f'create_group,{group_name},,,1,Approved tx role,'
                    f'peter,2026-05-30,{ticket},,'
                ),
                (
                    f'assign_user_to_group,{group_name},{username},,'
                    f'1,Observed tx need,peter,2026-05-30,{ticket},,'
                ),
            ]
        ),
        encoding='utf-8',
    )
    original_execute = ApplyApiScopeReviewedPlanCommand._execute_apply_action

    def fail_after_first_write(self, row):
        if (row.get('action') or '').strip() == 'assign_user_to_group':
            raise CommandError('injected transaction failure')
        return original_execute(self, row)

    monkeypatch.setattr(
        ApplyApiScopeReviewedPlanCommand,
        '_execute_apply_action',
        fail_after_first_write,
    )

    with pytest.raises(CommandError, match='injected transaction failure'):
        call_command(
            'apply_api_scope_reviewed_plan',
            '--plan-file',
            str(plan_csv),
            '--apply',
            '--confirm-apply',
        )

    assert Group.objects.filter(name=group_name).exists() is False
    assert user.groups.filter(name=group_name).exists() is False
    assert ApiScopeGrantAudit.objects.filter(ticket=ticket).exists() is False


def test_apply_api_scope_reviewed_plan_validation_blocks_bad_plan(
    api_scopes, tmp_path, api_scope_test_namespace
):
    group_name = api_scope_test_namespace.group('api_humnos_readers')
    plan_csv = tmp_path / 'bad-reviewed-api-scope-plan.csv'
    plan_csv.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,'
                    'ticket,rollback_of,notes'
                ),
                (
                    f'rollback_group_grant,{group_name},,api:humnos:read,'
                    'not-a-number,,peter,2026-05-30,,,'
                ),
            ]
        ),
        encoding='utf-8',
    )
    # TODO(P7 Phase 4): replace global grant/audit counts with scoped assertions.
    counts_before = (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
    )

    with pytest.raises(CommandError, match='reviewed plan validation failed'):
        call_command(
            'apply_api_scope_reviewed_plan',
            '--plan-file',
            str(plan_csv),
        )

    assert counts_before == (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
    )


def _write_rollback_plan(path, rows):
    path.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,rollback_of,reason,reviewed_by,'
                    'reviewed_at,ticket,notes'
                ),
                *rows,
            ]
        ),
        encoding='utf-8',
    )


def test_rollback_api_scope_reviewed_plan_dry_run_writes_nothing(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-rollback-user')
    service_username = api_scope_test_namespace.user('api-rollback-service')
    group_name = api_scope_test_namespace.group('api_rollback_readers')
    ticket = api_scope_test_namespace.ticket('RB')
    user = User.objects.create_user(username=username)
    service_user = User.objects.create_user(username=service_username)
    group = Group.objects.create(name=group_name)
    user.groups.add(group)
    GroupApiScopeGrant.objects.create(
        group=group,
        scope=api_scopes['api:humnos:read'],
    )
    UserApiScopeGrant.objects.create(
        user=service_user,
        scope=api_scopes['api:humnos:read'],
    )
    plan_csv = tmp_path / 'reviewed-api-scope-rollback-plan.csv'
    _write_rollback_plan(
        plan_csv,
        [
            (
                f'remove_user_from_group,{group_name},{username},,'
                f'apply-row-3,Rollback membership,peter,2026-05-30,{ticket},'
            ),
            (
                f'disable_group_grant,{group_name},,api:humnos:read,'
                f'apply-row-2,Rollback group grant,peter,2026-05-30,{ticket},'
            ),
            (
                f'disable_user_grant,,{service_username},api:humnos:read,'
                f'apply-row-4,Rollback user grant,peter,2026-05-30,{ticket},'
            ),
        ],
    )
    output = io.StringIO()
    # TODO(P7 Phase 4): replace global grant/audit counts with scoped assertions.
    counts_before = (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
        user.groups.count(),
    )

    call_command(
        'rollback_api_scope_reviewed_plan',
        '--plan-file',
        str(plan_csv),
        stdout=output,
    )

    assert counts_before == (
        UserApiScopeGrant.objects.count(),
        GroupApiScopeGrant.objects.count(),
        ApiScopeGrantAudit.objects.count(),
        user.groups.count(),
    )
    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert len(rows) == 3
    assert {row['dry_run'] for row in rows} == {'true'}
    assert {row['status'] for row in rows} == {'ok'}
    assert all('dry-run only' in row['notes'] for row in rows)


def test_rollback_api_scope_reviewed_plan_apply_without_confirm_writes_nothing(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-rollback-user')
    group_name = api_scope_test_namespace.group('api_rollback_readers')
    ticket = api_scope_test_namespace.ticket('RB')
    user = User.objects.create_user(username=username)
    group = Group.objects.create(name=group_name)
    user.groups.add(group)
    plan_csv = tmp_path / 'reviewed-api-scope-rollback-plan.csv'
    _write_rollback_plan(
        plan_csv,
        [
            (
                f'remove_user_from_group,{group_name},{username},,'
                f'apply-row-3,Rollback membership,peter,2026-05-30,{ticket},'
            ),
        ],
    )
    # TODO(P7 Phase 4): replace global audit count with scoped assertions.
    counts_before = (ApiScopeGrantAudit.objects.count(), user.groups.count())

    with pytest.raises(CommandError, match='--apply requires --confirm-rollback'):
        call_command(
            'rollback_api_scope_reviewed_plan',
            '--plan-file',
            str(plan_csv),
            '--apply',
        )

    assert counts_before == (ApiScopeGrantAudit.objects.count(), user.groups.count())
    assert user.groups.filter(name=group.name).exists() is True


def test_rollback_api_scope_reviewed_plan_with_confirm_writes_audit_and_rolls_back(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-rollback-user')
    service_username = api_scope_test_namespace.user('api-rollback-service')
    group_name = api_scope_test_namespace.group('api_rollback_readers')
    ticket = api_scope_test_namespace.ticket('RB')
    user = User.objects.create_user(username=username)
    service_user = User.objects.create_user(username=service_username)
    group = Group.objects.create(name=group_name)
    user.groups.add(group)
    group_grant = GroupApiScopeGrant.objects.create(
        group=group,
        scope=api_scopes['api:humnos:read'],
    )
    user_grant = UserApiScopeGrant.objects.create(
        user=service_user,
        scope=api_scopes['api:humnos:read'],
    )
    plan_csv = tmp_path / 'reviewed-api-scope-rollback-plan.csv'
    _write_rollback_plan(
        plan_csv,
        [
            (
                f'remove_user_from_group,{group_name},{username},,'
                f'apply-row-3,Rollback membership,peter,2026-05-30,{ticket},'
            ),
            (
                f'disable_group_grant,{group_name},,api:humnos:read,'
                f'apply-row-2,Rollback group grant,peter,2026-05-30,{ticket},'
            ),
            (
                f'disable_user_grant,,{service_username},api:humnos:read,'
                f'apply-row-4,Rollback user grant,peter,2026-05-30,{ticket},'
            ),
        ],
    )
    output = io.StringIO()

    call_command(
        'rollback_api_scope_reviewed_plan',
        '--plan-file',
        str(plan_csv),
        '--apply',
        '--confirm-rollback',
        stdout=output,
    )

    group_grant.refresh_from_db()
    user_grant.refresh_from_db()
    assert user.groups.filter(name=group_name).exists() is False
    assert group_grant.enabled is False
    assert user_grant.enabled is False
    assert Group.objects.filter(name=group_name).exists() is True

    rows = list(csv.DictReader(io.StringIO(output.getvalue())))
    assert len(rows) == 3
    assert {row['dry_run'] for row in rows} == {'false'}
    assert {row['status'] for row in rows} == {'rolled_back'}

    audit_rows = ApiScopeGrantAudit.objects.filter(ticket=ticket)
    assert audit_rows.count() == 3
    assert {audit.action for audit in audit_rows} == {
        'remove_user_from_group',
        'disable_group_grant',
        'disable_user_grant',
    }
    assert {audit.dry_run for audit in audit_rows} == {False}
    assert {audit.status for audit in audit_rows} == {'rolled_back'}
    assert {audit.rollback_of for audit in audit_rows} == {
        'apply-row-2',
        'apply-row-3',
        'apply-row-4',
    }
    assert all(audit.previous_state is not None for audit in audit_rows)
    assert all(audit.planned_state is not None for audit in audit_rows)
    assert all(audit.result for audit in audit_rows)


def test_disposable_apply_rollback_drill_verifies_rollback_of_chain(
    api_scopes, tmp_path, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('test_user')
    service_username = api_scope_test_namespace.user('test_staff_nomenu')
    group_name = api_scope_test_namespace.group('test_api_scope_drill_readers')
    apply_ticket = api_scope_test_namespace.ticket('DRILL')
    rollback_ticket = api_scope_test_namespace.ticket('DRILL-RB')
    user = User.objects.create_user(username=username)
    service_user = User.objects.create_user(username=service_username, is_staff=True)
    apply_csv = tmp_path / 'api-scope-disposable-reviewed-apply.csv'
    apply_csv.write_text(
        '\n'.join(
            [
                (
                    'action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,'
                    'ticket,rollback_of,notes'
                ),
                (
                    f'create_group,{group_name},,,1,'
                    f'Disposable drill reader group,peter,2026-05-30,{apply_ticket},,'
                ),
                (
                    f'create_group_grant,{group_name},,api:humnos:read,'
                    '1,Disposable drill group read grant,peter,2026-05-30,'
                    f'{apply_ticket},,'
                ),
                (
                    f'assign_user_to_group,{group_name},{username},,'
                    f'1,Disposable drill membership,peter,2026-05-30,{apply_ticket},,'
                ),
                (
                    f'create_user_grant,,{service_username},api:humnos:read,'
                    '1,Disposable drill direct user exception,peter,2026-05-30,'
                    f'{apply_ticket},,'
                ),
            ]
        ),
        encoding='utf-8',
    )
    apply_output = io.StringIO()

    call_command(
        'apply_api_scope_reviewed_plan',
        '--plan-file',
        str(apply_csv),
        '--apply',
        '--confirm-apply',
        stdout=apply_output,
    )

    apply_rows = {
        row['action']: row['audit_event']
        for row in csv.DictReader(io.StringIO(apply_output.getvalue()))
    }
    rollback_csv = tmp_path / 'api-scope-disposable-reviewed-rollback.csv'
    _write_rollback_plan(
        rollback_csv,
        [
            (
                f'remove_user_from_group,{group_name},{username},,'
                f'{apply_rows["assign_user_to_group"]},'
                'Disposable drill rollback membership,peter,2026-05-30,'
                f'{rollback_ticket},'
            ),
            (
                f'disable_group_grant,{group_name},,api:humnos:read,'
                f'{apply_rows["create_group_grant"]},'
                'Disposable drill rollback group grant,peter,2026-05-30,'
                f'{rollback_ticket},'
            ),
            (
                f'disable_user_grant,,{service_username},api:humnos:read,'
                f'{apply_rows["create_user_grant"]},'
                'Disposable drill rollback user grant,peter,2026-05-30,'
                f'{rollback_ticket},'
            ),
        ],
    )

    call_command(
        'rollback_api_scope_reviewed_plan',
        '--plan-file',
        str(rollback_csv),
        '--apply',
        '--confirm-rollback',
    )

    group = Group.objects.get(name=group_name)
    assert user.groups.filter(name=group.name).exists() is False
    assert not GroupApiScopeGrant.objects.filter(group=group, enabled=True).exists()
    assert not UserApiScopeGrant.objects.filter(user=service_user, enabled=True).exists()
    assert GroupApiScopeGrant.objects.filter(
        group=group,
        scope=api_scopes['api:humnos:read'],
        enabled=False,
    ).exists()
    assert UserApiScopeGrant.objects.filter(
        user=service_user,
        scope=api_scopes['api:humnos:read'],
        enabled=False,
    ).exists()

    apply_event_ids = set(
        ApiScopeGrantAudit.objects.filter(ticket=apply_ticket).values_list(
            'event_id',
            flat=True,
        )
    )
    rollback_events = ApiScopeGrantAudit.objects.filter(
        ticket=rollback_ticket
    )
    assert rollback_events.count() == 3
    assert {event.rollback_of for event in rollback_events} == {
        apply_rows['assign_user_to_group'],
        apply_rows['create_group_grant'],
        apply_rows['create_user_grant'],
    }
    assert {event.rollback_of for event in rollback_events} <= apply_event_ids


def test_rollback_api_scope_reviewed_plan_transaction_failure_rolls_back(
    api_scopes, tmp_path, monkeypatch, api_scope_test_namespace
):
    username = api_scope_test_namespace.user('api-rollback-tx-user')
    group_name = api_scope_test_namespace.group('api_rollback_tx_group')
    ticket = api_scope_test_namespace.ticket('RB-TX')
    user = User.objects.create_user(username=username)
    group = Group.objects.create(name=group_name)
    user.groups.add(group)
    grant = GroupApiScopeGrant.objects.create(
        group=group,
        scope=api_scopes['api:humnos:read'],
    )
    plan_csv = tmp_path / 'reviewed-api-scope-rollback-plan.csv'
    _write_rollback_plan(
        plan_csv,
        [
            (
                f'disable_group_grant,{group_name},,api:humnos:read,'
                f'apply-row-2,Rollback group grant,peter,2026-05-30,{ticket},'
            ),
            (
                f'remove_user_from_group,{group_name},{username},,'
                f'apply-row-3,Rollback membership,peter,2026-05-30,{ticket},'
            ),
        ],
    )
    original_execute = RollbackApiScopeReviewedPlanCommand._execute_rollback_action

    def fail_after_first_write(self, row, options):
        if (row.get('action') or '').strip() == 'remove_user_from_group':
            raise CommandError('injected rollback transaction failure')
        return original_execute(self, row, options)

    monkeypatch.setattr(
        RollbackApiScopeReviewedPlanCommand,
        '_execute_rollback_action',
        fail_after_first_write,
    )

    with pytest.raises(CommandError, match='injected rollback transaction failure'):
        call_command(
            'rollback_api_scope_reviewed_plan',
            '--plan-file',
            str(plan_csv),
            '--apply',
            '--confirm-rollback',
        )

    grant.refresh_from_db()
    assert grant.enabled is True
    assert user.groups.filter(name=group_name).exists() is True
    assert ApiScopeGrantAudit.objects.filter(ticket=ticket).exists() is False
