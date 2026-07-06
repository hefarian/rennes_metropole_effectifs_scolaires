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
