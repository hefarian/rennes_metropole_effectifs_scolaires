# tests/test_train_coverage.py
"""Tests unitaires pour src/p13/ml/train.py — objectif couverture >= 75%."""

import json
import numpy as np
import pandas as pd
import pytest
from unittest import mock


# ── Helpers ──────────────────────────────────────────────────────────────────

def _make_df(n=30):
    """Génère un DataFrame d'entraînement synthétique avec n lignes."""
    rng = np.random.RandomState(42)
    return pd.DataFrame({
        "code_insee": [f"{35000 + i}" for i in range(n)],
        "population": rng.randint(500, 50000, n).tolist(),
        "pop_0_14_pct": rng.uniform(10, 25, n).tolist(),
        "natalite": rng.uniform(8, 15, n).tolist(),
        "nb_permis_logements": rng.randint(0, 500, n).tolist(),
        "densite": rng.uniform(100, 5000, n).tolist(),
        "log_collectif": rng.randint(100, 10000, n).tolist(),
        "log_individuel": rng.randint(100, 10000, n).tolist(),
        "plh_logements": rng.randint(0, 3000, n).tolist(),
        "nb_mutations": rng.randint(0, 2000, n).tolist(),
        "nb_eleves_maternelle": rng.randint(50, 3000, n).tolist(),
        "nb_eleves_elementaire": rng.randint(80, 5000, n).tolist(),
        "nb_classes": rng.randint(3, 200, n).tolist(),
        "rentree": [2020 + (i % 4) for i in range(n)],
    })


# ── Tests _mape ─────────────────────────────────────────────────────────────

def test_mape_basic():
    from p13.ml.train import _mape
    y_true = np.array([100.0, 200.0])
    y_pred = np.array([110.0, 180.0])
    result = _mape(y_true, y_pred)
    # (|10/100| + |20/200|) / 2 * 100 = 10%
    assert result == pytest.approx(10.0)


def test_mape_all_zeros():
    from p13.ml.train import _mape
    y_true = np.array([0.0, 0.0])
    y_pred = np.array([1.0, 2.0])
    assert _mape(y_true, y_pred) == 0.0


# ── Tests _metrics ──────────────────────────────────────────────────────────

def test_metrics_keys():
    from p13.ml.train import _metrics
    y = np.array([1.0, 2.0, 3.0])
    m = _metrics(y, y)
    assert set(m.keys()) == {"rmse", "mae", "r2", "mape"}
    assert m["rmse"] == 0.0
    assert m["mae"] == 0.0
    assert m["r2"] == 1.0


# ── Tests get_model_candidates ──────────────────────────────────────────────

def test_get_model_candidates():
    from p13.ml.train import get_model_candidates
    candidates = get_model_candidates()
    assert "linear_regression" in candidates
    assert "ridge" in candidates
    assert "random_forest" in candidates
    assert "gradient_boosting" in candidates
    assert len(candidates) == 4


# ── Tests _tune_model ───────────────────────────────────────────────────────

def test_tune_model_no_grid():
    from p13.ml.train import _tune_model
    from sklearn.linear_model import LinearRegression
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    model = Pipeline([("scaler", StandardScaler()), ("model", LinearRegression())])
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    result = _tune_model("linear_regression", model, X, y)
    # Doit être fitté car pas de grid → fit direct
    pred = result.predict(X)
    assert len(pred) == 5


def test_tune_model_with_grid():
    from p13.ml.train import _tune_model
    from sklearn.ensemble import RandomForestRegressor

    model = RandomForestRegressor(n_estimators=10, random_state=42)
    X = np.random.RandomState(42).randn(20, 2)
    y = X[:, 0] * 2 + X[:, 1]
    result = _tune_model("random_forest", model, X, y)
    pred = result.predict(X)
    assert len(pred) == 20


# ── Tests build_feature_matrix ──────────────────────────────────────────────

def test_build_feature_matrix_base():
    from p13.ml.train import build_feature_matrix, FEATURE_COLUMNS
    df = _make_df(20)
    enriched, cols = build_feature_matrix(df, FEATURE_COLUMNS)
    assert cols == FEATURE_COLUMNS
    assert len(enriched) == 20


def test_build_feature_matrix_engineering():
    from p13.ml.train import build_feature_matrix, FEATURE_COLUMNS, ENGINEERED_FEATURES
    df = _make_df(20)
    enriched, cols = build_feature_matrix(df, FEATURE_COLUMNS, use_engineering=True)
    for eng_col in ENGINEERED_FEATURES:
        assert eng_col in enriched.columns
    assert len(cols) > len(FEATURE_COLUMNS)


def test_build_feature_matrix_lags():
    from p13.ml.train import build_feature_matrix, FEATURE_COLUMNS
    df = _make_df(40)
    enriched, cols = build_feature_matrix(df, FEATURE_COLUMNS, use_lags=True)
    lag_cols = [c for c in cols if "lag" in c or "rolling" in c or "delta" in c]
    assert len(lag_cols) > 0


def test_build_feature_matrix_full():
    from p13.ml.train import build_feature_matrix, FEATURE_COLUMNS
    df = _make_df(40)
    enriched, cols = build_feature_matrix(
        df, FEATURE_COLUMNS, use_engineering=True, use_lags=True
    )
    assert len(cols) > len(FEATURE_COLUMNS)


# ── Tests load_training_data ────────────────────────────────────────────────

@mock.patch("p13.ml.train.read_sql")
def test_load_training_data_all(mock_sql):
    mock_sql.return_value = _make_df(20)
    from p13.ml.train import load_training_data
    result = load_training_data()
    assert len(result) > 0


@mock.patch("p13.ml.train.read_sql")
def test_load_training_data_filtered(mock_sql):
    mock_sql.return_value = _make_df(20)
    from p13.ml.train import load_training_data
    result = load_training_data(rentree=2023)
    mock_sql.assert_called_once()
    # Vérifie que la requête contient le filtre
    call_args = mock_sql.call_args[0][0]
    assert "2023" in call_args


# ── Tests PARAM_GRIDS ──────────────────────────────────────────────────────

def test_param_grids_exist():
    from p13.ml.train import PARAM_GRIDS
    assert "random_forest" in PARAM_GRIDS
    assert "gradient_boosting" in PARAM_GRIDS
    assert "ridge" in PARAM_GRIDS
    assert "linear_regression" not in PARAM_GRIDS  # pas de grid pour LR


# ── Tests train_all (intégration légère avec mocks MLflow) ──────────────────

@mock.patch("p13.ml.train.mlflow")
@mock.patch("p13.ml.train.read_sql")
def test_train_all_basic(mock_sql, mock_mlflow, tmp_path):
    """Test train_all de bout en bout avec MLflow mocké."""
    mock_sql.return_value = _make_df(30)

    # Mock MLflow context manager
    mock_run = mock.MagicMock()
    mock_mlflow.start_run.return_value.__enter__ = mock.MagicMock(return_value=mock_run)
    mock_mlflow.start_run.return_value.__exit__ = mock.MagicMock(return_value=False)

    from p13.ml import train

    # Rediriger MODELS_DIR vers un dossier temp
    with mock.patch.object(train, "MODELS_DIR", tmp_path):
        results = train.train_all(
            use_engineering=False, use_spatial_cv=False, use_lags=False
        )

    assert isinstance(results, dict)
    for target in train.ALL_TARGETS:
        assert target in results
        assert "best_model" in results[target]
        assert "r2" in results[target]

    # Vérifier que les fichiers modèles et meta ont été créés
    for target in train.ALL_TARGETS:
        assert (tmp_path / f"{target}_best.joblib").exists()
        assert (tmp_path / f"{target}_meta.json").exists()
    assert (tmp_path / "training_summary.json").exists()


@mock.patch("p13.ml.train.read_sql")
def test_train_all_insufficient_data(mock_sql):
    mock_sql.return_value = _make_df(3)  # < 10 lignes
    from p13.ml.train import train_all
    with mock.patch("p13.ml.train.mlflow"):
        with pytest.raises(ValueError, match="Dataset insuffisant"):
            train_all()
