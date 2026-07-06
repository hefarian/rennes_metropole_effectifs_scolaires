# Redémarre le service streamlit sans reconstruire l'image
Set-Location $PSScriptRoot\..
Write-Host "[P13] Redémarrage de streamlit..." -ForegroundColor Cyan
docker compose restart streamlit
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] streamlit redémarré." -ForegroundColor Green
    docker compose ps streamlit
}
