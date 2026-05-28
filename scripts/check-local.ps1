param(
    [string]$FrontendUrl = "http://localhost:26001/",
    [string]$BackendUrl = "http://localhost:26002/api/health/",
    [string]$ModulesUrl = "http://localhost:26001/api/modules/",
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

function Assert-HttpOk {
    param(
        [string]$Name,
        [string]$Url
    )

    $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 15
    if ($response.StatusCode -lt 200 -or $response.StatusCode -ge 300) {
        throw "$Name failed: HTTP $($response.StatusCode)"
    }

    Write-Host "$Name OK: HTTP $($response.StatusCode)"
    return $response
}

Write-Host "Checking Docker Compose containers..."
Invoke-Compose @("ps")

$frontend = Assert-HttpOk -Name "Frontend" -Url $FrontendUrl
$backend = Assert-HttpOk -Name "Backend health" -Url $BackendUrl
$modules = Assert-HttpOk -Name "Frontend API proxy" -Url $ModulesUrl

$health = $backend.Content | ConvertFrom-Json
if ($health.database -ne "ok") {
    throw "Database check failed: $($health.database)"
}

Write-Host "Database OK: $($health.database)"
Write-Host "Modules API response length: $($modules.Content.Length)"
Write-Host "Local health check completed."
