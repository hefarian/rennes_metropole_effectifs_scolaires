# Redémarre le service postgres sans reconstruire l'image
Set-Location $PSScriptRoot\..
Write-Host "[P13] Redémarrage de postgres..." -ForegroundColor Cyan
docker compose restart postgres
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] postgres redémarré." -ForegroundColor Green
    docker compose ps postgres
}
