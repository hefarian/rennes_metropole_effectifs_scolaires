"""Inférence : prédiction des effectifs scolaires."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from p13.config import MODELS_DIR
from p13.db import read_sql
from p13.ml.features import FEATURE_COLUMNS, TARGET_CLASSES, TARGET_ELEMENTAIRE, TARGET_MATERNELLE


def _load_model(target: str):
    path = MODELS_DIR / f"{target}_best.joblib"
    if not path.exists():
        raise FileNotFoundError(
            f"Modèle '{target}' introuvable. Entraînez d'abord : python -m p13.ml.train"
        )
    return joblib.load(path)


def _get_commune_features(code_insee: str) -> dict:
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
            LEFT JOIN (SELECT code_insee, COUNT(*) AS nb FROM mutations_dvf GROUP BY code_insee) dvf
                ON dvf.code_insee = c.code_insee
            LEFT JOIN (SELECT code_insee, SUM(logements_crees) AS nb FROM permis_construire
                       WHERE code_insee IS NOT NULL GROUP BY code_insee) p
                ON p.code_insee = c.code_insee
            WHERE c.code_insee = :code
            """,
            {"code": code_insee},
        )
    if df.empty:
        raise ValueError(f"Commune inconnue : {code_insee}")
    row = df.iloc[0]
    features = {col: float(row.get(col, 0) or 0) for col in FEATURE_COLUMNS}
    return {"code_insee": code_insee, "nom_commune": row.get("nom_commune", ""), **features}


def _children_from_housing(
    nb_logements: int,
    surface_m2: float,
    nb_pieces: int,
    taux_enfants_par_logement: float = 0.35,
) -> float:
    """Estimation heuristique d'enfants scolarisables liés à un logement."""
    surface_factor = min(surface_m2 / 80.0, 2.0) if surface_m2 > 0 else 1.0
    pieces_factor = min(nb_pieces / 4.0, 1.5) if nb_pieces > 0 else 1.0
    return nb_logements * taux_enfants_par_logement * surface_factor * pieces_factor


def predict_commune(code_insee: str) -> dict:
    features = _get_commune_features(code_insee)
    X = np.array([[features[col] for col in FEATURE_COLUMNS]])

    maternelle = float(_load_model(TARGET_MATERNELLE).predict(X)[0])
    elementaire = float(_load_model(TARGET_ELEMENTAIRE).predict(X)[0])
    classes = float(_load_model(TARGET_CLASSES).predict(X)[0])

    return {
        "code_insee": code_insee,
        "nom_commune": features["nom_commune"],
        "predictions": {
            "nb_eleves_maternelle": max(0, round(maternelle, 1)),
            "nb_eleves_elementaire": max(0, round(elementaire, 1)),
            "nb_classes_estimees": max(0, round(classes, 1)),
            "nb_eleves_total": max(0, round(maternelle + elementaire, 1)),
        },
        "features_utilisees": {k: features[k] for k in FEATURE_COLUMNS},
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
