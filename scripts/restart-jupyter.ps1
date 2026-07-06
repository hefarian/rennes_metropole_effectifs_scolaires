# Redémarre le service jupyter sans reconstruire l'image
Set-Location $PSScriptRoot\..
Write-Host "[P13] Redémarrage de jupyter..." -ForegroundColor Cyan
docker compose restart jupyter
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] jupyter redémarré." -ForegroundColor Green
    docker compose ps jupyter
}
