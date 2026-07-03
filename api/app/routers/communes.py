from fastapi import APIRouter, HTTPException

from api.app.schemas import CommuneResponse
from p13.db import read_sql

router = APIRouter()


@router.get("", response_model=list[CommuneResponse])
def list_communes():
    df = read_sql(
        "SELECT code_insee, nom_commune, population, densite_hab_km2 "
        "FROM communes ORDER BY nom_commune"
    )
    return df.to_dict(orient="records")


@router.get("/{code_insee}", response_model=CommuneResponse)
def get_commune(code_insee: str):
    df = read_sql(
        "SELECT code_insee, nom_commune, population, densite_hab_km2 "
        "FROM communes WHERE code_insee = :code",
        {"code": code_insee},
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="Commune introuvable")
    return df.iloc[0].to_dict()


@router.get("/{code_insee}/stats")
def get_commune_stats(code_insee: str):
    df = read_sql(
        "SELECT s.* FROM stats_communes s WHERE s.code_insee = :code",
        {"code": code_insee},
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="Statistiques introuvables")
    return df.iloc[0].to_dict()


@router.get("/{code_insee}/effectifs")
def get_commune_effectifs(code_insee: str):
    df = read_sql(
        """
        SELECT rentree, nb_classes, nb_eleves_total,
               nb_eleves_maternelle, nb_eleves_elementaire
        FROM v_effectifs_commune_annee
        WHERE code_insee = :code
        ORDER BY rentree
        """,
        {"code": code_insee},
    )
    if df.empty:
        raise HTTPException(status_code=404, detail="Effectifs introuvables")
    return df.to_dict(orient="records")
