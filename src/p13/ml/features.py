"""Feature engineering pour les modèles ML."""

from __future__ import annotations

FEATURE_COLUMNS = [
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
