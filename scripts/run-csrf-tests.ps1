param(
    [string]$ComposeCommand = "docker compose"
)

$ErrorActionPreference = "Stop"

function Get-ComposeArgs {
    param([string[]]$ExtraArgs)

    $composeFileArgs = @("-f", "docker-compose.yml", "-f", "docker-compose.volume.yml")
    return $composeFileArgs + $ExtraArgs
}

function Invoke-ComposeText {
    param([string[]]$Arguments)

    if ($ComposeCommand -eq "docker compose") {
        $allArgs = @("compose") + $Arguments
        return (& docker @allArgs 2>$null | Out-String)
    }

    return (& $ComposeCommand @Arguments 2>$null | Out-String)
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

Write-Host "Checking Docker Compose containers..."
Invoke-Compose (Get-ComposeArgs @("ps"))

$dbStatus = Invoke-ComposeText (Get-ComposeArgs @("ps", "db"))
if ($dbStatus -notmatch "healthy") {
    throw "db container is not healthy."
}

$testsPath = (Resolve-Path "tests").Path
$pytestIniPath = (Resolve-Path "pytest.ini").Path
$originalEnableCsrfProtection = $env:ENABLE_CSRF_PROTECTION

Write-Host "Running CSRF-enabled tests..."
try {
    $env:ENABLE_CSRF_PROTECTION = "True"
    Invoke-Compose (Get-ComposeArgs @(
        "run", "--rm",
        "-v", "${testsPath}:/app/tests:ro",
        "-v", "${pytestIniPath}:/app/pytest.ini:ro",
        "-e", "ENABLE_CSRF_PROTECTION=True",
        "-e", "TEST_USERNAME",
        "-e", "TEST_PASSWORD",
        "-e", "TEST_USERNAME_SECONDARY",
        "-e", "TEST_PASSWORD_SECONDARY",
        "-e", "TEST_ADMIN_USERNAME",
        "-e", "TEST_ADMIN_PASSWORD",
        "web", "pytest", "tests/smoke", "tests/integration", "tests/security"
    ))
}
finally {
    if ($null -eq $originalEnableCsrfProtection) {
        Remove-Item Env:ENABLE_CSRF_PROTECTION -ErrorAction SilentlyContinue
    }
    else {
        $env:ENABLE_CSRF_PROTECTION = $originalEnableCsrfProtection
    }
}

Write-Host "CSRF-enabled tests completed successfully."
