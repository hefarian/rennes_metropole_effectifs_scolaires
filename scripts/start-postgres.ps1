# Démarre le service postgres
Set-Location $PSScriptRoot\..
Write-Host "[P13] Démarrage de postgres..." -ForegroundColor Cyan
docker compose up -d postgres
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] postgres démarré." -ForegroundColor Green
    docker compose ps postgres
} else {
    Write-Host "[P13] ERREUR démarrage postgres." -ForegroundColor Red; exit 1
}
