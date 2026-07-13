import pytest
from pydantic import ValidationError
from api.app.schemas import (
    HealthResponse,
    CommuneResponse,
    LogementRequest,
    PredictionsBlock,
    PredictionResponse,
    LogementImpact,
    LogementPredictionResponse,
    TrainResponse,
)

def test_health_response_model():
    response = HealthResponse(status="OK", database="PostgreSQL")
    assert response.status == "OK"
    assert response.database == "PostgreSQL"

def test_commune_response_model():
    response = CommuneResponse(code_insee="35238", nom_commune="Rennes", population=1000)
    assert response.code_insee == "35238"
    assert response.nom_commune == "Rennes"
    assert response.population == 1000

def test_logement_request_model_valid():
    request = LogementRequest(code_insee="35238", surface_m2=75.0, nb_pieces=4, nb_logements=1)
    assert request.code_insee == "35238"
    assert request.surface_m2 == 75.0
    assert request.nb_pieces == 4
    assert request.nb_logements == 1

def test_logement_request_model_invalid_surface():
    with pytest.raises(ValidationError):
        LogementRequest(code_insee="35238", surface_m2=-1, nb_pieces=4, nb_logements=1)

def test_logement_request_model_invalid_nb_pieces():
    with pytest.raises(ValidationError):
        LogementRequest(code_insee="35238", surface_m2=75.0, nb_pieces=0, nb_logements=1)

def test_predictions_block_model():
    block = PredictionsBlock(
        nb_eleves_maternelle=10.0,
        nb_eleves_elementaire=50.0,
        nb_classes_estimees=2.0,
        nb_eleves_total=60.0
    )
    assert block.nb_eleves_maternelle == 10.0
    assert block.nb_eleves_elementaire == 50.0
    assert block.nb_classes_estimees == 2.0
    assert block.nb_eleves_total == 60.0

def test_prediction_response_model():
    block = PredictionsBlock(
        nb_eleves_maternelle=10.0,
        nb_eleves_elementaire=50.0,
        nb_classes_estimees=2.0,
        nb_eleves_total=60.0
    )
    response = PredictionResponse(
        code_insee="35238",
        nom_commune="Rennes",
        predictions=block,
        features_utilisees={"feature1": 1.0, "feature2": 2.0}
    )
    assert response.code_insee == "35238"
    assert response.nom_commune == "Rennes"
    assert response.predictions.nb_eleves_total == 60.0
    assert response.features_utilisees["feature1"] == 1.0

def test_logement_impact_model():
    impact = LogementImpact(
        enfants_estimes=5.0,
        maternelle_estimee=1.0,
        elementaire_estimee=4.0,
        classes_supplementaires=1.0
    )
    assert impact.enfants_estimes == 5.0
    assert impact.maternelle_estimee == 1.0
    assert impact.elementaire_estimee == 4.0
    assert impact.classes_supplementaires == 1.0

def test_logement_prediction_response_model():
    block = PredictionsBlock(
        nb_eleves_maternelle=10.0,
        nb_eleves_elementaire=50.0,
        nb_classes_estimees=2.0,
        nb_eleves_total=60.0
    )
    impact = LogementImpact(
        enfants_estimes=5.0,
        maternelle_estimee=1.0,
        elementaire_estimee=4.0,
        classes_supplementaires=1.0
    )
    response = LogementPredictionResponse(
        code_insee="35238",
        nom_commune="Rennes",
        predictions=block,
        features_utilisees={"f1": 1.0},
        logement={"surface": 75.0},
        impact_logement=impact
    )
    assert response.nom_commune == "Rennes"
    assert response.impact_logement.classes_supplementaires == 1.0

def test_train_response_model():
    response = TrainResponse(status="success", results={"accuracy": 0.95})
    assert response.status == "success"
    assert response.results["accuracy"] == 0.95
