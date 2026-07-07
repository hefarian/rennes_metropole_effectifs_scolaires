"""Feature engineering pour les modèles ML."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Features retenues après analyse de multicolinéarité (notebook 00_eda)
# ---------------------------------------------------------------------------
# Groupes éliminés (r > 0.87 avec population) :
#   - log_collectif  : r=0.998 avec population → redondant
#   - log_individuel : r=0.951 avec population → redondant
#   - plh_logements  : r=0.978 avec population → redondant
#   - densite        : r=0.931 avec population → redondant
#   - nb_mutations   : r=0.999 avec population → redondant
#
# Features conservées :
#   population        : taille de la commune, driver principal
#   pop_0_14_pct      : part 0-14 ans, indépendante de population
#   natalite          : dynamique démographique future
#   nb_permis_logements : proxy offre neuve (indépendant des stocks)
# ---------------------------------------------------------------------------
FEATURE_COLUMNS = [
    "population",       # taille commune (driver dominant)
    "pop_0_14_pct",     # part 0-14 ans (proxy population scolarisable)
    "natalite",         # dynamique démographique
    "nb_permis_logements",  # logements en construction (signal prospectif)
]

# ---------------------------------------------------------------------------
# Features complètes (pour analyses SHAP et comparaisons dans les notebooks)
# ---------------------------------------------------------------------------
ALL_FEATURE_COLUMNS = [
    "population",
    "pop_0_14_pct",
    "natalite",
    "densite",
    "log_collectif",
    "log_individuel",
    "plh_logements",
    "nb_mutations",
    "nb_permis_logements",
]

TARGET_MATERNELLE = "nb_eleves_maternelle"
TARGET_ELEMENTAIRE = "nb_eleves_elementaire"
TARGET_CLASSES = "nb_classes"

ALL_TARGETS = [TARGET_MATERNELLE, TARGET_ELEMENTAIRE, TARGET_CLASSES]

# ---------------------------------------------------------------------------
# Features d'interaction / ratio (add_interaction_features)
# ---------------------------------------------------------------------------
ENGINEERED_FEATURES = [
    "nb_enfants_0_14",           # population × pop_0_14_pct / 100
    "taux_croissance_logements",  # nb_permis_logements / population
    "densite_natalite",           # densite × natalite
    "pct_collectif",              # log_collectif / (log_collectif + log_individuel)
]

# Features de base + features d'interaction
FEATURE_COLUMNS_ENGINEERED = FEATURE_COLUMNS + ENGINEERED_FEATURES

# ---------------------------------------------------------------------------
# Features de lag temporel (add_lag_features)
# Les noms exacts sont générés dynamiquement par get_lag_feature_names()
# ---------------------------------------------------------------------------
LAG_LAGS = [1, 2, 3]
LAG_WINDOWS = [3]

# Features du modèle temporel complet
FEATURE_COLUMNS_TEMPORAL = FEATURE_COLUMNS_ENGINEERED + [
    # Lags pour chaque cible
    "nb_eleves_maternelle_lag1",
    "nb_eleves_maternelle_lag2",
    "nb_eleves_maternelle_lag3",
    "nb_eleves_maternelle_rolling_mean3",
    "nb_eleves_maternelle_delta1",
    "nb_eleves_elementaire_lag1",
    "nb_eleves_elementaire_lag2",
    "nb_eleves_elementaire_lag3",
    "nb_eleves_elementaire_rolling_mean3",
    "nb_eleves_elementaire_delta1",
    "nb_classes_lag1",
    "nb_classes_lag2",
    "nb_classes_lag3",
    "nb_classes_rolling_mean3",
    "nb_classes_delta1",
]

# Colonne de groupe pour la validation spatiale
SPATIAL_GROUP_COLUMN = "code_insee"
