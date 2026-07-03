"""Configuration partagée P13."""

import os
from pathlib import Path

POSTGRES_USER = os.getenv("POSTGRES_USER", "p13_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "p13_password")
POSTGRES_DB = os.getenv("POSTGRES_DB", "p13_scolarite")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}",
)

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", "/app/models"))
MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "file:/app/mlruns")

COMMUNES_INSEE = [
    "35001", "35024", "35032", "35047", "35039", "35022", "35051", "35055",
    "35066", "35076", "35079", "35080", "35081", "35088", "35120", "35131",
    "35058", "35065", "35059", "35139", "35144", "35240", "35351", "35180",
    "35189", "35196", "35204", "35206", "35208", "35210", "35216", "35363",
    "35238", "35245", "35250", "35266", "35275", "35278", "35281", "35315",
    "35334", "35352", "35353",
]

COMMUNE_NOM_TO_INSEE = {
    "ACIGNE": "35001", "ACIGNÉ": "35001",
    "BETTON": "35024",
    "BOURGBARRE": "35032", "BOURGBARRÉ": "35032",
    "BRUZ": "35047",
    "BRECE": "35039", "BRÉCÉ": "35039",
    "BECHEREL": "35022", "BÉCHEREL": "35022",
    "CESSON-SEVIGNE": "35051", "CESSON-SÉVIGNÉ": "35051",
    "CHANTEPIE": "35055",
    "CHARTRES-DE-BRETAGNE": "35066",
    "CHAVAGNE": "35076",
    "CHEVAIGNE": "35079", "CHEVaigné": "35079",
    "CINTRE": "35080", "CINTRÉ": "35080",
    "CLAYES": "35081",
    "CORPS-NUDS": "35088",
    "GEVEZE": "35120", "GÉVEZÉ": "35120",
    "L'HERMITAGE": "35131",
    "LA CHAPELLE-CHAUSSEE": "35058", "LA CHAPELLE-CHAUSÉE": "35058",
    "LA CHAPELLE-THOUARAULT": "35065",
    "LA CHAPELLE-DES-FOUGERETZ": "35059",
    "LAILLE": "35139", "LAillé": "35139",
    "LANGAN": "35144",
    "LE RHEU": "35240",
    "LE VERGER": "35351",
    "MINIAC-SOUS-BECHEREL": "35180",
    "MONTGERMONT": "35189",
    "MORDELLES": "35196",
    "NOUVOITOU": "35204",
    "NOYAL-CHATILLON-SUR-SEICHE": "35206", "NOYAL-CHÂTILLON-SUR-SEICHE": "35206",
    "ORGERES": "35208", "ORGÈRES": "35208",
    "PACE": "35210", "PACÉ": "35210",
    "PARTHENAY-DE-BRETAGNE": "35216",
    "PONT-PEAN": "35363", "PONT-PÉAN": "35363",
    "RENNES": "35238",
    "ROMILLE": "35245",
    "SAINT-ARMEL": "35250",
    "SAINT-ERBLON": "35266",
    "SAINT-GILLES": "35275",
    "SAINT-GREGOIRE": "35278", "SAINT-GRÉGOIRE": "35278",
    "SAINT-JACQUES-DE-LA-LANDE": "35281",
    "SAINT-SULPICE-LA-FORET": "35315", "SAINT-SULPICE-LA-FORÊT": "35315",
    "THORIGNE-FOUILLARD": "35334",
    "VERN-SUR-SEICHE": "35352",
    "VEZIN-LE-COQUET": "35353",
}

PERMIS_COMMUNE_TO_INSEE = {
    "acigne": "35001", "betton": "35024", "bourgbarre": "35032", "bruz": "35047",
    "brece": "35039", "becherel": "35022", "cesson-sevigne": "35051",
    "chantepie": "35055", "chartres-de-bretagne": "35066", "chavagne": "35076",
    "chevaigne": "35079", "cintre": "35080", "clayes": "35081", "corps-nuds": "35088",
    "geveze": "35120", "l'hermitage": "35131", "la chapelle-chaussee": "35058",
    "la chapelle-thouarault": "35065", "la chapelle-des-fougeretz": "35059",
    "laille": "35139", "langan": "35144", "le rheu": "35240", "le verger": "35351",
    "miniac-sous-becherel": "35180", "montgermont": "35189", "mordelles": "35196",
    "nouvoitou": "35204", "noyal-chatillon-sur-seiche": "35206", "orgeres": "35208",
    "pace": "35210", "parthenay-de-bretagne": "35216", "pont-pean": "35363",
    "rennes": "35238", "romille": "35245", "saint-armel": "35250",
    "saint-erblon": "35266", "saint-gilles": "35275", "saint-gregoire": "35278",
    "saint-jacques-de-la-lande": "35281", "saint-sulpice-la-foret": "35315",
    "thorigne-fouillard": "35334", "vern-sur-seiche": "35352", "vezin-le-coquet": "35353",
}
