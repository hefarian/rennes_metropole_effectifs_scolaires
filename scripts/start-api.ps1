# Démarre le service api
Set-Location $PSScriptRoot\..
Write-Host "[P13] Démarrage de api..." -ForegroundColor Cyan
docker compose up -d api
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] api démarré." -ForegroundColor Green
    docker compose ps api
} else {
    Write-Host "[P13] ERREUR démarrage api." -ForegroundColor Red; exit 1
}
