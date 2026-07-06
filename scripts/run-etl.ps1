# Lance le service ETL (chargement CSV → PostgreSQL)
Set-Location $PSScriptRoot\..
Write-Host "[P13] Lancement de l ETL..." -ForegroundColor Cyan
docker compose --profile etl run --rm etl
if ($LASTEXITCODE -eq 0) {
    Write-Host "[P13] ETL terminé avec succès." -ForegroundColor Green
} else {
    Write-Host "[P13] ERREUR ETL (code $LASTEXITCODE)." -ForegroundColor Red
    exit 1
}
