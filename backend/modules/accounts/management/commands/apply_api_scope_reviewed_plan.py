import csv
import hashlib
import io
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError

from modules.accounts.models import ApiScope, GroupApiScopeGrant, UserApiScopeGrant


REVIEWED_PLAN_ACTIONS = {
    'create_group',
    'create_group_grant',
    'assign_user_to_group',
    'create_user_grant',
    'rollback_group_grant',
    'rollback_user_grant',
    'rollback_user_group_assignment',
}

REQUIRED_COLUMNS = {
    'action',
    'group',
    'username',
    'scope',
    'plan_version',
    'reason',
    'reviewed_by',
    'reviewed_at',
    'ticket',
}


class Command(BaseCommand):
    help = 'Dry-run a manually reviewed API scope grant apply/backfill plan.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-file',
            required=True,
            help='Reviewed CSV plan file. YAML is documented but not executable yet.',
        )
        parser.add_argument(
            '--format',
            choices=['csv'],
            default='csv',
            help='Reviewed plan format supported by this dry-run skeleton.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Validate and report planned actions without writing data. This is always on.',
        )
        parser.add_argument(
            '--expected-checksum',
            help='Optional SHA-256 checksum that the reviewed plan file must match.',
        )
        parser.add_argument(
            '--expected-plan-version',
            type=int,
            help='Optional plan version that every row must declare.',
        )
        parser.add_argument(
            '--reviewed-by',
            help='Optional reviewer identifier that every row must match.',
        )
        parser.add_argument(
            '--ticket',
            help='Optional ticket/reference that every row must match.',
        )
        parser.add_argument(
            '--audit-preview',
            action='store_true',
            default=True,
            help='Emit audit-preview CSV rows. This is the default dry-run output.',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Reserved for a future reviewed implementation. Currently never writes data.',
        )

    def handle(self, *args, **options):
        if options['apply']:
            raise CommandError(
                '--apply is intentionally disabled in this phase; only dry-run is supported.'
            )

        plan_checksum, rows = self._read_csv_plan(options['plan_file'])
        self._validate_plan(rows, plan_checksum, options)
        self._write_csv_row(
            [
                'dry_run',
                'audit_event',
                'plan_version',
                'plan_checksum',
                'row_number',
                'action',
                'status',
                'principal_type',
                'principal',
                'group',
                'username',
                'scope',
                'reason',
                'reviewed_by',
                'reviewed_at',
                'ticket',
                'notes',
            ]
        )
        for index, row in enumerate(rows, start=2):
            status, notes = self._validate_row(row)
            principal_type, principal = self._principal(row)
            self._write_csv_row(
                [
                    'true',
                    self._event_id(plan_checksum, index, row),
                    row.get('plan_version', ''),
                    plan_checksum,
                    str(index),
                    row.get('action', ''),
                    status,
                    principal_type,
                    principal,
                    row.get('group', ''),
                    row.get('username', ''),
                    row.get('scope', ''),
                    row.get('reason', ''),
                    row.get('reviewed_by', ''),
                    row.get('reviewed_at', ''),
                    row.get('ticket', ''),
                    notes,
                ]
            )

    def _read_csv_plan(self, plan_file):
        path = Path(plan_file)
        if not path.exists():
            raise CommandError(f'plan file not found: {plan_file}')
        plan_bytes = path.read_bytes()
        plan_checksum = hashlib.sha256(plan_bytes).hexdigest()
        with path.open(newline='', encoding='utf-8') as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise CommandError('reviewed plan is empty or missing a header row')
            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing_columns:
                raise CommandError(
                    'reviewed plan missing required columns: '
                    + ', '.join(sorted(missing_columns))
                )
            return plan_checksum, list(reader)

    def _validate_plan(self, rows, plan_checksum, options):
        errors = []
        if options.get('expected_checksum') and (
            options['expected_checksum'].lower() != plan_checksum
        ):
            errors.append('plan checksum does not match --expected-checksum')

        if not rows:
            errors.append('reviewed plan has no action rows')

        for index, row in enumerate(rows, start=2):
            row_errors = self._row_errors(row)
            if row_errors:
                errors.append(f'row {index}: ' + '; '.join(row_errors))

            if options.get('expected_plan_version'):
                try:
                    row_version = int((row.get('plan_version') or '').strip())
                except ValueError:
                    row_version = None
                if row_version != options['expected_plan_version']:
                    errors.append(
                        f'row {index}: plan_version does not match '
                        '--expected-plan-version'
                    )
            if options.get('reviewed_by') and (
                (row.get('reviewed_by') or '').strip() != options['reviewed_by']
            ):
                errors.append(f'row {index}: reviewed_by does not match --reviewed-by')
            if options.get('ticket') and (
                (row.get('ticket') or '').strip() != options['ticket']
            ):
                errors.append(f'row {index}: ticket does not match --ticket')

        if errors:
            raise CommandError('reviewed plan validation failed: ' + ' | '.join(errors))

    def _validate_row(self, row):
        errors = self._row_errors(row)
        if errors:
            return 'invalid', '; '.join(errors)

        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()

        notes = [self._object_state_note(action, group_name, username, scope_name)]
        notes.append('dry-run only; no groups, grants, or user assignments were written')
        return 'ok', '; '.join(notes)

    def _row_errors(self, row):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        plan_version = (row.get('plan_version') or '').strip()
        reviewed_by = (row.get('reviewed_by') or '').strip()
        reviewed_at = (row.get('reviewed_at') or '').strip()
        reason = (row.get('reason') or '').strip()
        ticket = (row.get('ticket') or '').strip()
        rollback_of = (row.get('rollback_of') or '').strip()

        errors = []
        if action not in REVIEWED_PLAN_ACTIONS:
            errors.append('unknown action')
        if not plan_version:
            errors.append('plan_version is required')
        else:
            try:
                if int(plan_version) < 1:
                    errors.append('plan_version must be a positive integer')
            except ValueError:
                errors.append('plan_version must be a positive integer')
        if not reviewed_by:
            errors.append('reviewed_by is required')
        if not reviewed_at:
            errors.append('reviewed_at is required')
        if not reason:
            errors.append('reason is required')
        if not ticket:
            errors.append('ticket is required')

        if action in {
            'create_group',
            'create_group_grant',
            'assign_user_to_group',
            'rollback_group_grant',
            'rollback_user_group_assignment',
        } and not group_name:
            errors.append('group is required')
        if action in {
            'assign_user_to_group',
            'create_user_grant',
            'rollback_user_grant',
            'rollback_user_group_assignment',
        } and not username:
            errors.append('username is required')
        if action in {
            'create_group_grant',
            'create_user_grant',
            'rollback_group_grant',
            'rollback_user_grant',
        } and not scope_name:
            errors.append('scope is required')
        if action.startswith('rollback_') and not rollback_of:
            errors.append('rollback_of is required for rollback actions')

        return errors

    def _principal(self, row):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()

        if action in {'create_user_grant', 'rollback_user_grant'}:
            return 'user', username
        if action in {'assign_user_to_group', 'rollback_user_group_assignment'}:
            return 'user_group_assignment', f'{username}->{group_name}'
        if group_name:
            return 'group', group_name
        return '', ''

    def _event_id(self, plan_checksum, row_number, row):
        seed = '|'.join(
            [
                plan_checksum,
                str(row_number),
                row.get('action', ''),
                row.get('group', ''),
                row.get('username', ''),
                row.get('scope', ''),
            ]
        )
        return hashlib.sha256(seed.encode('utf-8')).hexdigest()[:32]

    def _object_state_note(self, action, group_name, username, scope_name):
        group = Group.objects.filter(name=group_name).first() if group_name else None
        user = (
            get_user_model().objects.filter(username=username).first()
            if username
            else None
        )
        scope = ApiScope.objects.filter(scope=scope_name).first() if scope_name else None

        if action == 'create_group':
            return 'group exists' if group else 'group would be created'
        if action == 'assign_user_to_group':
            if not user:
                return 'user missing; assignment would fail in apply mode'
            if not group:
                return 'group missing; assignment would require create_group first'
            return (
                'user already in group'
                if user.groups.filter(name=group_name).exists()
                else 'user would be assigned to group'
            )
        if action in {'create_group_grant', 'rollback_group_grant'}:
            if not group:
                return 'group missing; grant action would require create_group first'
            if not scope:
                return 'scope missing; grant action would fail in apply mode'
            exists = GroupApiScopeGrant.objects.filter(group=group, scope=scope).exists()
            return 'group grant exists' if exists else 'group grant would be created'
        if action in {'create_user_grant', 'rollback_user_grant'}:
            if not user:
                return 'user missing; grant action would fail in apply mode'
            if not scope:
                return 'scope missing; grant action would fail in apply mode'
            exists = UserApiScopeGrant.objects.filter(user=user, scope=scope).exists()
            return 'user grant exists' if exists else 'user grant would be created'
        if action == 'rollback_user_group_assignment':
            if not user or not group:
                return 'user or group missing; rollback would be a no-op'
            return (
                'user would be removed from group'
                if user.groups.filter(name=group_name).exists()
                else 'user is not in group; rollback would be a no-op'
            )
        return 'validated'

    def _write_csv_row(self, row):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(row)
        self.stdout.write(buffer.getvalue().rstrip('\r\n'))
