# Démarre tous les services P13 (hors ETL)
Set-Location $PSScriptRoot\..
Write-Host "[P13] Démarrage de tous les services..." -ForegroundColor Cyan
docker compose up -d postgres api streamlit mlflow jupyter
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[P13] Services actifs :" -ForegroundColor Green
    docker compose ps
    Write-Host ""
    Write-Host "  Streamlit  : http://localhost:$(Get-Content .env | Select-String 'STREAMLIT_HOST_PORT=(.+)' | ForEach-Object { $_.Matches[0].Groups[1].Value })" -ForegroundColor Yellow
    Write-Host "  API Swagger: http://localhost:$(Get-Content .env | Select-String 'API_HOST_PORT=(.+)' | ForEach-Object { $_.Matches[0].Groups[1].Value })/docs" -ForegroundColor Yellow
    Write-Host "  Jupyter    : http://localhost:$(Get-Content .env | Select-String 'JUPYTER_HOST_PORT=(.+)' | ForEach-Object { $_.Matches[0].Groups[1].Value })" -ForegroundColor Yellow
    Write-Host "  MLflow     : http://localhost:$(Get-Content .env | Select-String 'MLFLOW_HOST_PORT=(.+)' | ForEach-Object { $_.Matches[0].Groups[1].Value })" -ForegroundColor Yellow
} else {
    Write-Host "[P13] ERREUR au démarrage." -ForegroundColor Red
    exit 1
}
