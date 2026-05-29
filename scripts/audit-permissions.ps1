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
        return
    }

    & $ComposeCommand @Arguments
}

$reportsPath = Join-Path (Get-Location) "reports"
New-Item -ItemType Directory -Force -Path $reportsPath | Out-Null

$scriptPath = (Resolve-Path "scripts/permission_audit.py").Path

Write-Host "Checking local Docker Compose containers..."
Invoke-Compose (Get-ComposeArgs @("ps"))

Write-Host "Generating read-only permission audit reports..."
Invoke-Compose (Get-ComposeArgs @(
    "run", "--rm",
    "-v", "${reportsPath}:/app/reports",
    "-v", "${scriptPath}:/app/scripts/permission_audit.py:ro",
    "web", "python", "/app/scripts/permission_audit.py"
))

Write-Host "Reports generated:"
Write-Host "- reports/permission-audit.json"
Write-Host "- reports/permission-audit.md"
