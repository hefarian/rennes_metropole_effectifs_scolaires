"""Entraînement des modèles de prédiction des effectifs scolaires."""

from __future__ import annotations

import json
from datetime import datetime

import joblib
import mlflow
import mlflow.sklearn
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import (
    GroupKFold,
    RandomizedSearchCV,
    cross_val_score,
    train_test_split,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from p13.config import MLFLOW_TRACKING_URI, MODELS_DIR
from p13.db import read_sql
from p13.ml.feature_engineering import (
    add_interaction_features,
    add_lag_features,
    spatial_cross_validate,
    spatial_train_test_split,
)
from p13.ml.features import (
    ALL_TARGETS,
    ENGINEERED_FEATURES,
    FEATURE_COLUMNS,
    LAG_LAGS,
    LAG_WINDOWS,
    SPATIAL_GROUP_COLUMN,
)


import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan, linear_rainbow
from scipy.stats import shapiro

def validate_linear_model(model, X, y):
    """
    Effectue les tests statistiques sur le modèle.
    Retourne True si le modèle est 'valide', False sinon.
    """
    # Statsmodels nécessite une constante pour les tests
    X_sm = sm.add_constant(X)
    results = sm.OLS(y, X_sm).fit()
    
    # 1. Test de linéarité (Rainbow)
    _, p_rainbow = linear_rainbow(results)
    
    # 2. Test d'homoscédasticité (Breusch-Pagan)
    _, p_bp, _, _ = het_breuschpagan(results.resid, results.model.exog)
    
    # 3. Test de normalité des résidus (Shapiro-Wilk)
    _, p_shapiro = shapiro(results.resid)
    
    # Logique de décision
    # On rejette si la linéarité est rompue ou si les résidus sont problématiques
    is_valid = (p_rainbow > 0.05) and (p_bp > 0.05) and (p_shapiro > 0.05)
    
    return is_valid, {"rainbow": p_rainbow, "bp": p_bp, "shapiro": p_shapiro}
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
        "n_estimators": [50, 100, 200, 300],
        "max_depth": [4, 6, 8, 10, None],
        "min_samples_leaf": [1, 2, 4],
        "max_features": ["sqrt", "log2", 0.5, 0.7],
    },
    "gradient_boosting": {
        "n_estimators": [50, 100, 200, 300],
        "max_depth": [2, 3, 4, 5, 6],
        "learning_rate": [0.01, 0.05, 0.1, 0.2, 0.3],
        "subsample": [0.6, 0.8, 1.0],
        "min_samples_leaf": [1, 2, 4, 8],
    },
    # Ridge est dans un Pipeline(scaler, model) → préfixe "model__" requis
    "ridge": {
        "model__alpha": [0.001, 0.01, 0.1, 1.0, 10.0, 100.0, 1000.0],
    },
}


def _tune_model(
    name: str,
    model,
    X_train: np.ndarray,
    y_train: np.ndarray,
    groups_train: np.ndarray | None = None,
    use_spatial_cv: bool = False,
) -> object:
    """Lance un RandomizedSearchCV si un param_grid est défini pour ce modèle.

    Si use_spatial_cv est activé et que des groupes sont fournis, le tuning
    utilise un GroupKFold (pas de fuite de données inter-communes pendant la
    recherche d'hyperparamètres). Sinon, comportement inchangé (cv=3 aléatoire).
    """
    grid = PARAM_GRIDS.get(name)
    if grid is None:
        model.fit(X_train, y_train)
        return model

    if use_spatial_cv and groups_train is not None:
        n_groups = len(np.unique(groups_train))
        cv = GroupKFold(n_splits=min(5, n_groups))
        search = RandomizedSearchCV(
            model,
            param_distributions=grid,
            n_iter=20,
            cv=cv,
            scoring="r2",
            random_state=42,
            n_jobs=-1,
            refit=True,
        )
        search.fit(X_train, y_train, groups=groups_train)
    else:
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


def build_feature_matrix(
    df: pd.DataFrame,
    feature_cols: list[str],
    use_engineering: bool = False,
    use_lags: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    """Construit la matrice de features avec enrichissements optionnels.

    Args:
        df: DataFrame brut de la base.
        feature_cols: Liste de features de base à utiliser.
        use_engineering: Si True, ajoute les features d'interaction/ratio.
        use_lags: Si True, ajoute les features de lag temporel.
    Returns:
        (df_enriched, final_feature_cols)
    """
    enriched = df.copy()

    if use_engineering:
        enriched = add_interaction_features(enriched)
        cols = list(feature_cols) + [c for c in ENGINEERED_FEATURES if c in enriched.columns]
    else:
        cols = list(feature_cols)

    if use_lags:
        enriched = add_lag_features(
            enriched,
            target_cols=ALL_TARGETS,
            group_col=SPATIAL_GROUP_COLUMN,
            time_col="rentree",
            lags=LAG_LAGS,
            rolling_windows=LAG_WINDOWS,
        )
        lag_cols = [c for c in enriched.columns if any(
            c.startswith(f"{t}_lag") or c.startswith(f"{t}_rolling") or c.startswith(f"{t}_delta")
            for t in ALL_TARGETS
        )]
        cols = cols + lag_cols
        # Supprimer les lignes avec NaN sur les features de lag
        enriched = enriched.dropna(subset=[c for c in lag_cols if c in enriched.columns])

    # Garder uniquement les colonnes qui existent réellement
    cols = [c for c in cols if c in enriched.columns]
    return enriched, cols


def train_all(
    rentree: int | None = None,
    use_engineering: bool = True,
    use_spatial_cv: bool = True,
    use_lags: bool = False,
) -> dict:
    """Entraîne tous les modèles pour les 3 cibles.

    Args:
        rentree: Filtrer sur une année de rentrée spécifique (None = toutes).
        use_engineering: Active les features d'interaction et de ratio.
        use_spatial_cv: Remplace le KFold aléatoire par un GroupKFold par communes.
        use_lags: Active les features de lag temporel (requiert plusieurs années).
    """
    mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
    try:
        mlflow.set_experiment("p13-effectifs")
    except Exception:
        mlflow.create_experiment("p13-effectifs")
        mlflow.set_experiment("p13-effectifs")

    df = load_training_data(rentree)
    if len(df) < 10:
        raise ValueError(f"Dataset insuffisant ({len(df)} lignes). Lancez d'abord l'ETL.")

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    # Construction de la matrice de features
    df_enriched, feature_cols = build_feature_matrix(
        df,
        feature_cols=FEATURE_COLUMNS,
        use_engineering=use_engineering,
        use_lags=use_lags,
    )

    results = {}
    for target in ALL_TARGETS:
        valid_df = df_enriched.dropna(subset=feature_cols + [target])
        X = valid_df[feature_cols].values
        y = valid_df[target].values
        groups = valid_df[SPATIAL_GROUP_COLUMN].values if SPATIAL_GROUP_COLUMN in valid_df.columns else None

        if use_spatial_cv and groups is not None:
            df_train, df_test = spatial_train_test_split(valid_df, group_col=SPATIAL_GROUP_COLUMN)
            X_train = df_train[feature_cols].values
            X_test = df_test[feature_cols].values
            y_train = df_train[target].values
            y_test = df_test[target].values
            groups_train = df_train[SPATIAL_GROUP_COLUMN].values
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            groups_train = None

        best_name, best_model, best_score = None, None, -np.inf
        target_results = {}

        for name, model in get_model_candidates().items():
            with mlflow.start_run(run_name=f"{target}_{name}"):
                tuned = _tune_model(
                    name, model, X_train, y_train,
                    groups_train=groups_train,
                    use_spatial_cv=use_spatial_cv,
                )

                # Si c'est un modèle linéaire, on teste sa validité
                if name in ["linear_regression"]:
                    is_valid, stats = validate_linear_model(tuned, X_train, y_train)
                    if not is_valid:
                        print(f"Modèle {name} rejeté par les tests de diagnostic: {stats}")
                        continue # Passe au modèle suivant (RandomForest, etc.)

                y_pred = tuned.predict(X_test)
                m = _metrics(y_test, y_pred)

                # Validation croisée (spatiale ou aléatoire)
                if use_spatial_cv and groups is not None:
                    spatial_result = spatial_cross_validate(
                        tuned, X, y, groups,
                        n_splits=min(5, len(np.unique(groups))),
                        scoring="r2",
                    )
                    cv_mean = spatial_result["mean_test"]
                    cv_std = spatial_result["std_test"]
                    overfit_gap = spatial_result["overfit_gap"]
                    mlflow.log_metric("spatial_cv_r2_mean", cv_mean)
                    mlflow.log_metric("spatial_cv_r2_std", cv_std)
                    mlflow.log_metric("spatial_overfit_gap", overfit_gap)
                    # Score utilisé pour sélectionner le meilleur modèle :
                    # la moyenne spatiale robuste, PAS le r2 du split unique
                    # (m["r2"]), qui est bruité avec seulement quelques
                    # communes dans le test (cf. notebook 06).
                    selection_score = cv_mean
                else:
                    cv = cross_val_score(
                        tuned, X, y, cv=min(5, len(df) // 3), scoring="r2", n_jobs=-1
                    )
                    cv_mean = float(cv.mean())
                    cv_std = float(cv.std())
                    overfit_gap = None
                    selection_score = m["r2"]

                mlflow.log_param("target", target)
                mlflow.log_param("model", name)
                mlflow.log_param("use_engineering", use_engineering)
                mlflow.log_param("use_spatial_cv", use_spatial_cv)
                mlflow.log_param("use_lags", use_lags)
                mlflow.log_param("n_features", len(feature_cols))
                if hasattr(tuned, "get_params"):
                    tuned_params = {
                        k: v for k, v in tuned.get_params().items()
                        if not hasattr(v, "__call__") and v is not None
                    }
                    mlflow.log_params({f"hp_{k}": str(v) for k, v in list(tuned_params.items())[:20]})
                mlflow.log_metrics(m)
                mlflow.log_metric("cv_r2_mean", cv_mean)
                mlflow.log_metric("selection_score", selection_score)
                try:
                    mlflow.sklearn.log_model(tuned, "model")
                except Exception:
                    pass  # Endpoint /logged-models non supporté sur cette version MLflow

                target_results[name] = {
                    **m,
                    "cv_r2_mean": cv_mean,
                    "cv_r2_std": cv_std,
                    "overfit_gap": overfit_gap,
                    "selection_score": selection_score,
                }
                if selection_score > best_score:
                    best_score = selection_score
                    best_name = name
                    best_model = tuned

        model_path = MODELS_DIR / f"{target}_best.joblib"
        joblib.dump(best_model, model_path)
        meta = {
            "target": target,
            "model": best_name,
            "metrics": target_results[best_name],
            "features": feature_cols,
            "use_engineering": use_engineering,
            "use_spatial_cv": use_spatial_cv,
            "use_lags": use_lags,
            "trained_at": datetime.now().isoformat(),
            "n_samples": len(valid_df),
        }
        meta_path = MODELS_DIR / f"{target}_meta.json"
        meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

        results[target] = {"best_model": best_name, **target_results[best_name]}

    summary_path = MODELS_DIR / "training_summary.json"
    summary_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Entraînement des modèles P13.")
    parser.add_argument("--rentree", type=int, default=None, help="Filtrer sur une rentrée")
    parser.add_argument("--engineering", action="store_true", help="Activer les features d'interaction")
    parser.add_argument("--spatial-cv", action="store_true", help="Validation croisée spatiale (GroupKFold)")
    parser.add_argument("--lags", action="store_true", help="Activer les features de lag temporel")
    args = parser.parse_args()

    results = train_all(
        rentree=args.rentree,
        use_engineering=args.engineering,
        use_spatial_cv=args.spatial_cv,
        use_lags=args.lags,
    )
    print(json.dumps(results, indent=2))