import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)

@patch("api.app.routers.ml.train_all")
def test_train_models_success(mock_train_all):
    mock_train_all.return_value = {"result": "success"}
    response = client.post("/ml/train")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["results"] == {"result": "success"}

@patch("api.app.routers.ml.train_all")
def test_train_models_failure(mock_train_all):
    mock_train_all.side_effect = Exception("Training failed")
    response = client.post("/ml/train")
    assert response.status_code == 500
    assert "Training failed" in response.json()["detail"]

@patch("api.app.routers.ml.get_model_metadata")
def test_list_models_success(mock_get_meta):
    mock_get_meta.return_value = {"model1": {"type": "rf"}}
    response = client.get("/ml/models")
    assert response.status_code == 200
    assert "model1" in response.json()

@patch("api.app.routers.ml.get_model_metadata")
def test_list_models_not_found(mock_get_meta):
    mock_get_meta.return_value = None
    response = client.get("/ml/models")
    assert response.status_code == 404
    assert "Aucun modèle entraîné" in response.json()["detail"]

@patch("api.app.routers.ml.get_model_metadata")
def test_get_metrics(mock_get_meta):
    mock_get_meta.return_value = {
        "model1": {"metrics": {"accuracy": 0.9}},
        "model2": {"metrics": {"accuracy": 0.8}}
    }
    response = client.get("/ml/metrics")
    assert response.status_code == 200
    assert response.json() == {"model1": {"accuracy": 0.9}, "model2": {"accuracy": 0.8}}