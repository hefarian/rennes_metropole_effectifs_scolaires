# Arrête le service jupyter
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de jupyter..." -ForegroundColor Cyan
docker compose stop jupyter
if ($LASTEXITCODE -eq 0) { Write-Host "[P13] jupyter arrêté." -ForegroundColor Green }
