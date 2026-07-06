# Reconstruit l'image de streamlit sans cache puis redémarre
Set-Location $PSScriptRoot\..
Write-Host "[P13] Arrêt de streamlit..." -ForegroundColor Cyan
docker compose stop streamlit
docker compose rm -f streamlit
Write-Host "[P13] Reconstruction de streamlit (--no-cache)..." -ForegroundColor Cyan
docker compose build --no-cache streamlit
Write-Host "[P13] Démarrage de streamlit..." -ForegroundColor Cyan
docker compose up -d streamlit
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] streamlit reconstruit et démarré." -ForegroundColor Green
    docker compose ps streamlit
} else {
    Write-Host "[P13] ERREUR rebuild streamlit." -ForegroundColor Red; exit 1
}
