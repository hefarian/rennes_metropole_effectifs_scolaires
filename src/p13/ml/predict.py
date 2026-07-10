"""Inférence : prédiction des effectifs scolaires."""

from __future__ import annotations

import json

import joblib
import numpy as np
import pandas as pd

from p13.config import MODELS_DIR
from p13.db import read_sql
from p13.ml.feature_engineering import add_interaction_features
from p13.ml.features import (
    ALL_FEATURE_COLUMNS,
    ENGINEERED_FEATURES,
    FEATURE_COLUMNS,
    TARGET_CLASSES,
    TARGET_ELEMENTAIRE,
    TARGET_MATERNELLE,
)


def _load_model(target: str):
    path = MODELS_DIR / f"{target}_best.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"Modèle '{target}' introuvable. Entraînez d'abord : python -m p13.ml.train"
        )
    return joblib.load(path)


def _load_model_features(target: str) -> list[str]:
    """Lit la liste exacte de features depuis le metadata JSON du modèle sauvegardé.

    Garantit que le vecteur X envoyé au modèle correspond exactement à ce qui a servi
    à l'entraînement (4, 8 ou 9 features selon use_engineering/use_lags).
    """
    meta_path = MODELS_DIR / f"{target}_meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        return meta.get("features", FEATURE_COLUMNS)
    return FEATURE_COLUMNS


def _get_commune_features(code_insee: str) -> dict:
    """Récupère toutes les features disponibles pour une commune.

    Retourne ALL_FEATURE_COLUMNS + ENGINEERED_FEATURES calculés à la volée.
    predict_commune() choisira ensuite les colonnes utiles via _load_model_features().
    """
    df = read_sql(
        """
        SELECT d.*, c.nom_commune
        FROM ml_dataset_commune d
        JOIN communes c ON c.code_insee = d.code_insee
        WHERE d.code_insee = :code
        ORDER BY d.rentree DESC
        LIMIT 1
        """,
        {"code": code_insee},
    )
    if df.empty:
        df = read_sql(
            """
            SELECT c.code_insee, c.nom_commune, c.population,
                   s.cat_0_14_2020 AS pop_0_14_pct, s.natalite_2022 AS natalite,
                   s.densite_2021 AS densite, s.log_collectif, s.log_individuel,
                   s.plh_nb_log_a_const AS plh_logements,
                   COALESCE(dvf.nb, 0) AS nb_mutations,
                   COALESCE(p.nb, 0) AS nb_permis_logements
            FROM communes c
            LEFT JOIN stats_communes s ON s.code_insee = c.code_insee
            LEFT JOIN (
                SELECT code_insee, COUNT(*) AS nb FROM mutations_dvf
                WHERE annee >= EXTRACT(YEAR FROM NOW())::int - 3
                GROUP BY code_insee
            ) dvf ON dvf.code_insee = c.code_insee
            LEFT JOIN (SELECT code_insee, SUM(logements_crees) AS nb FROM permis_construire
                       WHERE code_insee IS NOT NULL GROUP BY code_insee) p
                ON p.code_insee = c.code_insee
            WHERE c.code_insee = :code
            """,
            {"code": code_insee},
        )
    if df.empty:
        raise ValueError(f"Commune inconnue : {code_insee}")

    # Calculer les features d'interaction (engineered)
    df_eng = add_interaction_features(df)
    row = df_eng.iloc[0]

    all_cols = ALL_FEATURE_COLUMNS + ENGINEERED_FEATURES
    features = {col: float(row.get(col, 0) or 0) for col in all_cols if col in df_eng.columns}
    return {"code_insee": code_insee, "nom_commune": row.get("nom_commune", ""), **features}


def _get_lag_features(code_insee: str) -> dict:
    """Récupère les features de lag temporel pour une commune.

    Utilisé uniquement si le modèle a été entraîné avec use_lags=True.
    Les lags sont calculés depuis les 4 dernières années d'historique.
    """
    df_hist = read_sql(
        """
        SELECT rentree, nb_eleves_maternelle, nb_eleves_elementaire, nb_classes
        FROM ml_dataset_commune
        WHERE code_insee = :code
        ORDER BY rentree DESC
        LIMIT 4
        """,
        {"code": code_insee},
    )
    if df_hist.empty:
        return {}

    df_hist = df_hist.sort_values("rentree")
    lag_data: dict = {}

    for target in [TARGET_MATERNELLE, TARGET_ELEMENTAIRE, TARGET_CLASSES]:
        if target not in df_hist.columns:
            continue
        vals = df_hist[target].dropna().tolist()
        for lag in [1, 2, 3]:
            lag_data[f"{target}_lag{lag}"] = float(vals[-lag]) if len(vals) >= lag else 0.0
        lag_data[f"{target}_rolling_mean3"] = float(np.mean(vals[-3:])) if vals else 0.0
        lag_data[f"{target}_delta1"] = float(vals[-1] - vals[-2]) if len(vals) >= 2 else 0.0

    return lag_data


def _children_from_housing(
    nb_logements: int,
    surface_m2: float,
    nb_pieces: int,
    taux_enfants_par_logement: float = 0.35,
) -> float:
    """Estimation heuristique d'enfants scolarisables (0-11 ans) liés à un logement.

    Calibration indicative (à affiner sur données locales DVF/effectifs) :
    - taux_enfants_par_logement=0.35 : ratio moyen enfants 0-11 ans / logement
      sur Rennes Métropole (source : ratio effectifs scolaires / nb logements communes)
    - surface_factor : un T4+ (>80m²) accueille statistiquement plus d'enfants
    - pieces_factor : proxy de la taille de ménage

    TODO : calibrer ces constantes via régression sur (surface, pièces) → effectifs
    en utilisant les données DVF + effectifs scolaires historiques.
    """
    surface_factor = min(surface_m2 / 80.0, 2.0) if surface_m2 > 0 else 1.0
    pieces_factor = min(nb_pieces / 4.0, 1.5) if nb_pieces > 0 else 1.0
    return nb_logements * taux_enfants_par_logement * surface_factor * pieces_factor


def predict_commune(code_insee: str) -> dict:
    """Prédit les effectifs pour une commune.

    Lit les features requises depuis le metadata JSON de chaque modèle — s'adapte
    automatiquement à use_engineering=True/False et use_lags=True/False.
    """
    base_features = _get_commune_features(code_insee)

    # Pré-charger les lags une seule fois si au moins un modèle en a besoin
    lag_features: dict = {}
    for target in [TARGET_MATERNELLE, TARGET_ELEMENTAIRE, TARGET_CLASSES]:
        mf = _load_model_features(target)
        if any("_lag" in f or "_rolling" in f or "_delta" in f for f in mf):
            lag_features = _get_lag_features(code_insee)
            break

    all_available = {**base_features, **lag_features}

    predictions = {}
    features_used: dict = {}

    for target in [TARGET_MATERNELLE, TARGET_ELEMENTAIRE, TARGET_CLASSES]:
        model = _load_model(target)
        model_features = _load_model_features(target)
        X = np.array([[float(all_available.get(f, 0.0)) for f in model_features]])
        predictions[target] = float(model.predict(X)[0])
        if target == TARGET_ELEMENTAIRE:
            features_used = {f: all_available.get(f, 0.0) for f in model_features}

    return {
        "code_insee": code_insee,
        "nom_commune": base_features["nom_commune"],
        "predictions": {
            "nb_eleves_maternelle": max(0, round(predictions[TARGET_MATERNELLE], 1)),
            "nb_eleves_elementaire": max(0, round(predictions[TARGET_ELEMENTAIRE], 1)),
            "nb_classes_estimees": max(0, round(predictions[TARGET_CLASSES], 1)),
            "nb_eleves_total": max(0, round(
                predictions[TARGET_MATERNELLE] + predictions[TARGET_ELEMENTAIRE], 1
            )),
        },
        "features_utilisees": features_used,
    }


def predict_logement(
    code_insee: str,
    surface_m2: float,
    nb_pieces: int,
    nb_logements: int = 1,
) -> dict:
    base = predict_commune(code_insee)
    enfants_estimes = _children_from_housing(nb_logements, surface_m2, nb_pieces)
    ratio_maternelle = 0.45
    return {
        **base,
        "logement": {
            "surface_m2": surface_m2,
            "nb_pieces": nb_pieces,
            "nb_logements": nb_logements,
        },
        "impact_logement": {
            "enfants_estimes": round(enfants_estimes, 2),
            "maternelle_estimee": round(enfants_estimes * ratio_maternelle, 2),
            "elementaire_estimee": round(enfants_estimes * (1 - ratio_maternelle), 2),
            "classes_supplementaires": round(enfants_estimes / 25, 2),
        },
    }


def predict_batch_csv(df: pd.DataFrame) -> pd.DataFrame:
    required = {"code_insee", "surface_m2", "nb_pieces"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")
    df = df.copy()
    df["code_insee"] = df["code_insee"].astype(str).str.strip()
    rows = []
    for _, row in df.iterrows():
        nb_log = int(row.get("nb_logements", 1))
        result = predict_logement(
            str(row["code_insee"]),
            float(row["surface_m2"]),
            int(row["nb_pieces"]),
            nb_log,
        )
        rows.append({
            "code_insee": result["code_insee"],
            "nom_commune": result["nom_commune"],
            "surface_m2": row["surface_m2"],
            "nb_pieces": row["nb_pieces"],
            "nb_logements": nb_log,
            **result["impact_logement"],
            "effectif_maternelle_commune": result["predictions"]["nb_eleves_maternelle"],
            "effectif_elementaire_commune": result["predictions"]["nb_eleves_elementaire"],
        })
    return pd.DataFrame(rows)


def get_model_metadata() -> dict:
    meta = {}
    for target in [TARGET_MATERNELLE, TARGET_ELEMENTAIRE, TARGET_CLASSES]:
        path = MODELS_DIR / f"{target}_meta.json"
        if path.exists():
            meta[target] = json.loads(path.read_text(encoding="utf-8"))
    return meta
