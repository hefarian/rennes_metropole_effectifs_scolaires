# Redémarre le service mlflow sans reconstruire l'image
Set-Location $PSScriptRoot\..
Write-Host "[P13] Redémarrage de mlflow..." -ForegroundColor Cyan
docker compose restart mlflow
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] mlflow redémarré." -ForegroundColor Green
    docker compose ps mlflow
}
