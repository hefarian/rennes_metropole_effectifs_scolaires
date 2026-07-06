# Démarre le service jupyter
Set-Location $PSScriptRoot\..
Write-Host "[P13] Démarrage de jupyter..." -ForegroundColor Cyan
docker compose up -d jupyter
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] jupyter démarré." -ForegroundColor Green
    docker compose ps jupyter
} else {
    Write-Host "[P13] ERREUR démarrage jupyter." -ForegroundColor Red; exit 1
}
