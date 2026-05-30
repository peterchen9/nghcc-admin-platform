param(
    [string]$ComposeCommand = "docker compose"
)

$ErrorActionPreference = "Stop"

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
'@

Write-Host "Removing local permission test accounts..."
Invoke-Compose -Arguments (Get-ComposeArgs @(
    "exec", "-T",
    "web", "python", "manage.py", "shell", "-c", $pythonCode
))

Write-Host "Local permission test accounts removed."
