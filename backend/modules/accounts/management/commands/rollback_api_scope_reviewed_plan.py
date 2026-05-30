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


ROLLBACK_ACTIONS = {
    'remove_user_from_group',
    'disable_user_grant',
    'disable_group_grant',
    'delete_empty_group',
}

REQUIRED_COLUMNS = {
    'action',
    'group',
    'username',
    'scope',
    'rollback_of',
    'reason',
    'reviewed_by',
    'reviewed_at',
    'ticket',
    'notes',
}


class Command(BaseCommand):
    help = 'Dry-run or explicitly apply a reviewed API scope rollback plan.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--plan-file',
            required=True,
            help='Reviewed rollback CSV plan file.',
        )
        parser.add_argument(
            '--format',
            choices=['csv'],
            default='csv',
            help='Reviewed rollback plan format.',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=True,
            help='Validate and report planned rollback actions without writes. Default.',
        )
        parser.add_argument(
            '--expected-checksum',
            help='Optional SHA-256 checksum that the reviewed plan file must match.',
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
            '--plan-version',
            type=int,
            default=1,
            help='Audit plan version stored for rollback events. Default: 1.',
        )
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Write rollback changes only when --confirm-rollback is also present.',
        )
        parser.add_argument(
            '--confirm-rollback',
            action='store_true',
            help='Required second approval flag for --apply.',
        )
        parser.add_argument(
            '--delete-empty-groups',
            action='store_true',
            help='Allow delete_empty_group rows to delete empty Django groups.',
        )

    def handle(self, *args, **options):
        if options['plan_version'] < 1:
            raise CommandError('--plan-version must be a positive integer')

        plan_checksum, rows = self._read_csv_plan(options['plan_file'])
        self._validate_plan(rows, plan_checksum, options)
        if options['apply'] and not options['confirm_rollback']:
            raise CommandError('--apply requires --confirm-rollback')

        result_rows = (
            self._rollback_rows(plan_checksum, rows, options)
            if options['apply']
            else self._dry_run_rows(plan_checksum, rows, options)
        )
        self._write_csv_row(
            [
                'dry_run',
                'audit_event',
                'plan_checksum',
                'row_number',
                'action',
                'status',
                'principal_type',
                'principal',
                'group',
                'username',
                'scope',
                'rollback_of',
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
                    plan_checksum,
                    str(result_row['row_number']),
                    result_row['action'],
                    result_row['status'],
                    result_row['principal_type'],
                    result_row['principal'],
                    result_row['group'],
                    result_row['username'],
                    result_row['scope'],
                    result_row['rollback_of'],
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
                raise CommandError('reviewed rollback plan is empty or missing a header row')
            missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames)
            if missing_columns:
                raise CommandError(
                    'reviewed rollback plan missing required columns: '
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
            errors.append('reviewed rollback plan has no action rows')

        for index, row in enumerate(rows, start=2):
            row_errors = self._row_errors(row)
            if row_errors:
                errors.append(f'row {index}: ' + '; '.join(row_errors))
            if options.get('apply'):
                errors.extend(
                    f'row {index}: {error}'
                    for error in self._apply_row_errors(plan_checksum, index, row)
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
            raise CommandError(
                'reviewed rollback plan validation failed: ' + ' | '.join(errors)
            )

    def _row_errors(self, row):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        rollback_of = (row.get('rollback_of') or '').strip()
        reviewed_by = (row.get('reviewed_by') or '').strip()
        reviewed_at = (row.get('reviewed_at') or '').strip()
        reason = (row.get('reason') or '').strip()
        ticket = (row.get('ticket') or '').strip()

        errors = []
        if action not in ROLLBACK_ACTIONS:
            errors.append('unknown rollback action')
        if action in {'remove_user_from_group', 'disable_group_grant', 'delete_empty_group'}:
            if not group_name:
                errors.append('group is required')
        if action in {'remove_user_from_group', 'disable_user_grant'}:
            if not username:
                errors.append('username is required')
        if action in {'disable_user_grant', 'disable_group_grant'}:
            if not scope_name:
                errors.append('scope is required')
        if not rollback_of:
            errors.append('rollback_of is required')
        if not reviewed_by:
            errors.append('reviewed_by is required')
        if not reviewed_at:
            errors.append('reviewed_at is required')
        if not reason:
            errors.append('reason is required')
        if not ticket:
            errors.append('ticket is required')
        return errors

    def _apply_row_errors(self, plan_checksum, row_number, row):
        errors = []
        if ApiScopeGrantAudit.objects.filter(
            event_id=self._event_id(plan_checksum, row_number, row)
        ).exists():
            errors.append('audit event already exists for this rollback plan row')
        return errors

    def _dry_run_rows(self, plan_checksum, rows, options):
        result_rows = []
        for index, row in enumerate(rows, start=2):
            principal_type, principal = self._principal(row)
            status, notes = self._validate_row(row, options)
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

    def _rollback_rows(self, plan_checksum, rows, options):
        result_rows = []
        with transaction.atomic():
            for index, row in enumerate(rows, start=2):
                principal_type, principal = self._principal(row)
                event_id = self._event_id(plan_checksum, index, row)
                audit = ApiScopeGrantAudit.objects.create(
                    event_id=event_id,
                    plan_version=options['plan_version'],
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
                    planned_state=self._planned_state(row, options),
                    result={},
                )
                result = self._execute_rollback_action(row, options)
                audit.group = self._group(row)
                audit.user = self._user(row)
                audit.scope = self._scope(row)
                audit.status = result['status']
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
                        result['status'],
                        principal_type,
                        principal,
                        result['note'],
                    )
                )
        return result_rows

    def _validate_row(self, row, options):
        errors = self._row_errors(row)
        if errors:
            return 'invalid', '; '.join(errors)
        notes = [self._object_state_note(row, options)]
        notes.append('dry-run only; no groups, grants, or memberships were changed')
        return 'ok', '; '.join(notes)

    def _execute_rollback_action(self, row, options):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        reason = (row.get('reason') or '').strip()

        if action == 'remove_user_from_group':
            user = self._required_user(username)
            group = self._required_group(group_name)
            existed = user.groups.filter(id=group.id).exists()
            if existed:
                user.groups.remove(group)
            return {
                'status': 'rolled_back',
                'changed': existed,
                'note': (
                    'user removed from group'
                    if existed
                    else 'user was not a member of group'
                ),
            }

        if action == 'disable_user_grant':
            user = self._required_user(username)
            scope = self._required_scope(scope_name)
            grant = UserApiScopeGrant.objects.filter(user=user, scope=scope).first()
            changed = self._disable_grant(grant, reason) if grant else False
            return {
                'status': 'rolled_back',
                'changed': changed,
                'grant_id': grant.id if grant else None,
                'note': (
                    'user grant disabled'
                    if changed
                    else 'user grant missing or already disabled'
                ),
            }

        if action == 'disable_group_grant':
            group = self._required_group(group_name)
            scope = self._required_scope(scope_name)
            grant = GroupApiScopeGrant.objects.filter(group=group, scope=scope).first()
            changed = self._disable_grant(grant, reason) if grant else False
            return {
                'status': 'rolled_back',
                'changed': changed,
                'grant_id': grant.id if grant else None,
                'note': (
                    'group grant disabled'
                    if changed
                    else 'group grant missing or already disabled'
                ),
            }

        if action == 'delete_empty_group':
            group = self._required_group(group_name)
            empty = (
                group.user_set.count() == 0
                and not GroupApiScopeGrant.objects.filter(group=group, enabled=True).exists()
            )
            if options['delete_empty_groups'] and empty:
                group.delete()
                return {
                    'status': 'rolled_back',
                    'changed': True,
                    'note': 'empty group deleted',
                }
            return {
                'status': 'skipped',
                'changed': False,
                'note': (
                    'empty group deletion not enabled'
                    if empty
                    else 'group is not empty or has enabled grants'
                ),
            }

        raise CommandError(f'{action} is not supported for reviewed rollback')

    def _disable_grant(self, grant, reason):
        if not grant or not grant.enabled:
            return False
        grant.enabled = False
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

        if action == 'remove_user_from_group':
            return {
                'user_exists': bool(user),
                'group_exists': bool(group),
                'membership_exists': bool(
                    user and group and user.groups.filter(id=group.id).exists()
                ),
            }
        if action == 'disable_user_grant':
            grant = (
                UserApiScopeGrant.objects.filter(user=user, scope=scope).first()
                if user and scope
                else None
            )
            return self._grant_state(grant, '', username, scope_name)
        if action == 'disable_group_grant':
            grant = (
                GroupApiScopeGrant.objects.filter(group=group, scope=scope).first()
                if group and scope
                else None
            )
            return self._grant_state(grant, group_name, '', scope_name)
        if action == 'delete_empty_group':
            return {
                'group_exists': bool(group),
                'group': group_name,
                'member_count': group.user_set.count() if group else 0,
                'enabled_group_grant_count': (
                    GroupApiScopeGrant.objects.filter(group=group, enabled=True).count()
                    if group
                    else 0
                ),
            }
        return {}

    def _planned_state(self, row, options):
        action = (row.get('action') or '').strip()
        return {
            'action': action,
            'group': (row.get('group') or '').strip(),
            'username': (row.get('username') or '').strip(),
            'scope': (row.get('scope') or '').strip(),
            'enabled': False if action in {'disable_user_grant', 'disable_group_grant'} else None,
            'member': False if action == 'remove_user_from_group' else None,
            'delete_empty_groups': bool(options['delete_empty_groups']),
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

    def _object_state_note(self, row, options):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()
        scope_name = (row.get('scope') or '').strip()
        group = self._group(row)
        user = self._user(row)
        scope = self._scope(row)

        if action == 'remove_user_from_group':
            if not user or not group:
                return 'user or group missing; rollback would be a no-op'
            return (
                'user would be removed from group'
                if user.groups.filter(id=group.id).exists()
                else 'user is not in group; rollback would be a no-op'
            )
        if action == 'disable_user_grant':
            if not user or not scope:
                return 'user or scope missing; rollback would be a no-op'
            grant = UserApiScopeGrant.objects.filter(user=user, scope=scope).first()
            if not grant:
                return 'user grant missing; rollback would be a no-op'
            return 'user grant would be disabled' if grant.enabled else 'user grant already disabled'
        if action == 'disable_group_grant':
            if not group or not scope:
                return 'group or scope missing; rollback would be a no-op'
            grant = GroupApiScopeGrant.objects.filter(group=group, scope=scope).first()
            if not grant:
                return 'group grant missing; rollback would be a no-op'
            return 'group grant would be disabled' if grant.enabled else 'group grant already disabled'
        if action == 'delete_empty_group':
            if not group:
                return 'group missing; rollback would be a no-op'
            if not options['delete_empty_groups']:
                return 'group deletion disabled by default'
            return 'empty group would be deleted'
        return 'validated'

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
            'row_number': row_number,
            'action': row.get('action', ''),
            'status': status,
            'principal_type': principal_type,
            'principal': principal,
            'group': row.get('group', ''),
            'username': row.get('username', ''),
            'scope': row.get('scope', ''),
            'rollback_of': row.get('rollback_of', ''),
            'reason': row.get('reason', ''),
            'reviewed_by': row.get('reviewed_by', ''),
            'reviewed_at': row.get('reviewed_at', ''),
            'ticket': row.get('ticket', ''),
            'notes': notes,
        }

    def _principal(self, row):
        action = (row.get('action') or '').strip()
        group_name = (row.get('group') or '').strip()
        username = (row.get('username') or '').strip()

        if action == 'disable_user_grant':
            return 'user', username
        if action == 'remove_user_from_group':
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
                row.get('rollback_of', ''),
            ]
        )
        return hashlib.sha256(seed.encode('utf-8')).hexdigest()[:32]

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
            raise CommandError(f'group not found for rollback: {group_name}')
        return group

    def _required_user(self, username):
        user = get_user_model().objects.filter(username=username).first()
        if not user:
            raise CommandError(f'user not found for rollback: {username}')
        return user

    def _required_scope(self, scope_name):
        scope = ApiScope.objects.filter(scope=scope_name, active=True).first()
        if not scope:
            raise CommandError(f'active API scope not found for rollback: {scope_name}')
        return scope

    def _write_csv_row(self, row):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(row)
        self.stdout.write(buffer.getvalue().rstrip('\r\n'))
