param(
    [string]$OutputDir = "backups",
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

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$envLines = Get-Content ".env" | Where-Object { $_ -match "^[A-Za-z_][A-Za-z0-9_]*=" }
$envMap = @{}
foreach ($line in $envLines) {
    $parts = $line -split "=", 2
    $envMap[$parts[0]] = $parts[1]
}

$dbName = $envMap["DB_NAME"]
$dbUser = $envMap["DB_USER"]
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputFile = Join-Path $OutputDir "nghcc-admin-db-$timestamp.sql"

Write-Host "Exporting MySQL database: $dbName"
Invoke-Compose @("exec", "-T", "db", "sh", "-c", "mysqldump --no-tablespaces -u`$MYSQL_USER -p`$MYSQL_PASSWORD `$MYSQL_DATABASE") | Set-Content -Path $outputFile -Encoding UTF8

Write-Host "Database backup completed: $outputFile"
