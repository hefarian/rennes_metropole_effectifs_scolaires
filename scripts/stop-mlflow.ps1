# Arrête le service mlflow
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de mlflow..." -ForegroundColor Cyan
docker compose stop mlflow
if ($LASTEXITCODE -eq 0) { Write-Host "[P13] mlflow arrêté." -ForegroundColor Green }
