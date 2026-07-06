# Démarre le service streamlit
Set-Location $PSScriptRoot\..
Write-Host "[P13] Démarrage de streamlit..." -ForegroundColor Cyan
docker compose up -d streamlit
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] streamlit démarré." -ForegroundColor Green
    docker compose ps streamlit
} else {
    Write-Host "[P13] ERREUR démarrage streamlit." -ForegroundColor Red; exit 1
}
