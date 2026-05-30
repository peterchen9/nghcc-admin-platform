param(
    [string]$ComposeCommand = "docker compose",
    [string]$Service = "web",
    [string]$LogFile = "",
    [int]$Tail = 1000
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

$parserPath = (Resolve-Path "scripts/api_permission_log_review.py").Path

if ($LogFile) {
    $logFilePath = (Resolve-Path $LogFile).Path
    Invoke-ComposeText (Get-ComposeArgs @(
        "run",
        "--rm",
        "-v",
        "${parserPath}:/app/scripts/api_permission_log_review.py:ro",
        "-v",
        "${logFilePath}:/app/review-api-permission.log:ro",
        "web",
        "python",
        "/app/scripts/api_permission_log_review.py",
        "/app/review-api-permission.log"
    ))
    exit 0
}

$logText = Invoke-ComposeText (Get-ComposeArgs @(
    "logs",
    "--no-color",
    "--timestamps",
    "--tail",
    "$Tail",
    "$Service"
))

$composeArgs = Get-ComposeArgs @(
    "run",
    "--rm",
    "-T",
    "-v",
    "${parserPath}:/app/scripts/api_permission_log_review.py:ro",
    "web",
    "python",
    "/app/scripts/api_permission_log_review.py",
    "-"
)

if ($ComposeCommand -eq "docker compose") {
    $allArgs = @("compose") + $composeArgs
    $logText | docker @allArgs
}
else {
    $logText | & $ComposeCommand @composeArgs
}
