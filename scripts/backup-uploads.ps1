param(
    [string]$OutputDir = "backups",
    [string]$UploadDir = "uploads"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $UploadDir)) {
    throw "Uploads directory not found: $UploadDir"
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outputFile = Join-Path $OutputDir "nghcc-admin-uploads-$timestamp.zip"

Compress-Archive -Path "$UploadDir\*" -DestinationPath $outputFile -Force

Write-Host "Uploads backup completed: $outputFile"
