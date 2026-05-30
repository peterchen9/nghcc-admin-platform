param(
    [switch]$ExecuteLocal,
    [string]$ComposeCommand = "docker compose"
)

$ErrorActionPreference = "Stop"
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$steps = @(
    @{
        Name = "Local health check"
        Command = ".\scripts\check-local.ps1"
        Args = @(".\scripts\check-local.ps1")
    },
    @{
        Name = "Refresh local test_* account matrix"
        Command = ".\scripts\create-test-accounts.ps1"
        Args = @(".\scripts\create-test-accounts.ps1")
    },
    @{
        Name = "Run report-only request sample"
        Command = ".\scripts\run-api-permission-report-only-check.ps1"
        Args = @(".\scripts\run-api-permission-report-only-check.ps1")
    },
    @{
        Name = "Review CSV decision/reason distribution"
        Command = "Import-Csv reports\api-permission-review.csv | Group-Object decision, reason | Sort-Object Name | Select-Object Name, Count"
        Args = @()
    },
    @{
        Name = "Grant plan dry-run"
        Command = "$ComposeCommand -f docker-compose.yml -f docker-compose.volume.yml run --rm -v <repo>\reports:/app/reports web python manage.py plan_api_scope_grants --report-csv reports/api-permission-review.csv --active-only"
        Args = @("grant-plan")
    },
    @{
        Name = "Disposable apply/rollback drill"
        Command = ".\scripts\run-api-scope-apply-rollback-drill.ps1"
        Args = @(".\scripts\run-api-scope-apply-rollback-drill.ps1")
    },
    @{
        Name = "Smoke, integration, and security tests"
        Command = ".\scripts\run-smoke-tests.ps1"
        Args = @(".\scripts\run-smoke-tests.ps1")
    },
    @{
        Name = "CSRF tests"
        Command = ".\scripts\run-csrf-tests.ps1"
        Args = @(".\scripts\run-csrf-tests.ps1")
    },
    @{
        Name = "Full pytest recheck"
        Command = "$ComposeCommand -f docker-compose.yml -f docker-compose.volume.yml run --rm -v <repo>\tests:/app/tests:ro -v <repo>\pytest.ini:/app/pytest.ini:ro -v <repo>\scripts\api_permission_log_review.py:/app/scripts/api_permission_log_review.py:ro web pytest tests/smoke tests/integration tests/security"
        Args = @("full-pytest")
    }
)

Write-Host "Staging-like API permission report-only recheck"
Write-Host "Boundary: local only; no .240 deploy/connect/modify; no enforce; default API_PERMISSION_MODE remains off."
Write-Host ""

Write-Host "Preconditions:"
Write-Host "- Branch main is up to date with origin/main."
Write-Host "- Docker Compose uses docker-compose.yml plus docker-compose.volume.yml."
Write-Host "- Media is restored in named volume nghcc-admin-media-data."
Write-Host "- Local DB is restored."
Write-Host "- Local test_* accounts are refreshed before request sampling."
Write-Host "- Report-only is applied only as a one-off environment override."
Write-Host ""

Write-Host "Ordered steps:"
for ($index = 0; $index -lt $steps.Count; $index++) {
    $number = $index + 1
    Write-Host "$number. $($steps[$index].Name)"
    Write-Host "   $($steps[$index].Command)"
}

if (-not $ExecuteLocal) {
    Write-Host ""
    Write-Host "Checklist only. Re-run with -ExecuteLocal to execute local steps."
    exit 0
}

Write-Host ""
Write-Host "Executing local-only recheck..."

foreach ($step in $steps) {
    Write-Host ""
    Write-Host "==> $($step.Name)"

    if ($step.Name -eq "Review CSV decision/reason distribution") {
        if (-not (Test-Path "reports\api-permission-review.csv")) {
            throw "reports\api-permission-review.csv does not exist."
        }

        Import-Csv "reports\api-permission-review.csv" |
            Group-Object decision, reason |
            Sort-Object Name |
            Select-Object Name, Count |
            Format-Table -AutoSize
        continue
    }

    if ($step.Command -like "$ComposeCommand*") {
        if ($ComposeCommand -ne "docker compose") {
            throw "ExecuteLocal currently supports the default docker compose command only."
        }

        if ($step.Args[0] -eq "full-pytest") {
            $testsPath = (Resolve-Path "tests").Path
            $pytestIniPath = (Resolve-Path "pytest.ini").Path
            $apiPermissionLogReviewPath = (Resolve-Path "scripts/api_permission_log_review.py").Path
            & docker compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
                -v "${testsPath}:/app/tests:ro" `
                -v "${pytestIniPath}:/app/pytest.ini:ro" `
                -v "${apiPermissionLogReviewPath}:/app/scripts/api_permission_log_review.py:ro" `
                web pytest tests/smoke tests/integration tests/security
            if ($LASTEXITCODE -ne 0) {
                throw "$($step.Name) failed with exit code $LASTEXITCODE."
            }
            continue
        }

        if ($step.Args[0] -eq "grant-plan") {
            $reportPath = (Resolve-Path "reports").Path
            & docker compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
                -v "${reportPath}:/app/reports" `
                web python manage.py plan_api_scope_grants --report-csv reports/api-permission-review.csv --active-only
            if ($LASTEXITCODE -ne 0) {
                throw "$($step.Name) failed with exit code $LASTEXITCODE."
            }
            continue
        }

        & docker @($step.Args)
        if ($LASTEXITCODE -ne 0) {
            throw "$($step.Name) failed with exit code $LASTEXITCODE."
        }
        continue
    }

    & $step.Args[0]
    if ($LASTEXITCODE -ne 0) {
        throw "$($step.Name) failed with exit code $LASTEXITCODE."
    }
}

Write-Host ""
Write-Host "Staging-like API permission report-only recheck completed."
