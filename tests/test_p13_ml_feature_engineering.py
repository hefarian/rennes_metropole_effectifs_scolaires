import pytest
import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator
from p13.ml.feature_engineering import (
    add_interaction_features,
    target_encode,
    encode_commune,
    add_lag_features,
    get_lag_feature_names,
    spatial_cross_validate,
    spatial_train_test_split
)

# --- Test Interaction Features ---
def test_add_interaction_features():
    df = pd.DataFrame({
        "population": [1000, 2000],
        "pop_0_14_pct": [20.0, 25.0],
        "nb_permis_logements": [50, 100],
        "densite": [500, 600],
        "natalite": [10, 12],
        "log_collectif": [100, 200],
        "log_individuel": [400, 800]
    })
    result = add_interaction_features(df)

    assert "nb_enfants_0_14" in result.columns
    assert result["nb_enfants_0_14"].iloc[0] == 200.0  # 1000 * 20 / 100
    assert "taux_croissance_logements" in result.columns
    assert result["taux_croissance_logements"].iloc[0] == 0.05  # 50 / 1000
    assert "densite_natalite" in result.columns
    assert result["densite_natalite"].iloc[0] == 5000.0  # 500 * 10 (densité × natalité)
    assert "pct_collectif" in result.columns
    assert result["pct_collectif"].iloc[0] == 100 / 500  # 100 / (100+400)

# --- Test Target Encoding ---
def test_target_encode():
    df = pd.DataFrame({
        "cat": ["A", "A", "B", "B", "C"],
        "target": [1, 2, 3, 4, 5]
    })
    # Global mean = 3.0
    # A: mean=1.5, count=2. Smoothed = (2*1.5 + 10*3.0) / (2+10) = 33/12 = 2.75
    # B: mean=3.5, count=2. Smoothed = (2*3.5 + 10*3.0) / (2+10) = 37/12 ≈ 3.0833
    encoded = target_encode(df, "cat", "target", smoothing=10.0)
    assert encoded.iloc[0] == pytest.approx(2.75)
    assert encoded.iloc[2] == pytest.approx((2 * 3.5 + 10 * 3.0) / (2 + 10))

def test_encode_commune():
    df = pd.DataFrame({
        "code_insee": ["35238", "35238", "35001"],
        "target": [10, 20, 30]
    })
    # Group 35238: mean=15, count=2. Global=20.
    # Smoothed = (2*15 + 10*20) / (2+10) = 230/12 = 19.166...
    result = encode_commune(df, "target", "code_insee")
    assert "code_insee_te_target" in result.columns
    assert result["code_insee_te_target"].iloc[0] == pytest.approx(19.166666666666666)

# --- Test Lag Features ---
def test_add_lag_features():
    df = pd.DataFrame({
        "code_insee": ["X", "X", "X", "X"],
        "rentree": [2020, 2021, 2022, 2023],
        "nb_eleves_maternelle": [10, 20, 30, 40]
    })
    result = add_lag_features(df, target_cols=["nb_eleves_maternelle"])

    assert "nb_eleves_maternelle_lag1" in result.columns
    assert result["nb_eleves_maternelle_lag1"].iloc[1] == 10.0
    assert np.isnan(result["nb_eleves_maternelle_lag1"].iloc[0])

    assert "nb_eleves_maternelle_rolling_mean3" in result.columns
    # Moyenne glissante calculée sur les valeurs PASSÉES (shift(1) avant rolling) :
    # au rang 2023, la fenêtre couvre les 3 années précédentes disponibles (10, 20, 30)
    assert result["nb_eleves_maternelle_rolling_mean3"].iloc[3] == pytest.approx(20.0)

def test_get_lag_feature_names():
    names = get_lag_feature_names(["target1"], lags=[1], rolling_windows=[3])
    assert "target1_lag1" in names
    assert "target1_rolling_mean3" in names
    assert "target1_delta1" in names

# --- Test Spatial Validation ---
def test_spatial_cross_validate():
    # Dummy data
    X = np.array([[1, 2], [3, 4], [5, 6], [7, 8], [9, 10], [11, 12]])
    y = np.array([1, 2, 3, 4, 5, 6])
    groups = np.array([1, 1, 2, 2, 3, 3])  # 3 groups

    class DummyModel(BaseEstimator):
        def fit(self, X, y, groups=None):
            return self
        def predict(self, X):
            return np.zeros(len(X))
        def score(self, X, y, **kwargs):
            return 0.8

    model = DummyModel()
    results = spatial_cross_validate(model, X, y, groups, n_splits=3)
    assert "mean_test" in results
    assert results["n_splits"] == 3

def test_spatial_train_test_split():
    df = pd.DataFrame({
        "code_insee": ["A", "A", "B", "B", "C", "C", "D", "D"],
        "val": [1, 2, 3, 4, 5, 6, 7, 8]
    })
    # 4 unique communes. test_size=0.5 -> 2 test communes.
    train, test = spatial_train_test_split(df, group_col="code_insee", test_size=0.5, random_state=42)

    assert len(train) == 4
    assert len(test) == 4
    assert len(train["code_insee"].unique()) == 2
    assert len(test["code_insee"].unique()) == 2