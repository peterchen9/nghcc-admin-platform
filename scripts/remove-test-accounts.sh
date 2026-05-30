#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

COMPOSE="${COMPOSE:-docker compose}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.volume.yml}"

echo "Removing local permission test accounts..."

MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES exec -T web python manage.py shell -c "
from django.contrib.auth.models import User

MANAGED_USERNAMES = [
    'test_superuser',
    'test_staff_menu',
    'test_staff_nomenu',
    'test_user',
]

for username in MANAGED_USERNAMES:
    if not username.startswith('test_'):
        raise RuntimeError(f'unsafe managed username: {username}')

deleted, _ = User.objects.filter(username__in=MANAGED_USERNAMES).delete()
print(f'deleted_objects {deleted}')
"

echo "Local permission test accounts removed."
