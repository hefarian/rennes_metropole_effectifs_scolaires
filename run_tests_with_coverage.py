#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script pour exécuter les tests unitaires et générer un rapport de couverture.

Utilise pytest avec coverage pour :
1. Exécuter tous les tests du répertoire tests/
2. Mesurer la couverture du code sur api/ et src/p13/
3. Générer un rapport HTML (htmlcov/), XML (coverage.xml) et terminal

Installation des dépendances :
    pip install pytest pytest-cov coverage

Utilisation :
    python run_tests_with_coverage.py
    python run_tests_with_coverage.py --file test_api_schemas.py
    python run_tests_with_coverage.py --report-only

Le rapport de couverture sera généré en HTML dans htmlcov/index.html
"""

import subprocess
import sys
from pathlib import Path


def run_tests_with_coverage():
    """Exécuter les tests avec coverage et générer des rapports."""

    project_root = Path(__file__).parent

    # Ajout des chemins au PYTHONPATH (insert pour priorité)
    sys.path.insert(0, str(project_root))
    sys.path.insert(0, str(project_root / "src"))

    print("=" * 80)
    print("EXÉCUTION DES TESTS AVEC COUVERTURE DE CODE")
    print("=" * 80)
    print()

    # Commande pytest avec couverture
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",               # Répertoire des tests
        "-v",                   # Verbose
        "--tb=short",           # Traceback court pour les erreurs
        "--cov=api",            # Couverture du package api
        "--cov=src/p13",        # Couverture du package p13
        "--cov-report=term-missing",  # Rapport terminal avec lignes manquantes
        "--cov-report=html",          # Rapport HTML dans htmlcov/
        "--cov-report=xml",           # Rapport XML (coverage.xml) pour CI
        "--cov-fail-under=75",        # Seuil minimum de couverture : 75%
    ]

    print("🏃 Exécution des tests...")
    print(f"   Commande : {' '.join(cmd)}")
    print()

    # Exécuter pytest via le même interpréteur Python
    result = subprocess.run(cmd, cwd=str(project_root))

    print()
    print("=" * 80)
    if result.returncode == 0:
        print("✅ TOUS LES TESTS SONT PASSÉS ET LE SEUIL DE COUVERTURE EST ATTEINT")
    else:
        print("❌ DES TESTS ONT ÉCHOUÉ OU LE SEUIL DE COUVERTURE N'EST PAS ATTEINT")
    print("=" * 80)
    print()

    # Afficher le chemin du rapport HTML
    htmlcov_path = project_root / "htmlcov" / "index.html"
    if htmlcov_path.exists():
        print("📊 RAPPORT DE COUVERTURE HTML")
        print(f"   {htmlcov_path}")
    print()

    return result.returncode


def run_specific_test_file(test_file):
    """
    Exécuter un seul fichier de test avec coverage.

    Args:
        test_file : nom du fichier de test (ex: "test_api_schemas.py")
    """
    cmd = [
        sys.executable, "-m", "pytest",
        f"tests/{test_file}",
        "-v",
        "--tb=short",
        "--cov=api",
        "--cov=src/p13",
        "--cov-report=term-missing",
    ]

    print(f"🏃 Exécution : {' '.join(cmd)}")
    return subprocess.run(cmd).returncode


def generate_coverage_report_only():
    """
    Générer un rapport de couverture à partir des données existantes.

    Utile si vous avez déjà exécuté les tests.
    """
    cmd = [sys.executable, "-m", "coverage", "report", "-m"]
    print("📊 Génération du rapport de couverture...")
    subprocess.run(cmd)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--file" and len(sys.argv) > 2:
            sys.exit(run_specific_test_file(sys.argv[2]))
        elif sys.argv[1] == "--report-only":
            generate_coverage_report_only()
        elif sys.argv[1] in ("-h", "--help"):
            print(__doc__)
        else:
            print(f"Argument inconnu : {sys.argv[1]}")
            print("Utilisation : python run_tests_with_coverage.py [--file <test>] [--report-only] [--help]")
    else:
        sys.exit(run_tests_with_coverage())
