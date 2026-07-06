# Démarre le service mlflow
Set-Location $PSScriptRoot\..
Write-Host "[P13] Démarrage de mlflow..." -ForegroundColor Cyan
docker compose up -d mlflow
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] mlflow démarré." -ForegroundColor Green
    docker compose ps mlflow
} else {
    Write-Host "[P13] ERREUR démarrage mlflow." -ForegroundColor Red; exit 1
}
