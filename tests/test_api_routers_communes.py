import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)

@patch("api.app.routers.communes.read_sql")
def test_list_communes(mock_read_sql):
    # Mock data return
    mock_df = pd.DataFrame([
        {"code_insee": "35238", "nom_commune": "Rennes", "population": 1000, "densite_hab_km2": 500.0},
        {"code_insee": "35239", "nom_commune": "Cesson", "population": 500, "densite_hab_km2": 300.0}
    ])
    mock_read_sql.return_value = mock_df
    
    response = client.get("/communes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["nom_commune"] == "Rennes"

@patch("api.app.routers.communes.read_sql")
def test_get_commune_success(mock_read_sql):
    mock_df = pd.DataFrame([
        {"code_insee": "35238", "nom_commune": "Rennes", "population": 1000, "densite_hab_km2": 500.0}
    ])
    mock_read_sql.return_value = mock_df
    
    response = client.get("/communes/35238")
    assert response.status_code == 200
    data = response.json()
    assert data["code_insee"] == "35238"
    assert data["nom_commune"] == "Rennes"

@patch("api.app.routers.communes.read_sql")
def test_get_commune_not_found(mock_read_sql):
    mock_read_sql.return_value = pd.DataFrame()
    
    response = client.get("/communes/99999")
    assert response.status_code == 404
    assert "Commune introuvable" in response.json()["detail"]

@patch("api.app.routers.communes.read_sql")
def test_get_commune_stats_success(mock_read_sql):
    mock_df = pd.DataFrame([
        {"code_insee": "35238", "stats": "some_stats"}
    ])
    mock_read_sql.return_value = mock_df
    
    response = client.get("/communes/35238/stats")
    assert response.status_code == 200
    assert "stats" in response.json()

@patch("api.app.routers.communes.read_sql")
def test_get_commune_effectifs_success(mock_read_sql):
    mock_df = pd.DataFrame([
        {"rentree": 2024, "nb_classes": 5, "nb_eleves_total": 100, "nb_eleves_maternelle": 10, "nb_eleves_elementaire": 90}
    ])
    mock_read_sql.return_value = mock_df
    
    response = client.get("/communes/35238/effectifs")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["rentree"] == 2024
