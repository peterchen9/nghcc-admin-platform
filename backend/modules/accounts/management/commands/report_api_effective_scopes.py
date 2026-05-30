import csv
import io

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from nads26.api_permissions import get_effective_api_scopes


class Command(BaseCommand):
    help = 'List stored effective API scopes for users without enforcing them.'
    requires_system_checks = []

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            action='append',
            default=None,
            help='Limit report to one username. Can be provided multiple times.',
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Only include active users.',
        )

    def handle(self, *args, **options):
        User = get_user_model()
        users = User.objects.order_by('username')
        if options['username']:
            users = users.filter(username__in=options['username'])
        if options['active_only']:
            users = users.filter(is_active=True)

        self._write_csv_row(
            [
                'username',
                'user_id',
                'is_active',
                'is_staff',
                'is_superuser',
                'bypass_reason',
                'effective_scopes',
            ]
        )
        for user in users:
            scopes = sorted(get_effective_api_scopes(user))
            self._write_csv_row(
                [
                    user.username,
                    user.id,
                    user.is_active,
                    user.is_staff,
                    user.is_superuser,
                    'superuser' if user.is_superuser else '',
                    '|'.join(scopes),
                ]
            )

    def _write_csv_row(self, row):
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(row)
        self.stdout.write(buffer.getvalue().rstrip('\r\n'))
