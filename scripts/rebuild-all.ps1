# Reconstruit toutes les images sans cache puis relance tous les services
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt des services..." -ForegroundColor Cyan
docker compose down
Write-Host "[P13] Reconstruction des images (--no-cache)..." -ForegroundColor Cyan
docker compose build --no-cache l
Write-Host "[P13] Démarrage des services..." -ForegroundColor Cyan
docker compose up -d 
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] Reconstruction terminée. Services actifs :" -ForegroundColor Green
    docker compose ps
} else {
    Write-Host "[P13] ERREUR lors de la reconstruction." -ForegroundColor Red
    exit 1
}
