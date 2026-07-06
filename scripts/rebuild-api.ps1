# Reconstruit l'image de api sans cache puis redémarre
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de api..." -ForegroundColor Cyan
docker compose stop api
docker compose rm -f api
Write-Host "[P13] Reconstruction de api (--no-cache)..." -ForegroundColor Cyan
docker compose build --no-cache api
Write-Host "[P13] Démarrage de api..." -ForegroundColor Cyan
docker compose up -d api
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] api reconstruit et démarré." -ForegroundColor Green
    docker compose ps api
} else {
    Write-Host "[P13] ERREUR rebuild api." -ForegroundColor Red; exit 1
}
