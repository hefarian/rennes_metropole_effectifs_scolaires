# Redémarre tous les services P13 sans reconstruire les images
Set-Location $PSScriptRoot\..
Write-Host "[P13] Redémarrage de tous les services..." -ForegroundColor Cyan
docker compose restart 
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] Tous les services ont redémarré." -ForegroundColor Green
    docker compose ps
}
