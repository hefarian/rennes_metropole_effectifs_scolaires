#!/usr/bin/env powershell
# Script pour exécuter les tests avec couverture et afficher les rapports

param(
    [switch]$OpenReport = $true,
    [switch]$QuickRun = $false
)

Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host "                    TESTS UNITAIRES & COUVERTURE                  " -ForegroundColor Cyan
Write-Host "---" -ForegroundColor Cyan
Write-Host ""

# Déterminer la commande à exécuter
if ($QuickRun) {
    Write-Host "[Quick] Mode rapide (sans couverture)..." -ForegroundColor Yellow
    $test_cmd = "python -m pytest tests/ -q --tb=no"
} else {
    Write-Host "[Full] Exécution complète avec couverture..." -ForegroundColor Green
    $test_cmd = "python run_tests_with_coverage.py"
}

Write-Host ""
Write-Host "[EXECUTION]" -ForegroundColor Yellow
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# Exécuter les tests
Invoke-Expression $test_cmd

Write-Host ""
Write-Host "---" -ForegroundColor Gray
Write-Host ""

# Vérifier si les rapports ont été générés
if (Test-Path "htmlcov/index.html") {
    Write-Host "[OK] Rapport de couverture généré: htmlcov/index.html" -ForegroundColor Green
    Write-Host ""

    if ($OpenReport) {
        Write-Host "[INFO] Ouverture du rapport HTML..." -ForegroundColor Cyan
        Start-Process "htmlcov/index.html"
    } else {
        Write-Host "[TIP] Astuce: Ouvrez htmlcov/index.html dans votre navigateur" -ForegroundColor Gray
    }
} else {
    Write-Host "[WARNING] Aucun rapport de couverture généré (mode rapide?)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host "                           COMMANDES UTILES" -ForegroundColor Cyan
Write-Host "---" -ForegroundColor Cyan
Write-Host ""
Write-Host "[INFO] Lancer les tests:" -ForegroundColor Green
Write-Host "   .\run_tests.ps1              # Avec couverture complète"
Write-Host "   .\run_tests.ps1 -QuickRun    # Rapide, sans couverture"
Write-Host ""
Write-Host "[INFO] Lancer un seul fichier de test:" -ForegroundColor Green
Write-Host "   python run_tests_with_coverage.py --file test_api_schemas.py"
Write-Host ""
Write-Host "---" -ForegroundColor Cyan
Write-Host ""
