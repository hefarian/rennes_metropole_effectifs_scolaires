"""Entraînement des modèles de prédiction des effectifs scolaires."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RandomizedSearchCV, cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from p13.config import MLFLOW_TRACKING_URI, MODELS_DIR
from p13.db import read_sql
from p13.ml.features import ALL_TARGETS, FEATURE_COLUMNS


def _mape(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    mask = y_true != 0
    if not mask.any():
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)


def _metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
        "mape": _mape(y_true, y_pred),
    }


def get_model_candidates() -> dict:
    return {
        "linear_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LinearRegression()),
        ]),
        "ridge": Pipeline([
            ("scaler", StandardScaler()),
            ("model", Ridge(alpha=1.0)),
        ]),
        "random_forest": RandomForestRegressor(
            n_estimators=100, max_depth=8, random_state=42, n_jobs=-1
        ),
        "gradient_boosting": GradientBoostingRegressor(
            n_estimators=100, max_depth=4, random_state=42
        ),
    }


PARAM_GRIDS: dict = {
    "random_forest": {
        "n_estimators": [50, 100, 200],
        "max_depth": [4, 6, 8, None],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2", 0.5],
    },
    "gradient_boosting": {
        "n_estimators": [50, 100, 200],
        "max_depth": [3, 4, 5],
        "learning_rate": [0.05, 0.1, 0.2],
        "subsample": [0.8, 1.0],
        "min_samples_leaf": [1, 2, 4],
    },
    "ridge": {
        "model__alpha": [0.01, 0.1, 1.0, 10.0, 100.0],
    },
}


def _tune_model(name: str, model, X_train: np.ndarray, y_train: np.ndarray) -> object:
    """Lance un RandomizedSearchCV si un param_grid est défini pour ce modèle."""
    grid = PARAM_GRIDS.get(name)
    if grid is None:
        model.fit(X_train, y_train)
        return model
    search = RandomizedSearchCV(
        model,
        param_distributions=grid,
        n_iter=20,
        cv=3,
        scoring="r2",
        random_state=42,
        n_jobs=-1,
        refit=True,
    )
    search.fit(X_train, y_train)
    return search.best_estimator_


def load_training_data(rentree: int | None = None) -> pd.DataFrame:
    query = "SELECT * FROM ml_dataset_commune WHERE nb_eleves_maternelle IS NOT NULL"
    if rentree:
        query += f" AND rentree = {int(rentree)}"
    df = read_sql(query)
    return df.dropna(subset=FEATURE_COLUMNS + ALL_TARGETS)


def train_all(rentree: int | None = None) -> dict:
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    try:
        mlflow.set_experiment("p13-effectifs")
    except Exception:
        mlflow.create_experiment("p13-effectifs")
        mlflow.set_experiment("p13-effectifs")
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    df = load_training_data(rentree)
    if len(df) < 10:
        raise ValueError(f"Dataset insuffisant ({len(df)} lignes). Lancez d'abord l'ETL.")

    results = {}
    for target in ALL_TARGETS:
        X = df[FEATURE_COLUMNS].values
        y = df[target].values
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        best_name, best_model, best_score = None, None, -np.inf
        target_results = {}

        for name, model in get_model_candidates().items():
            with mlflow.start_run(run_name=f"{target}_{name}"):
                tuned = _tune_model(name, model, X_train, y_train)
                y_pred = tuned.predict(X_test)
                m = _metrics(y_test, y_pred)
                cv = cross_val_score(
                    tuned, X, y, cv=min(5, len(df) // 3), scoring="r2", n_jobs=-1
                )
                mlflow.log_param("target", target)
                mlflow.log_param("model", name)
                # Log best hyperparams found
                if hasattr(tuned, "get_params"):
                    tuned_params = {
                        k: v for k, v in tuned.get_params().items()
                        if not hasattr(v, "__call__") and v is not None
                    }
                    mlflow.log_params({f"hp_{k}": str(v) for k, v in list(tuned_params.items())[:20]})
                mlflow.log_metrics(m)
                mlflow.log_metric("cv_r2_mean", float(cv.mean()))
                mlflow.sklearn.log_model(tuned, "model")

                target_results[name] = {**m, "cv_r2_mean": float(cv.mean())}
                if m["r2"] > best_score:
                    best_score = m["r2"]
                    best_name = name
                    best_model = tuned

        model_path = MODELS_DIR / f"{target}_best.joblib"
        joblib.dump(best_model, model_path)
        meta = {
            "target": target,
            "model": best_name,
            "metrics": target_results[best_name],
            "features": FEATURE_COLUMNS,
            "trained_at": datetime.now().isoformat(),
            "n_samples": len(df),
        }
        meta_path = MODELS_DIR / f"{target}_meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        results[target] = {"best_model": best_name, **target_results[best_name]}

    summary_path = MODELS_DIR / "training_summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    print(json.dumps(train_all(), indent=2))
