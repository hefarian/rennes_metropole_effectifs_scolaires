# Démarre tous les services P13 selon les profils du .env
Set-Location $PSScriptRoot\..

# 1. Lire le fichier .env pour extraire les profils actifs et les ports
$envContent = Get-Content .env -Raw
$profilesMatch = [regex]::Match($envContent, 'COMPOSE_PROFILES=(.+)')
$activeProfiles = if ($profilesMatch.Success) { $profilesMatch.Groups[1].Value.Split(',').Trim() } else { @() }

Write-Host "[P13] Démarrage des services configurés..." -ForegroundColor Cyan

# On lance docker compose sans spécifier de services : il lira automatiquement COMPOSE_PROFILES du .env
docker compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "[P13] Services actifs :" -ForegroundColor Green
    docker compose ps
    Write-Host ""
    
    # Fonction locale rapide pour extraire un port du .env
    function Get-Port($key) {
        if ($envContent -match "$key=(\d+)") { return $Matches[1] }
        return "????"
    }

    # 2. Affichage conditionnel des URLs selon les profils activés
    # La base de données et MLflow n'ont pas forcément de profils bloquants, mais on peut valider le reste
    if ($activeProfiles -contains "streamlit") {
        Write-Host "  Streamlit  : http://localhost:$(Get-Port 'STREAMLIT_HOST_PORT')" -ForegroundColor Yellow
    }
    if ($activeProfiles -contains "api") {
        Write-Host "  API Swagger: http://localhost:$(Get-Port 'API_HOST_PORT')/docs" -ForegroundColor Yellow
    }
    if ($activeProfiles -contains "jupyter") {
        Write-Host "  Jupyter    : http://localhost:$(Get-Port 'JUPYTER_HOST_PORT')" -ForegroundColor Yellow
    }
    if ($activeProfiles -contains "mlflow") {
        Write-Host "  MLflow     : http://localhost:$(Get-Port 'MLFLOW_HOST_PORT')" -ForegroundColor Yellow
    }

} else {
    Write-Host "[P13] ERREUR au démarrage." -ForegroundColor Red
    exit 1
}