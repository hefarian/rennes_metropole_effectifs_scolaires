# tests/test_predict_coverage.py
"""Tests unitaires pour src/p13/ml/predict.py — objectif couverture >= 75%."""

import numpy as np
import pandas as pd
import pytest
from unittest import mock


# ── Helpers ──────────────────────────────────────────────────────────────────

class DummyModel:
    """Modèle factice qui renvoie toujours la même valeur."""
    def __init__(self, value=10.0):
        self._value = value

    def predict(self, X):
        return np.array([self._value])


def _base_df(**overrides):
    """Retourne un DataFrame minimal imitant la table ml_dataset_commune."""
    data = {
        "code_insee": ["35238"],
        "nom_commune": ["Rennes"],
        "population": [220000],
        "pop_0_14_pct": [17.5],
        "natalite": [12.0],
        "densite": [4300.0],
        "log_collectif": [80000],
        "log_individuel": [25000],
        "plh_logements": [5000],
        "nb_mutations": [3000],
        "nb_permis_logements": [1200],
        "nb_eleves_maternelle": [5000],
        "nb_eleves_elementaire": [8000],
        "nb_classes": [500],
        "rentree": [2023],
    }
    data.update(overrides)
    return pd.DataFrame(data)


# ── Tests _children_from_housing ────────────────────────────────────────────

def test_children_from_housing_defaults():
    from p13.ml.predict import _children_from_housing
    result = _children_from_housing(10, 80.0, 4)
    assert result == pytest.approx(10 * 0.35 * 1.0 * 1.0)


def test_children_from_housing_large_surface():
    from p13.ml.predict import _children_from_housing
    result = _children_from_housing(1, 200.0, 4)
    # surface_factor capped at 2.0
    assert result == pytest.approx(1 * 0.35 * 2.0 * 1.0)


def test_children_from_housing_zero_surface():
    from p13.ml.predict import _children_from_housing
    result = _children_from_housing(1, 0, 0)
    # surface=0 → factor=1.0 ; pieces=0 → factor=1.0
    assert result == pytest.approx(0.35)


def test_children_from_housing_many_pieces():
    from p13.ml.predict import _children_from_housing
    result = _children_from_housing(1, 80.0, 8)
    # pieces_factor capped at 1.5
    assert result == pytest.approx(0.35 * 1.0 * 1.5)


# ── Tests _load_model ──────────────────────────────────────────────────────

@mock.patch("p13.ml.predict.MODELS_DIR")
def test_load_model_file_not_found(mock_models_dir, tmp_path):
    mock_models_dir.__truediv__ = lambda self, name: tmp_path / name
    from p13.ml.predict import _load_model
    with pytest.raises(FileNotFoundError, match="Modèle"):
        _load_model("inexistant")


# ── Tests _load_model_features ─────────────────────────────────────────────

@mock.patch("p13.ml.predict.MODELS_DIR")
def test_load_model_features_with_meta(mock_models_dir, tmp_path):
    import json
    meta = {"features": ["a", "b", "c"]}
    meta_file = tmp_path / "test_meta.json"
    meta_file.write_text(json.dumps(meta), encoding="utf-8")
    mock_models_dir.__truediv__ = lambda self, name: tmp_path / name
    from p13.ml.predict import _load_model_features
    assert _load_model_features("test") == ["a", "b", "c"]


@mock.patch("p13.ml.predict.MODELS_DIR")
def test_load_model_features_no_meta(mock_models_dir, tmp_path):
    mock_models_dir.__truediv__ = lambda self, name: tmp_path / name
    from p13.ml.predict import _load_model_features
    from p13.ml.features import FEATURE_COLUMNS
    assert _load_model_features("inexistant") == FEATURE_COLUMNS


# ── Tests _get_commune_features ────────────────────────────────────────────

@mock.patch("p13.ml.predict.read_sql")
def test_get_commune_features_primary_query(mock_sql):
    mock_sql.return_value = _base_df()
    from p13.ml.predict import _get_commune_features
    result = _get_commune_features("35238")
    assert result["code_insee"] == "35238"
    assert result["nom_commune"] == "Rennes"
    assert "population" in result


@mock.patch("p13.ml.predict.read_sql")
def test_get_commune_features_fallback_query(mock_sql):
    # Premier appel vide → fallback query
    mock_sql.side_effect = [pd.DataFrame(), _base_df()]
    from p13.ml.predict import _get_commune_features
    result = _get_commune_features("35238")
    assert result["code_insee"] == "35238"


@mock.patch("p13.ml.predict.read_sql")
def test_get_commune_features_not_found(mock_sql):
    mock_sql.return_value = pd.DataFrame()
    from p13.ml.predict import _get_commune_features
    with pytest.raises(ValueError, match="Commune inconnue"):
        _get_commune_features("99999")


# ── Tests _get_lag_features ────────────────────────────────────────────────

@mock.patch("p13.ml.predict.read_sql")
def test_get_lag_features_with_history(mock_sql):
    mock_sql.return_value = pd.DataFrame({
        "rentree": [2020, 2021, 2022, 2023],
        "nb_eleves_maternelle": [100, 110, 120, 130],
        "nb_eleves_elementaire": [200, 210, 220, 230],
        "nb_classes": [10, 11, 12, 13],
    })
    from p13.ml.predict import _get_lag_features
    result = _get_lag_features("35238")
    assert "nb_eleves_maternelle_lag1" in result
    assert "nb_eleves_elementaire_rolling_mean3" in result
    assert "nb_classes_delta1" in result


@mock.patch("p13.ml.predict.read_sql")
def test_get_lag_features_empty(mock_sql):
    mock_sql.return_value = pd.DataFrame()
    from p13.ml.predict import _get_lag_features
    assert _get_lag_features("99999") == {}


# ── Tests predict_commune ──────────────────────────────────────────────────

@mock.patch("p13.ml.predict._get_lag_features")
@mock.patch("p13.ml.predict._get_commune_features")
@mock.patch("p13.ml.predict._load_model")
@mock.patch("p13.ml.predict._load_model_features")
def test_predict_commune(mock_features_list, mock_model, mock_commune, mock_lags):
    mock_model.return_value = DummyModel(100.0)
    mock_features_list.return_value = ["population"]
    mock_commune.return_value = {
        "code_insee": "35238", "nom_commune": "Rennes", "population": 220000.0,
    }
    mock_lags.return_value = {}

    from p13.ml.predict import predict_commune
    result = predict_commune("35238")
    assert result["code_insee"] == "35238"
    assert result["predictions"]["nb_eleves_maternelle"] == 100.0
    assert result["predictions"]["nb_eleves_elementaire"] == 100.0
    assert result["predictions"]["nb_eleves_total"] == 200.0
    assert "features_utilisees" in result


# ── Tests predict_logement ─────────────────────────────────────────────────

@mock.patch("p13.ml.predict.predict_commune")
def test_predict_logement(mock_pred):
    mock_pred.return_value = {
        "code_insee": "35238",
        "nom_commune": "Rennes",
        "predictions": {
            "nb_eleves_maternelle": 100, "nb_eleves_elementaire": 200,
            "nb_classes_estimees": 12, "nb_eleves_total": 300,
        },
        "features_utilisees": {},
    }
    from p13.ml.predict import predict_logement
    result = predict_logement("35238", 80.0, 4, 1)
    assert "impact_logement" in result
    assert result["impact_logement"]["enfants_estimes"] > 0
    assert result["logement"]["surface_m2"] == 80.0


# ── Tests predict_batch_csv ────────────────────────────────────────────────

@mock.patch("p13.ml.predict.predict_logement")
def test_predict_batch_csv(mock_logement):
    mock_logement.return_value = {
        "code_insee": "35238", "nom_commune": "Rennes",
        "predictions": {
            "nb_eleves_maternelle": 100, "nb_eleves_elementaire": 200,
            "nb_classes_estimees": 12, "nb_eleves_total": 300,
        },
        "features_utilisees": {},
        "impact_logement": {
            "enfants_estimes": 0.35, "maternelle_estimee": 0.16,
            "elementaire_estimee": 0.19, "classes_supplementaires": 0.01,
        },
    }
    df = pd.DataFrame({
        "code_insee": ["35238"],
        "surface_m2": [80.0],
        "nb_pieces": [4],
        "nb_logements": [1],
    })
    from p13.ml.predict import predict_batch_csv
    result = predict_batch_csv(df)
    assert len(result) == 1
    assert "enfants_estimes" in result.columns


def test_predict_batch_csv_missing_columns():
    df = pd.DataFrame({"code_insee": ["35238"]})  # manque surface_m2, nb_pieces
    from p13.ml.predict import predict_batch_csv
    with pytest.raises(ValueError, match="Colonnes manquantes"):
        predict_batch_csv(df)


# ── Tests get_model_metadata ───────────────────────────────────────────────

@mock.patch("p13.ml.predict.MODELS_DIR")
def test_get_model_metadata(mock_models_dir, tmp_path):
    import json
    for target in ["nb_eleves_maternelle", "nb_eleves_elementaire", "nb_classes"]:
        meta_file = tmp_path / f"{target}_meta.json"
        meta_file.write_text(json.dumps({"model": "rf"}), encoding="utf-8")
    mock_models_dir.__truediv__ = lambda self, name: tmp_path / name
    from p13.ml.predict import get_model_metadata
    meta = get_model_metadata()
    assert len(meta) == 3
