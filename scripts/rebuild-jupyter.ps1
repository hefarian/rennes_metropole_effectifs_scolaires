# Reconstruit l'image de jupyter sans cache puis redémarre
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de jupyter..." -ForegroundColor Cyan
docker compose stop jupyter
docker compose rm -f jupyter
Write-Host "[P13] Reconstruction de jupyter (--no-cache)..." -ForegroundColor Cyan
docker compose build --no-cache jupyter
Write-Host "[P13] Démarrage de jupyter..." -ForegroundColor Cyan
docker compose up -d jupyter
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] jupyter reconstruit et démarré." -ForegroundColor Green
    docker compose ps jupyter
} else {
    Write-Host "[P13] ERREUR rebuild jupyter." -ForegroundColor Red; exit 1
}
