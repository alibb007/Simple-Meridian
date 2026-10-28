# Start Simple Meridian on Windows 10/11. Needs Docker Desktop with the WSL 2 backend.
# Run from PowerShell:  powershell -ExecutionPolicy Bypass -File .\start.ps1
$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker is not installed. Get Docker Desktop: https://www.docker.com/products/docker-desktop/"
    exit 1
}
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker is installed but not running. Start Docker Desktop, wait for it to finish starting, then run this again."
    exit 1
}

Write-Host "Building and starting Simple Meridian (the first build takes a few minutes)..."
docker compose up --build -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Waiting for the app to be ready..."
for ($i = 0; $i -lt 60; $i++) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8501/_stcore/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) {
            Write-Host "Ready: http://localhost:8501"
            Start-Process "http://localhost:8501"
            Write-Host "Stop it later with:  docker compose down"
            exit 0
        }
    } catch { Start-Sleep -Seconds 2 }
}
Write-Host "The app did not answer yet. Check the logs with:  docker compose logs -f"
