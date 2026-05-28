param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$ComposeCommand = "docker-compose"
)

$ErrorActionPreference = "Stop"

function Invoke-Compose {
    param([string[]]$Arguments)

    if ($ComposeCommand -eq "docker compose") {
        & docker compose @Arguments
        return
    }

    & $ComposeCommand @Arguments
}

if (-not (Test-Path $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

$envLines = Get-Content ".env" | Where-Object { $_ -match "^[A-Za-z_][A-Za-z0-9_]*=" }
$envMap = @{}
foreach ($line in $envLines) {
    $parts = $line -split "=", 2
    $envMap[$parts[0]] = $parts[1]
}

$dbName = $envMap["DB_NAME"]
$dbUser = $envMap["DB_USER"]

Write-Host "Restoring database: $dbName"
Write-Host "Backup file: $BackupFile"
Write-Host "Confirm that this is the correct environment. Restore will overwrite current data."

if ($ComposeCommand -eq "docker compose") {
    Get-Content -Raw $BackupFile | docker compose exec -T db sh -c "mysql -u`$MYSQL_USER -p`$MYSQL_PASSWORD `$MYSQL_DATABASE"
} else {
    Get-Content -Raw $BackupFile | & $ComposeCommand exec -T db sh -c "mysql -u`$MYSQL_USER -p`$MYSQL_PASSWORD `$MYSQL_DATABASE"
}

Write-Host "Database restore completed."
