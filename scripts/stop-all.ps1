# Arrête tous les services P13 (conserve les volumes)
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de tous les services..." -ForegroundColor Cyan
docker compose down
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] Tous les services sont arrêtés." -ForegroundColor Green
}
