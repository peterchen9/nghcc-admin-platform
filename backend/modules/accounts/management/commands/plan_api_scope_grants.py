import csv
import io
from collections import defaultdict
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from modules.accounts.models import GroupApiScopeGrant, UserApiScopeGrant
from nads26.api_permissions import (
    API_PERMISSION_SCOPE_MAP,
    CANONICAL_API_SCOPES,
    get_effective_api_scopes,
)


RECOMMENDED_GROUP_SCOPE_PLAN = {
    'api_hymns_readers': ('api:hymns:read',),
    'api_hymns_editors': ('api:hymns:read', 'api:hymns:write'),
    'api_hymns_uploaders': ('api:hymns:read', 'api:hymns:upload'),
    'api_humnos_readers': ('api:humnos:read',),
    'api_humnos_operators': ('api:humnos:read', 'api:humnos:write'),
}


class Command(BaseCommand):
    help = 'Output a read-only API scope grant assignment plan.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--report-csv',
            default=None,
            help='Optional report-only CSV from api_permission_log_review.',
        )
        parser.add_argument(
            '--username',
            action='append',
            default=None,
            help='Limit user review rows to one username. Can be provided multiple times.',
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only include active users in user review rows.',
        )

    def handle(self, *args, **options):
        report_rows = self._read_report_rows(options['report_csv'])
        missing_by_user = self._missing_scopes_by_user_id(report_rows)
        superuser_scope_counts = self._superuser_scope_counts(report_rows)

        self._write_csv_row(
            [
                'plan_type',
                'principal_type',
                'principal',
                'scope',
                'action',
                'source',
                'reason',
                'notes',
            ]
        )
        self._write_endpoint_mapping_rows()
        self._write_group_plan_rows()
        self._write_user_review_rows(options, missing_by_user)
        self._write_superuser_bypass_rows(superuser_scope_counts)

    def _write_endpoint_mapping_rows(self):
        for (method, endpoint), scope in sorted(API_PERMISSION_SCOPE_MAP.items()):
            self._write_csv_row(
                [
                    'endpoint_mapping',
                    'endpoint',
                    f'{method} {endpoint}',
                    scope,
                    'document',
                    'canonical_map',
                    'required_scope',
                    'Mapping only; no grant is created.',
                ]
            )

    def _write_group_plan_rows(self):
        existing_group_grants = set(
            GroupApiScopeGrant.objects.filter(enabled=True, scope__active=True).values_list(
                'group__name',
                'scope__scope',
            )
        )
        for group_name, scopes in sorted(RECOMMENDED_GROUP_SCOPE_PLAN.items()):
            for scope in scopes:
                exists = (group_name, scope) in existing_group_grants
                self._write_csv_row(
                    [
                        'group_grant',
                        'group',
                        group_name,
                        scope,
                        'keep_existing' if exists else 'suggest_grant',
                        'policy',
                        'group_grants_preferred',
                        (
                            'Existing enabled group grant already covers this scope.'
                            if exists
                            else 'Create or review this role group before assigning users.'
                        ),
                    ]
                )

    def _write_user_review_rows(self, options, missing_by_user):
        User = get_user_model()
        users = User.objects.order_by('username')
        if options['username']:
            users = users.filter(username__in=options['username'])
        if options['active_only']:
            users = users.filter(is_active=True)

        existing_user_grants = set(
            UserApiScopeGrant.objects.filter(enabled=True, scope__active=True).values_list(
                'user_id',
                'scope__scope',
            )
        )
        canonical_scope_set = set(CANONICAL_API_SCOPES)
        for user in users:
            if user.is_superuser:
                self._write_csv_row(
                    [
                        'user_review',
                        'user',
                        user.username,
                        '',
                        'no_grant',
                        'effective_scopes',
                        'superuser_bypass',
                        'Superuser remains an audited bypass; do not backfill grants.',
                    ]
                )
                continue

            effective_scopes = get_effective_api_scopes(user)
            report_missing_scopes = missing_by_user.get(str(user.id), set())
            scopes_to_review = sorted(
                canonical_scope_set & (set(effective_scopes) | report_missing_scopes)
            )
            if not scopes_to_review and report_missing_scopes:
                scopes_to_review = sorted(report_missing_scopes)
            if not scopes_to_review and user.is_staff:
                self._write_csv_row(
                    [
                        'user_review',
                        'user',
                        user.username,
                        '',
                        'no_grant',
                        'effective_scopes',
                        'staff_no_default_scope',
                        'Staff status does not grant API scopes by itself.',
                    ]
                )
                continue

            for scope in scopes_to_review:
                has_direct = (user.id, scope) in existing_user_grants
                has_effective = scope in effective_scopes
                self._write_csv_row(
                    [
                        'user_review',
                        'user',
                        user.username,
                        scope,
                        self._user_action(user, has_direct, has_effective),
                        'report_only_logs' if scope in report_missing_scopes else 'effective_scopes',
                        self._user_reason(user, has_direct, has_effective),
                        self._user_notes(user, has_direct, has_effective),
                    ]
                )

    def _write_superuser_bypass_rows(self, superuser_scope_counts):
        for scope, count in sorted(superuser_scope_counts.items()):
            self._write_csv_row(
                [
                    'superuser_bypass',
                    'superuser',
                    '*',
                    scope,
                    'no_grant',
                    'report_only_logs',
                    'superuser_bypass',
                    f'{count} report-only decision(s); keep visible in audit.',
                ]
            )

    def _user_action(self, user, has_direct, has_effective):
        if has_direct:
            return 'keep_existing_exception'
        if has_effective:
            return 'covered_by_group'
        if user.is_staff:
            return 'review_group_assignment'
        return 'review_need'

    def _user_reason(self, user, has_direct, has_effective):
        if has_direct:
            return 'user_grant_exception'
        if has_effective:
            return 'group_grant_preferred'
        if user.is_staff:
            return 'staff_no_default_scope'
        return 'missing_scope'

    def _user_notes(self, user, has_direct, has_effective):
        if has_direct:
            return 'Direct user grant exists; keep only if this is a documented exception.'
        if has_effective:
            return 'User is already covered by enabled group grants.'
        if user.is_staff:
            return 'Staff status does not grant API scopes; assign a role group if needed.'
        return 'Prefer assigning the user to a reviewed role group; use direct grant only for exceptions.'

    def _read_report_rows(self, report_csv):
        if not report_csv:
            return []
        path = Path(report_csv)
        if not path.exists():
            raise CommandError(f'report CSV not found: {report_csv}')
        with path.open(newline='', encoding='utf-8') as handle:
            return list(csv.DictReader(handle))

    def _missing_scopes_by_user_id(self, rows):
        missing = defaultdict(set)
        for row in rows:
            if row.get('decision') == 'deny' and row.get('reason') == 'missing_scope':
                user_id = row.get('user_id') or ''
                scope = row.get('scope') or ''
                if user_id and scope:
                    missing[user_id].add(scope)
        return missing

    def _superuser_scope_counts(self, rows):
        counts = defaultdict(int)
        for row in rows:
            if row.get('decision') == 'allow' and row.get('reason') == 'superuser':
                scope = row.get('scope') or ''
                if scope:
                    counts[scope] += 1
        return counts

    def _write_csv_row(self, row):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(row)
        self.stdout.write(buffer.getvalue().rstrip('\r\n'))
