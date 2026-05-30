#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

COMPOSE="${COMPOSE:-docker compose}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.volume.yml}"
TEST_ACCOUNT_PASSWORD="${TEST_ACCOUNT_PASSWORD:-local-test-password-12345}"

echo "Creating local permission test accounts..."

MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES exec -T \
  -e TEST_ACCOUNT_PASSWORD="$TEST_ACCOUNT_PASSWORD" \
  web python manage.py shell -c "
import os

from django.contrib.auth.models import User
from modules.menu.models import MenuItem

PASSWORD = os.environ['TEST_ACCOUNT_PASSWORD']
MANAGED_USERS = {
    'test_superuser': {
        'email': 'test_superuser@example.local',
        'display_name': 'Permission Test Superuser',
        'role': 'superuser',
        'is_staff': True,
        'is_superuser': True,
        'menu_routes': ['*'],
    },
    'test_staff_menu': {
        'email': 'test_staff_menu@example.local',
        'display_name': 'Permission Test Staff With Menu',
        'role': 'staff_with_menu',
        'is_staff': True,
        'is_superuser': False,
        'menu_routes': ['*'],
    },
    'test_staff_nomenu': {
        'email': 'test_staff_nomenu@example.local',
        'display_name': 'Permission Test Staff Without Menu',
        'role': 'staff_without_menu',
        'is_staff': True,
        'is_superuser': False,
        'menu_routes': [],
    },
    'test_user': {
        'email': 'test_user@example.local',
        'display_name': 'Permission Test Normal User',
        'role': 'normal_user',
        'is_staff': False,
        'is_superuser': False,
        'menu_routes': [],
    },
}

active_menu = MenuItem.objects.filter(is_active=True)
webav_menu = MenuItem.objects.filter(route='/webav/', is_active=True)

for username, spec in MANAGED_USERS.items():
    user, _ = User.objects.get_or_create(username=username)
    user.email = spec['email']
    user.is_active = True
    user.is_staff = spec['is_staff']
    user.is_superuser = spec['is_superuser']
    user.set_password(PASSWORD)
    user.save()

    profile = user.profile
    profile.worker_ename = username
    profile.display_name = spec['display_name']
    profile.department = 'Local Permission Test'
    profile.worker_id = username
    profile.role = spec['role']
    profile.save()

    if spec['menu_routes'] == ['*']:
        profile.allowed_menu_items.set(active_menu)
    elif '/webav/' in spec['menu_routes']:
        profile.allowed_menu_items.set(webav_menu)
    else:
        profile.allowed_menu_items.clear()

    print(f'created_or_updated {username}')
"

echo "Local permission test accounts are ready."
