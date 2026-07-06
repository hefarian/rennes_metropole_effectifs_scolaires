# Arrête le service postgres
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de postgres..." -ForegroundColor Cyan
docker compose stop postgres
if ($LASTEXITCODE -eq 0) { Write-Host "[P13] postgres arrêté." -ForegroundColor Green }
