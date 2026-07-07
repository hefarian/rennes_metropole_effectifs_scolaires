"""Feature engineering avancé : interactions, lag temporel, validation spatiale."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, cross_validate


# ---------------------------------------------------------------------------
# 1. Features d'interaction et de ratio
# ---------------------------------------------------------------------------

def add_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des features d'interaction, de ratio et de densité sémantique.

    Ces features capturent des relations non-linéaires que les variables brutes
    n'expriment pas individuellement :
    - nb_enfants_0_14 : nombre absolu d'enfants (driver direct des effectifs)
    - taux_croissance_logements : pression démographique relative à la taille
    - densite_natalite : zones denses à fort renouvellement de population
    - pct_collectif : proxy du profil urbain/rural de la commune
    """
    df = df.copy()

    # Nombre absolu d'enfants 0-14 ans (population * part 0-14)
    if "population" in df.columns and "pop_0_14_pct" in df.columns:
        df["nb_enfants_0_14"] = df["population"] * df["pop_0_14_pct"] / 100.0

    # Taux de croissance logements relatif à la population existante
    if "nb_permis_logements" in df.columns and "population" in df.columns:
        df["taux_croissance_logements"] = (
            df["nb_permis_logements"] / (df["population"].clip(lower=1))
        )

    # Interaction densité × natalité (zones denses à fort renouvellement)
    if "densite" in df.columns and "natalite" in df.columns:
        df["densite_natalite"] = df["densite"] * df["natalite"]

    # Part de logements collectifs (proxy urbain)
    if "log_collectif" in df.columns and "log_individuel" in df.columns:
        total = (df["log_collectif"] + df["log_individuel"]).clip(lower=1)
        df["pct_collectif"] = df["log_collectif"] / total

    return df


# ---------------------------------------------------------------------------
# 2. Encodage des variables catégorielles
# ---------------------------------------------------------------------------

def target_encode(
    df: pd.DataFrame,
    cat_col: str,
    target_col: str,
    smoothing: float = 10.0,
    train_mask: pd.Series | None = None,
) -> pd.Series:
    """Target encoding avec lissage bayésien pour variables catégorielles.

    Le lissage évite l'overfitting sur les catégories rares :
        encoded = (n * mean_cat + smoothing * mean_global) / (n + smoothing)

    Args:
        df: DataFrame complet.
        cat_col: Colonne catégorielle (ex: 'code_insee', 'type_zone_plu').
        target_col: Cible à encoder.
        smoothing: Force du lissage (10 = equilibre standard).
        train_mask: Masque booléen pour n'estimer les stats que sur le train.
    Returns:
        Série encodée (même index que df).
    """
    source = df[train_mask] if train_mask is not None else df
    global_mean = source[target_col].mean()
    stats = source.groupby(cat_col)[target_col].agg(["mean", "count"])
    smoothed = (stats["count"] * stats["mean"] + smoothing * global_mean) / (
        stats["count"] + smoothing
    )
    return df[cat_col].map(smoothed).fillna(global_mean)


def encode_commune(
    df: pd.DataFrame,
    target_col: str,
    group_col: str = "code_insee",
    smoothing: float = 10.0,
) -> pd.DataFrame:
    """Encode les communes par target encoding lissé.

    Remplace la variable catégorielle 'code_insee' par une valeur numérique
    représentant la moyenne de la cible pour cette commune (lissée).
    """
    df = df.copy()
    col_name = f"{group_col}_te_{target_col}"
    df[col_name] = target_encode(df, group_col, target_col, smoothing=smoothing)
    return df


# ---------------------------------------------------------------------------
# 3. Features de lag temporel (séries chronologiques)
# ---------------------------------------------------------------------------

def add_lag_features(
    df: pd.DataFrame,
    target_cols: list[str],
    group_col: str = "code_insee",
    time_col: str = "rentree",
    lags: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> pd.DataFrame:
    """Ajoute des features de lag et de moyenne glissante par commune.

    Les features de lag permettent d'introduire la dynamique temporelle :
    - lag1 : effectif de l'année précédente (mémoire à court terme)
    - lag2, lag3 : effectifs N-2 et N-3 (tendance)
    - rolling_mean3 : moyenne glissante sur 3 ans (signal lissé)

    Args:
        df: DataFrame avec colonnes [group_col, time_col] + target_cols.
        target_cols: Colonnes cibles pour lesquelles créer les lags.
        group_col: Colonne de groupement (commune).
        time_col: Colonne temporelle (année de rentrée).
        lags: Liste des décalages temporels (défaut: [1, 2, 3]).
        rolling_windows: Fenêtres pour les moyennes glissantes (défaut: [3]).
    Returns:
        DataFrame enrichi avec les colonnes de lag (NaN pour les premières années).
    """
    if lags is None:
        lags = [1, 2, 3]
    if rolling_windows is None:
        rolling_windows = [3]

    df = df.copy().sort_values([group_col, time_col])

    for target in target_cols:
        if target not in df.columns:
            continue
        grp = df.groupby(group_col)[target]

        # Lags simples
        for lag in lags:
            df[f"{target}_lag{lag}"] = grp.shift(lag)

        # Moyennes glissantes calculées sur les valeurs passées (shift(1) avant rolling)
        for window in rolling_windows:
            df[f"{target}_rolling_mean{window}"] = (
                grp.transform(
                    lambda x, w=window: x.shift(1).rolling(w, min_periods=1).mean()
                )
            )

        # Variation annuelle (tendance)
        df[f"{target}_delta1"] = df[f"{target}_lag1"] - df.groupby(group_col)[target].shift(2)

    return df


def get_lag_feature_names(
    target_cols: list[str],
    lags: list[int] | None = None,
    rolling_windows: list[int] | None = None,
) -> list[str]:
    """Retourne les noms des features de lag générées par add_lag_features()."""
    if lags is None:
        lags = [1, 2, 3]
    if rolling_windows is None:
        rolling_windows = [3]
    names = []
    for target in target_cols:
        for lag in lags:
            names.append(f"{target}_lag{lag}")
        for window in rolling_windows:
            names.append(f"{target}_rolling_mean{window}")
        names.append(f"{target}_delta1")
    return names


# ---------------------------------------------------------------------------
# 4. Validation spatiale par blocs de communes (GroupKFold)
# ---------------------------------------------------------------------------

def spatial_cross_validate(
    model,
    X: np.ndarray | pd.DataFrame,
    y: np.ndarray | pd.Series,
    groups: np.ndarray | pd.Series,
    n_splits: int = 5,
    scoring: str = "r2",
) -> dict:
    """Validation croisée spatiale : entraîne sur N-1 groupes, teste sur 1 groupe.

    Contrairement au KFold aléatoire, cette approche garantit qu'aucune commune
    du test set n'a jamais été vue à l'entraînement. Cela mesure la vraie capacité
    de généralisation du modèle à une nouvelle commune inconnue.

    Args:
        model: Estimateur scikit-learn (non entraîné).
        X: Features.
        y: Cible.
        groups: Identifiant de groupe (code_insee pour chaque ligne).
        n_splits: Nombre de folds (≤ nb de communes uniques).
        scoring: Métrique d'évaluation.
    Returns:
        dict avec scores train/test, moyenne, écart-type, gap d'overfitting.
    """
    n_groups = len(np.unique(groups))
    n_splits = min(n_splits, n_groups)

    cv = GroupKFold(n_splits=n_splits)
    results = cross_validate(
        model,
        X,
        y,
        cv=cv,
        groups=groups,
        scoring=scoring,
        return_train_score=True,
    )
    return {
        "test_scores": results["test_score"].tolist(),
        "train_scores": results["train_score"].tolist(),
        "mean_test": float(results["test_score"].mean()),
        "std_test": float(results["test_score"].std()),
        "mean_train": float(results["train_score"].mean()),
        "overfit_gap": float(
            results["train_score"].mean() - results["test_score"].mean()
        ),
        "n_splits": n_splits,
    }


def spatial_train_test_split(
    df: pd.DataFrame,
    group_col: str = "code_insee",
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split train/test basé sur des communes entières (pas des lignes individuelles).

    Évite la fuite de données : si une commune apparaît dans plusieurs années,
    toutes ses années seront dans le même split.

    Args:
        df: DataFrame avec la colonne group_col.
        group_col: Colonne de groupement.
        test_size: Fraction des communes pour le test.
        random_state: Graine aléatoire.
    Returns:
        (df_train, df_test)
    """
    rng = np.random.default_rng(random_state)
    communes = df[group_col].unique()
    n_test = max(1, int(len(communes) * test_size))
    test_communes = rng.choice(communes, size=n_test, replace=False)
    mask = df[group_col].isin(test_communes)
    return df[~mask].copy(), df[mask].copy()
