param(
    [string]$ComposeCommand = "docker compose",
    [string]$ReportDir = "reports",
    [string]$RawLog = "api-permission-report-only.log",
    [string]$CsvFile = "api-permission-review.csv"
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
            throw "docker compose failed with exit code $LASTEXITCODE."
        }
        return
    }

    & $ComposeCommand @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$ComposeCommand failed with exit code $LASTEXITCODE."
    }
}

function Invoke-ComposeText {
    param([string[]]$Arguments)

    if ($ComposeCommand -eq "docker compose") {
        $allArgs = @("compose") + $Arguments
        $previousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $text = (& docker @allArgs 2>$null | Out-String)
        }
        finally {
            $ErrorActionPreference = $previousErrorActionPreference
        }
        if ($LASTEXITCODE -ne 0) {
            throw "docker compose failed with exit code $LASTEXITCODE."
        }
        return $text
    }

    $previousErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $text = (& $ComposeCommand @Arguments 2>$null | Out-String)
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }
    if ($LASTEXITCODE -ne 0) {
        throw "$ComposeCommand failed with exit code $LASTEXITCODE."
    }
    return $text
}

New-Item -ItemType Directory -Force -Path $ReportDir | Out-Null
$reportPath = (Resolve-Path $ReportDir).Path
$parserPath = (Resolve-Path "scripts/api_permission_log_review.py").Path
$checkerPath = (Resolve-Path "scripts/api_permission_report_only_check.py").Path

Write-Host "Running API permission report-only local endpoint check..."
Invoke-Compose (Get-ComposeArgs @(
    "run", "--rm",
    "-e", "API_PERMISSION_MODE=report-only",
    "-e", "REPORT_RAW_LOG=$RawLog",
    "-v", "${reportPath}:/app/reports",
    "-v", "${checkerPath}:/app/scripts/api_permission_report_only_check.py:ro",
    "web", "python", "/app/scripts/api_permission_report_only_check.py"
))

Write-Host "Exporting safe review CSV..."
$csvText = Invoke-ComposeText (Get-ComposeArgs @(
    "run", "--rm",
    "-v", "${reportPath}:/app/reports",
    "-v", "${parserPath}:/app/scripts/api_permission_log_review.py:ro",
    "web", "python", "/app/scripts/api_permission_log_review.py", "/app/reports/$RawLog"
))
$csvPath = Join-Path $ReportDir $CsvFile
Set-Content -Path $csvPath -Value $csvText -Encoding utf8

Write-Host "Decision/reason distribution:"
$rows = Import-Csv $csvPath
Write-Host "rows=$($rows.Count)"
$rows |
    Group-Object decision, reason |
    Sort-Object Name |
    ForEach-Object {
        $decision = $_.Group[0].decision
        $reason = $_.Group[0].reason
        Write-Host "$decision,$reason,$($_.Count)"
    }

Write-Host "CSV written to $csvPath"
