import pytest
import io
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)

@patch("p13.ml.predict.predict_commune")
def test_predict_by_commune_success(mock_predict_commune):
    mock_predict_commune.return_value = {
        "code_insee": "35238",
        "nom_commune": "Rennes",
        "predictions": {
            "nb_eleves_maternelle": 10.0,
            "nb_eleves_elementaire": 50.0,
            "nb_classes_estimees": 2.0,
            "nb_eleves_total": 60.0
        },
        "features_utilisees": {"f1": 1.0}
    }
    response = client.get("/commune/35238")
    assert response.status_code == 200
    assert response.json()["nom_commune"] == "Rennes"

@patch("p13.ml.predict.predict_commune")
def test_predict_by_commune_not_found(mock_predict_commune):
    mock_predict_commune.side_effect = ValueError("Not found")
    response = client.get("/commune/99999")
    assert response.status_code == 404

@patch("p13.ml.predict.predict_logement")
def test_predict_by_logement_success(mock_predict_logement):
    mock_predict_logement.return_value = {
        "code_insee": "35238",
        "nom_commune": "Rennes",
        "predictions": {
            "nb_eleves_maternelle": 10.0,
            "nb_eleves_elementaire": 50.0,
            "nb_classes_estimees": 2.0,
            "nb_eleves_total": 60.0
        },
        "features_utilisees": {"f1": 1.0},
        "logement": {"surface": 75.0},
        "impact_logement": {
            "enfants_estimes": 5.0,
            "maternelle_estimee": 1.0,
            "elementaire_estimee": 4.0,
            "classes_supplementaires": 1.0
        }
    }
    response = client.post("/logement", json={
        "code_insee": "35238",
        "surface_m2": 75.0,
        "nb_pieces": 4,
        "nb_logements": 1
    })
    assert response.status_code == 200
    assert response.json()["nom_commune"] == "Rennes"

@patch("p13.ml.predict.predict_batch_csv")
@patch("pandas.read_csv")
def test_predict_batch_success(mock_read_csv, mock_predict_batch):
    mock_df = pd.DataFrame([
        {"code_insee": "35238", "surface_m2": 75.0, "nb_pieces": 4, "nb_logements": 1}
    ])
    mock_read_csv.return_value = mock_df
    mock_predict_batch.return_value = mock_df
    
    content = "code_insee,surface_m2,nb_pieces,nb_logements\n35238,75.0,4,1"
    response = client.post("/batch", files={"file": ("test.csv", content)})
    assert response.status_code == 200
    assert len(response.json()) == 1

def test_predict_batch_invalid_file():
    response = client.post("/batch", files={"file": ("test.txt", "not a csv")})
    assert response.status_code == 400
