param(
    [string]$WebUrl = "http://localhost:26001/",
    [string]$HealthUrl = "http://localhost:26001/api/health/",
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

$web = Assert-HttpOk -Name "Web" -Url $WebUrl
$healthResponse = Assert-HttpOk -Name "Health" -Url $HealthUrl

$health = $healthResponse.Content | ConvertFrom-Json
if ($health.database -ne "ok") {
    throw "Database check failed: $($health.database)"
}

Write-Host "Database OK: $($health.database)"
if ($web.Content -notmatch "sidebar") {
    throw "Web content check failed: sidebar marker was not found."
}

Write-Host "Web content OK: sidebar marker found"
Write-Host "Local health check completed."
