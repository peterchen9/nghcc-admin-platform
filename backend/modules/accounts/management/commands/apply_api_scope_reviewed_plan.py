import csv
import hashlib
import io
from pathlib import Path

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from modules.accounts.models import (
    ApiScope,
    ApiScopeGrantAudit,
    GroupApiScopeGrant,
    UserApiScopeGrant,
)


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
    help = 'Dry-run or explicitly apply a reviewed API scope grant plan.'
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
            help='Validate and report planned actions without writing data. Default.',
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
            help='Write reviewed changes only when --confirm-apply is also present.',
        )
        parser.add_argument(
            '--confirm-apply',
            action='store_true',
            help='Required second approval flag for --apply.',
        )

    def handle(self, *args, **options):
        plan_checksum, rows = self._read_csv_plan(options['plan_file'])
        self._validate_plan(rows, plan_checksum, options)
        if options['apply'] and not options['confirm_apply']:
            raise CommandError('--apply requires --confirm-apply')

        result_rows = (
            self._apply_rows(plan_checksum, rows)
            if options['apply']
            else self._dry_run_rows(plan_checksum, rows)
        )
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
        for result_row in result_rows:
            self._write_csv_row(
                [
                    'true' if result_row['dry_run'] else 'false',
                    result_row['audit_event'],
                    result_row['plan_version'],
                    plan_checksum,
                    str(result_row['row_number']),
                    result_row['action'],
                    result_row['status'],
                    result_row['principal_type'],
                    result_row['principal'],
                    result_row['group'],
                    result_row['username'],
                    result_row['scope'],
                    result_row['reason'],
                    result_row['reviewed_by'],
                    result_row['reviewed_at'],
                    result_row['ticket'],
                    result_row['notes'],
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

        planned_groups = set(Group.objects.values_list('name', flat=True))
        for index, row in enumerate(rows, start=2):
            row_errors = self._row_errors(row)
            if row_errors:
                errors.append(f'row {index}: ' + '; '.join(row_errors))
            if options.get('apply'):
                errors.extend(
                    f'row {index}: {error}'
                    for error in self._apply_row_errors(
                        row,
                        plan_checksum,
                        index,
                        planned_groups,
                    )
                )

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

    def _apply_row_errors(self, row, plan_checksum, row_number, planned_groups):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        errors = []

        if action.startswith('rollback_'):
            errors.append('rollback actions are dry-run only in this phase')
        if ApiScopeGrantAudit.objects.filter(
            event_id=self._event_id(plan_checksum, row_number, row)
        ).exists():
            errors.append('audit event already exists for this plan row')
        if action == 'create_group':
            planned_groups.add(group_name)
            return errors
        if action in {'create_group_grant', 'assign_user_to_group'}:
            if group_name not in planned_groups:
                errors.append('group must already exist or be created by an earlier row')
        if action in {'assign_user_to_group', 'create_user_grant'} and not (
            get_user_model().objects.filter(username=username).exists()
        ):
            errors.append('user does not exist')
        if action in {'create_group_grant', 'create_user_grant'} and not (
            ApiScope.objects.filter(scope=scope_name, active=True).exists()
        ):
            errors.append('active API scope does not exist')
        return errors

    def _dry_run_rows(self, plan_checksum, rows):
        result_rows = []
        for index, row in enumerate(rows, start=2):
            status, notes = self._validate_row(row)
            principal_type, principal = self._principal(row)
            result_rows.append(
                self._result_row(
                    row,
                    plan_checksum,
                    index,
                    True,
                    status,
                    principal_type,
                    principal,
                    notes,
                )
            )
        return result_rows

    def _apply_rows(self, plan_checksum, rows):
        result_rows = []
        with transaction.atomic():
            for index, row in enumerate(rows, start=2):
                principal_type, principal = self._principal(row)
                event_id = self._event_id(plan_checksum, index, row)
                audit = ApiScopeGrantAudit.objects.create(
                    event_id=event_id,
                    plan_version=int((row.get('plan_version') or '').strip()),
                    plan_checksum=plan_checksum,
                    row_number=index,
                    action=(row.get('action') or '').strip(),
                    dry_run=False,
                    status='pending',
                    principal_type=principal_type,
                    principal_name=principal,
                    group=self._group(row),
                    user=self._user(row),
                    scope=self._scope(row),
                    reviewed_by=(row.get('reviewed_by') or '').strip(),
                    reviewed_at=(row.get('reviewed_at') or '').strip(),
                    ticket=(row.get('ticket') or '').strip(),
                    reason=(row.get('reason') or '').strip(),
                    rollback_of=(row.get('rollback_of') or '').strip(),
                    previous_state=self._previous_state(row),
                    planned_state=self._planned_state(row),
                    result={},
                )
                result = self._execute_apply_action(row)
                audit.group = self._group(row)
                audit.user = self._user(row)
                audit.scope = self._scope(row)
                audit.status = 'applied'
                audit.result = result
                audit.save(
                    update_fields=[
                        'group',
                        'user',
                        'scope',
                        'status',
                        'result',
                    ]
                )
                result_rows.append(
                    self._result_row(
                        row,
                        plan_checksum,
                        index,
                        False,
                        'applied',
                        principal_type,
                        principal,
                        result.get('note', 'applied'),
                    )
                )
        return result_rows

    def _result_row(
        self,
        row,
        plan_checksum,
        row_number,
        dry_run,
        status,
        principal_type,
        principal,
        notes,
    ):
        return {
            'dry_run': dry_run,
            'audit_event': self._event_id(plan_checksum, row_number, row),
            'plan_version': row.get('plan_version', ''),
            'row_number': row_number,
            'action': row.get('action', ''),
            'status': status,
            'principal_type': principal_type,
            'principal': principal,
            'group': row.get('group', ''),
            'username': row.get('username', ''),
            'scope': row.get('scope', ''),
            'reason': row.get('reason', ''),
            'reviewed_by': row.get('reviewed_by', ''),
            'reviewed_at': row.get('reviewed_at', ''),
            'ticket': row.get('ticket', ''),
            'notes': notes,
        }

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

    def _execute_apply_action(self, row):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        reason = (row.get('reason') or '').strip()

        if action == 'create_group':
            group, created = Group.objects.get_or_create(name=group_name)
            return {
                'group_id': group.id,
                'created': created,
                'note': 'group created' if created else 'group already existed',
            }

        if action == 'create_group_grant':
            group = self._required_group(group_name)
            scope = self._required_scope(scope_name)
            grant, created = GroupApiScopeGrant.objects.get_or_create(
                group=group,
                scope=scope,
                defaults={'enabled': True, 'reason': reason},
            )
            changed = self._enable_grant(grant, reason) if not created else False
            return {
                'grant_id': grant.id,
                'created': created,
                'updated': changed,
                'note': 'group grant created' if created else 'group grant reused',
            }

        if action == 'create_user_grant':
            user = self._required_user(username)
            scope = self._required_scope(scope_name)
            grant, created = UserApiScopeGrant.objects.get_or_create(
                user=user,
                scope=scope,
                defaults={'enabled': True, 'reason': reason},
            )
            changed = self._enable_grant(grant, reason) if not created else False
            return {
                'grant_id': grant.id,
                'created': created,
                'updated': changed,
                'note': 'user grant created' if created else 'user grant reused',
            }

        if action == 'assign_user_to_group':
            user = self._required_user(username)
            group = self._required_group(group_name)
            already_member = user.groups.filter(id=group.id).exists()
            if not already_member:
                user.groups.add(group)
            return {
                'user_id': user.id,
                'group_id': group.id,
                'created': not already_member,
                'note': (
                    'user assigned to group'
                    if not already_member
                    else 'user was already in group'
                ),
            }

        raise CommandError(f'{action} is not supported for mutating apply')

    def _enable_grant(self, grant, reason):
        if grant.enabled and grant.reason == reason:
            return False
        grant.enabled = True
        grant.reason = reason
        grant.save(update_fields=['enabled', 'reason'])
        return True

    def _previous_state(self, row):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        group = self._group(row)
        user = self._user(row)
        scope = self._scope(row)

        if action == 'create_group':
            return {'group_exists': bool(group), 'group': group_name}
        if action == 'assign_user_to_group':
            return {
                'user_exists': bool(user),
                'group_exists': bool(group),
                'membership_exists': bool(
                    user and group and user.groups.filter(id=group.id).exists()
                ),
            }
        if action == 'create_group_grant':
            grant = (
                GroupApiScopeGrant.objects.filter(group=group, scope=scope).first()
                if group and scope
                else None
            )
            return self._grant_state(grant, group_name, '', scope_name)
        if action == 'create_user_grant':
            grant = (
                UserApiScopeGrant.objects.filter(user=user, scope=scope).first()
                if user and scope
                else None
            )
            return self._grant_state(grant, '', username, scope_name)
        return {}

    def _planned_state(self, row):
        action = (row.get('action') or '').strip()
        return {
            'action': action,
            'group': (row.get('group') or '').strip(),
            'username': (row.get('username') or '').strip(),
            'scope': (row.get('scope') or '').strip(),
            'enabled': action in {'create_group_grant', 'create_user_grant'},
            'member': action == 'assign_user_to_group',
        }

    def _grant_state(self, grant, group_name, username, scope_name):
        if not grant:
            return {
                'exists': False,
                'group': group_name,
                'username': username,
                'scope': scope_name,
            }
        return {
            'exists': True,
            'id': grant.id,
            'enabled': grant.enabled,
            'reason': grant.reason,
            'group': group_name,
            'username': username,
            'scope': scope_name,
        }

    def _group(self, row):
        group_name = (row.get('group') or '').strip()
        return Group.objects.filter(name=group_name).first() if group_name else None

    def _user(self, row):
        username = (row.get('username') or '').strip()
        return (
            get_user_model().objects.filter(username=username).first()
            if username
            else None
        )

    def _scope(self, row):
        scope_name = (row.get('scope') or '').strip()
        return ApiScope.objects.filter(scope=scope_name).first() if scope_name else None

    def _required_group(self, group_name):
        group = Group.objects.filter(name=group_name).first()
        if not group:
            raise CommandError(f'group not found for apply: {group_name}')
        return group

    def _required_user(self, username):
        user = get_user_model().objects.filter(username=username).first()
        if not user:
            raise CommandError(f'user not found for apply: {username}')
        return user

    def _required_scope(self, scope_name):
        scope = ApiScope.objects.filter(scope=scope_name, active=True).first()
        if not scope:
            raise CommandError(f'active API scope not found for apply: {scope_name}')
        return scope

    def _write_csv_row(self, row):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(row)
        self.stdout.write(buffer.getvalue().rstrip('\r\n'))
