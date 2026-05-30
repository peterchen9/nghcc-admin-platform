param(
    [string]$ComposeCommand = "docker compose",
    [string]$TestAccountPassword = $env:TEST_ACCOUNT_PASSWORD
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($TestAccountPassword)) {
    $TestAccountPassword = "local-test-password-12345"
}

function Get-ComposeArgs {
    param([string[]]$ExtraArgs)

    $composeFileArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.volume.yml")
    return $composeFileArgs + $ExtraArgs
}

function Invoke-Compose {
    param([string[]]$Arguments)

    if ($ComposeCommand -eq "docker compose") {
        $allArgs = @("compose") + $Arguments
        & docker @allArgs
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose failed with exit code $LASTEXITCODE"
        }
        return
    }

    & $ComposeCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$ComposeCommand failed with exit code $LASTEXITCODE"
    }
}

$pythonCode = @'
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
'@

Write-Host "Creating local permission test accounts..."
$originalTestAccountPassword = $env:TEST_ACCOUNT_PASSWORD
$env:TEST_ACCOUNT_PASSWORD = $TestAccountPassword
try {
    Invoke-Compose -Arguments (Get-ComposeArgs @(
        "exec", "-T",
        "-e", "TEST_ACCOUNT_PASSWORD=$TestAccountPassword",
        "web", "python", "manage.py", "shell", "-c", $pythonCode
    ))
}
finally {
    if ($null -eq $originalTestAccountPassword) {
        Remove-Item Env:TEST_ACCOUNT_PASSWORD -ErrorAction SilentlyContinue
    }
    else {
        $env:TEST_ACCOUNT_PASSWORD = $originalTestAccountPassword
    }
}

Write-Host "Local permission test accounts are ready."
