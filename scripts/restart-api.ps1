# Redémarre le service api sans reconstruire l'image
Set-Location $PSScriptRoot\..
Write-Host "[P13] Redémarrage de api..." -ForegroundColor Cyan
docker compose restart api
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] api redémarré." -ForegroundColor Green
    docker compose ps api
}
