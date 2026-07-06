# ATTENTION : supprime les volumes (PostgreSQL inclus) puis reconstruit tout
Set-Location $PSScriptRoot\..
Write-Host "[P13] ATTENTION : ce script supprime les données PostgreSQL et MLflow." -ForegroundColor Red
$confirm = Read-Host "Confirmer la suppression des volumes ? (oui/non)"
if ($confirm -ne "oui") {
    Write-Host "Annulé." -ForegroundColor Yellow
    exit 0
}
Write-Host "[P13] Arrêt et suppression des volumes..." -ForegroundColor Cyan
docker compose down -v
Write-Host "[P13] Reconstruction des images (--no-cache)..." -ForegroundColor Cyan
docker compose build --no-cache api streamlit jupyter etl
Write-Host "[P13] Démarrage des services..." -ForegroundColor Cyan
docker compose up -d postgres api streamlit mlflow jupyter
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] Reset complet terminé." -ForegroundColor Green
    docker compose ps
} else {
    Write-Host "[P13] ERREUR." -ForegroundColor Red
    exit 1
}
