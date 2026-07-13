import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.app.main import app

client = TestClient(app)

@patch("p13.db.get_engine")
def test_health_check_ok(mock_get_engine):
    # Mock the database connection to succeed
    mock_conn = MagicMock()
    mock_get_engine.return_value.__enter__.return_value = mock_conn
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"

@patch("p13.db.get_engine")
def test_health_check_degraded(mock_get_engine):
    # Mock the database connection to fail
    mock_get_engine.return_value.__enter__.return_value.execute.side_effect = Exception("DB Error")
    
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "degraded"
    assert data["database"] == "ok"
