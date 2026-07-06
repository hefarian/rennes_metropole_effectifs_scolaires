# Arrête le service api
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de api..." -ForegroundColor Cyan
docker compose stop api
if ($LASTEXITCODE -eq 0) { Write-Host "[P13] api arrêté." -ForegroundColor Green }
