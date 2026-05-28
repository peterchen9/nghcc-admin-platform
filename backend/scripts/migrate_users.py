import os
import sys
import django

# Add the project root to sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nads26.settings')
django.setup()

from django.contrib.auth.models import User

users = [
    {
        'id': 1,
        'username': 'admin',
        'is_superuser': True,
        'is_staff': True,
        'date_joined': '2026-02-12 15:26:41.567609',
    },
    {
        'id': 2,
        'username': 'user',
        'is_superuser': False,
        'is_staff': False,
        'date_joined': '2026-02-15 00:11:41.082049',
    },
    {
        'id': 3,
        'username': 'peter',
        'is_superuser': False,
        'is_staff': False,
        'date_joined': '2026-02-15 00:11:52.401801',
    },
]

for u_data in users:
    user, created = User.objects.get_or_create(username=u_data['username'])
    user.set_unusable_password()
    user.is_superuser = u_data['is_superuser']
    user.is_staff = u_data['is_staff']
    user.save()
    if created:
        print(f"Created user: {u_data['username']}")
    else:
        print(f"Updated user: {u_data['username']}")
