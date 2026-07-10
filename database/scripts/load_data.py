"""Chargement des données CSV vers PostgreSQL."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from p13.config import (  # noqa: E402
    COMMUNE_NOM_TO_INSEE,
    COMMUNES_INSEE,
    DATA_DIR,
    PERMIS_COMMUNE_TO_INSEE,
)
from p13.db import get_engine, log_etl_run, truncate_table  # noqa: E402


def _normalize_commune(name: str) -> str:
    return str(name).strip().upper()


def _commune_to_insee(name: str) -> str | None:
    return COMMUNE_NOM_TO_INSEE.get(_normalize_commune(name))


def _safe_int(val) -> int | None:
    if pd.isna(val) or val == "":
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


def _safe_float(val) -> float | None:
    if pd.isna(val) or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _to_db(df: pd.DataFrame, table: str, if_exists: str = "append") -> int:
    engine = get_engine()
    n = len(df)
    df.to_sql(table, engine, if_exists=if_exists, index=False, method="multi", chunksize=500)
    return n


def load_communes() -> None:
    path = DATA_DIR / "communes_rennes_metropole.csv"
    df = pd.read_csv(path, sep=";")
    out = pd.DataFrame({
        "code_insee": df["code_insee"].astype(str).str.zfill(5),
        "nom_commune": df["nom_commune"],
        "code_departement": df["code_departement"].astype(str),
        "departement": df["departement"],
        "region": df["region"],
        "epci": df["epci"],
        "population": pd.to_numeric(df["population"], errors="coerce"),
        "superficie_km2": pd.to_numeric(df["superficie_km2"], errors="coerce"),
        "densite_hab_km2": pd.to_numeric(df["densite_hab_km2"], errors="coerce"),
    })
    truncate_table("communes")
    n = _to_db(out, "communes")
    log_etl_run("communes", n, "ok")
    print(f"  communes: {n} lignes")


def load_stats_communes() -> None:
    path = DATA_DIR / "donnee_statistique_commune_rennes_metropole.csv"
    df = pd.read_csv(path, sep=";")
    cols = [
        "code_insee", "nom_commune", "Geo Point",
        "pop_1968", "pop_1975", "pop_1982", "pop_1990", "pop_1999", "pop_2009",
        "pop_2014", "pop_2020", "pop_2021", "pop_estim_2023", "pop_proj_2030", "pop_proj_2040",
        "cat_0_14_2020", "cat_15_29_2020", "cat_30_44_2020", "cat_45_59_2020",
        "cat_60_74_2020", "cat_75_plus_2020", "densite_2021", "mortalite_2022", "natalite_2022",
        "cat_15_plus_2020", "emploi_2018", "emploi_2021", "ecole_mat_ele", "college", "lycee",
        "log_collectif", "log_individuel", "plh_nb_log_a_const",
    ]
    available = [c for c in cols if c in df.columns]
    out = df[available].copy()
    out["code_insee"] = out["code_insee"].astype(str).str.zfill(5)
    out = out.rename(columns={"Geo Point": "geo_point"})
    truncate_table("stats_communes")
    n = _to_db(out, "stats_communes")
    log_etl_run("stats_communes", n, "ok")
    print(f"  stats_communes: {n} lignes")


def load_ecoles() -> None:
    path = DATA_DIR / "fr-en-ecoles-effectifs-nb_classes.csv"
    communes_set = set(COMMUNES_INSEE)
    chunks = []
    for chunk in pd.read_csv(path, sep=";", chunksize=100_000, low_memory=False):
        mask = chunk["Code département"].astype(str) == "35"
        filtered = chunk[mask].copy()
        if filtered.empty:
            continue
        filtered["code_insee"] = filtered["Commune"].map(_commune_to_insee)
        filtered = filtered[filtered["code_insee"].isin(communes_set)]
        if not filtered.empty:
            chunks.append(filtered)
    if not chunks:
        log_etl_run("ecoles_effectifs", 0, "warning", "Aucune donnée filtrée")
        return

    df = pd.concat(chunks, ignore_index=True)

    # Dérivation du type d'école depuis la dénomination
    def _type_ecole(denom: str) -> str:
        d = str(denom).upper()
        if "MATERNELLE" in d:
            return "MATERNELLE"
        if "ELEMENTAIRE" in d:
            return "ELEMENTAIRE"
        return "PRIMAIRE"  # école primaire = maternelle + élémentaire

    out = pd.DataFrame({
        "rentree": df["Rentrée scolaire"].astype(int),
        "code_insee": df["code_insee"],
        "nom_commune": df["Commune"],
        "numero_ecole": df["Numéro de l'école"].astype(str),
        "denomination": df["Dénomination principale"].fillna(""),
        "type_ecole": df["Dénomination principale"].apply(_type_ecole),
        "secteur": df["Secteur"],
        "rep": pd.to_numeric(df["REP"], errors="coerce").fillna(0).astype(int),
        "rep_plus": pd.to_numeric(df["REP +"], errors="coerce").fillna(0).astype(int),
        "nb_classes": pd.to_numeric(df["Nombre total de classes"], errors="coerce"),
        "nb_eleves_total": pd.to_numeric(df["Nombre total d'élèves"], errors="coerce"),
        "nb_eleves_maternelle": pd.to_numeric(
            df["Nombre d'élèves en pré-élémentaire hors ULIS"], errors="coerce"
        ),
        "nb_eleves_elementaire": pd.to_numeric(
            df["Nombre d'élèves en élémentaire hors ULIS"], errors="coerce"
        ),
        "nb_eleves_cp": pd.to_numeric(df["Nombre d'élèves en CP hors ULIS"], errors="coerce"),
        "nb_eleves_ce1": pd.to_numeric(df["Nombre d'élèves en CE1 hors ULIS"], errors="coerce"),
        "nb_eleves_ce2": pd.to_numeric(df["Nombre d'élèves en CE2 hors ULIS"], errors="coerce"),
        "nb_eleves_cm1": pd.to_numeric(df["Nombre d'élèves en CM1 hors ULIS"], errors="coerce"),
        "nb_eleves_cm2": pd.to_numeric(df["Nombre d'élèves en CM2 hors ULIS"], errors="coerce"),
    })

    # Validation : toutes les 43 communes doivent être présentes
    missing = communes_set - set(out["code_insee"].unique())
    if missing:
        print(f"  ATTENTION : {len(missing)} communes sans école dans le fichier : {missing}")
    else:
        print("  Validation OK : les 43 communes de Rennes Métropole ont des données.")

    # Répartition maternelle / élémentaire / primaire
    print(f"  Types d'école : {out['type_ecole'].value_counts().to_dict()}")
    print(f"  Écoles REP: {out['rep'].sum()} | REP+: {out['rep_plus'].sum()}")

    truncate_table("ecoles_effectifs")
    n = _to_db(out, "ecoles_effectifs")
    log_etl_run("ecoles_effectifs", n, "ok")
    print(f"  ecoles_effectifs: {n} lignes")


def load_population_2014() -> None:
    path = DATA_DIR / "population-par-sexe-age-et-nationalite-par-commune-2014.csv"
    df = pd.read_csv(path, sep=";")
    df = df[df["code géographique"].astype(str).isin(COMMUNES_INSEE)]
    out = pd.DataFrame({
        "code_insee": df["code géographique"].astype(str),
        "tranche_age": df["âge regroupé (4 classes d'âges)"],
        "nationalite": df["indicateur de nationalité condensé (Français/Étranger)"],
        "sexe": df["sexe"],
        "effectif": pd.to_numeric(df["nb"], errors="coerce"),
    })
    truncate_table("population_2014")
    n = _to_db(out, "population_2014")
    log_etl_run("population_2014", n, "ok")
    print(f"  population_2014: {n} lignes")


def load_mutations_dvf() -> None:
    path = DATA_DIR / "mutation_immobiliere_dvf_rm.csv"
    df = pd.read_csv(path, sep=";", low_memory=False)
    df["code_insee"] = df["nom_commune"].map(_commune_to_insee)
    df = df[df["code_insee"].notna()]
    out = pd.DataFrame({
        "idmutation": pd.to_numeric(df["idmutation"], errors="coerce"),
        "annee": pd.to_numeric(df["annee"], errors="coerce"),
        "date_mutation": pd.to_datetime(df.get("date_mutation", df.get("datemut", None)), errors="coerce"),
        "type_bien": df.get("type_bien", df.get("libtypbien", "")),
        "surface_terrain": pd.to_numeric(df.get("surface_terrain", df.get("sterr", None)), errors="coerce"),
        "surface_batie": pd.to_numeric(df.get("surface_batie", df.get("sbati", None)), errors="coerce"),
        "valeur_fonciere": pd.to_numeric(df.get("valeur_fonciere", df.get("valeurfonc", None)), errors="coerce"),
        "prix_bati_m2": pd.to_numeric(df["prix_bati_m2"], errors="coerce"),
        "nb_maison": pd.to_numeric(df.get("nb_maison", df.get("nblocmai", None)), errors="coerce"),
        "nb_appart": pd.to_numeric(df.get("nb_appart", df.get("nblocapt", None)), errors="coerce"),
        "nom_commune": df["nom_commune"],
        "code_insee": df["code_insee"],
        "periode_construction": df.get("periode_construction", df.get("periodedecst", "")),
    })
    truncate_table("mutations_dvf")
    n = _to_db(out, "mutations_dvf")
    log_etl_run("mutations_dvf", n, "ok")
    print(f"  mutations_dvf: {n} lignes")


def load_permis_construire() -> None:
    path = DATA_DIR / "permis_de_contruire_ global_rennes_metropole_historique.csv"
    df = pd.read_csv(path, sep="|")
    df["code_insee"] = df["Commune"].str.lower().map(PERMIS_COMMUNE_TO_INSEE)
    out = pd.DataFrame({
        "commune": df["Commune"],
        "code_insee": df["code_insee"],
        "date_autorisation": pd.to_datetime(df["Date d'autorisation"], format="%d/%m/%Y", errors="coerce"),
        "etat_projet": df["État du projet"],
        "superficie_terrain": df["Superficie du terrain"].astype(str),
        "logements_crees": pd.to_numeric(df["Logements créés (total)"], errors="coerce").fillna(0).astype(int),
        "logements_collectifs": pd.to_numeric(df["dont collectifs"], errors="coerce").fillna(0).astype(int),
        "logements_1p": pd.to_numeric(df["Logements 1 pièce"], errors="coerce").fillna(0).astype(int),
        "logements_2p": pd.to_numeric(df["Logements 2 pièces"], errors="coerce").fillna(0).astype(int),
        "logements_3p": pd.to_numeric(df["Logements 3 pièces"], errors="coerce").fillna(0).astype(int),
        "logements_4p": pd.to_numeric(df["Logements 4 pièces"], errors="coerce").fillna(0).astype(int),
        "logements_5p": pd.to_numeric(df["Logements 5 pièces"], errors="coerce").fillna(0).astype(int),
        "surface_habitable": df["Surface habitable créée"].astype(str),
        "type_habitation": df["Type d'habitation"],
    })
    truncate_table("permis_construire")
    n = _to_db(out, "permis_construire")
    log_etl_run("permis_construire", n, "ok")
    print(f"  permis_construire: {n} lignes")


def load_logements_parcelle() -> None:
    path = DATA_DIR / "nombre-et-type-de-logement-a-la-parcelle-cadastrale-sur-le-territoire-de-rennes-.csv"
    df = pd.read_csv(path, sep=";", usecols=["parcelle", "nb_logement", "type_logement"])
    out = df.rename(columns={
        "parcelle": "parcelle",
        "nb_logement": "nb_logement",
        "type_logement": "type_logement",
    })
    truncate_table("logements_parcelle")
    n = _to_db(out, "logements_parcelle")
    log_etl_run("logements_parcelle", n, "ok")
    print(f"  logements_parcelle: {n} lignes")


def load_referentiel_batiment() -> None:
    path = DATA_DIR / "referentiel-batiment-et-ses-donnees-descriptives-sur-rennes-metropole.csv"
    usecols = [
        "id_bati3d", "parcelle", "jannat", "niveau", "nb_logement", "nb_maison",
        "nb_appart", "surf_locaux_hab", "nb_occ_theorique", "nb_piece",
    ]
    df = pd.read_csv(path, sep=";", usecols=usecols, low_memory=False)
    truncate_table("referentiel_batiment")
    n = _to_db(df, "referentiel_batiment")
    log_etl_run("referentiel_batiment", n, "ok")
    print(f"  referentiel_batiment: {n} lignes")


def build_ml_dataset() -> None:
    engine = get_engine()
    query = """
    WITH effectifs AS (
        SELECT rentree, code_insee,
               SUM(nb_eleves_maternelle) AS nb_eleves_maternelle,
               SUM(nb_eleves_elementaire) AS nb_eleves_elementaire,
               SUM(nb_classes) AS nb_classes
        FROM ecoles_effectifs
        GROUP BY rentree, code_insee
    ),
    dvf AS (
        -- nb_mutations sur les 3 années précédant la rentrée scolaire
        -- (date_mutation est NULL dans la source, on utilise annee)
        SELECT d.code_insee, e2.rentree, COUNT(*) AS nb_mutations
        FROM mutations_dvf d
        JOIN (SELECT DISTINCT rentree, code_insee FROM ecoles_effectifs) e2
          ON e2.code_insee = d.code_insee
         AND d.annee BETWEEN e2.rentree - 3 AND e2.rentree - 1
        GROUP BY d.code_insee, e2.rentree
    ),
    parcelles AS (
        SELECT COUNT(*) AS nb_logements_parcelle FROM logements_parcelle
    ),
    batiments AS (
        SELECT COUNT(*) AS nb_batiments FROM referentiel_batiment
    ),
    permis AS (
        SELECT code_insee, SUM(COALESCE(logements_crees, 0)) AS nb_permis_logements
        FROM permis_construire
        WHERE code_insee IS NOT NULL
        GROUP BY code_insee
    )
    SELECT
        e.code_insee,
        e.rentree,
        e.nb_eleves_maternelle,
        e.nb_eleves_elementaire,
        e.nb_classes,
        c.population,
        s.cat_0_14_2020 AS pop_0_14_pct,
        s.natalite_2022 AS natalite,
        s.densite_2021 AS densite,
        s.log_collectif,
        s.log_individuel,
        s.plh_nb_log_a_const AS plh_logements,
        COALESCE(d.nb_mutations, 0) AS nb_mutations,
        (SELECT nb_logements_parcelle FROM parcelles) AS nb_logements_parcelle,
        (SELECT nb_batiments FROM batiments) AS nb_batiments,
        COALESCE(p.nb_permis_logements, 0) AS nb_permis_logements
    FROM effectifs e
    JOIN communes c ON c.code_insee = e.code_insee
    LEFT JOIN stats_communes s ON s.code_insee = e.code_insee
    LEFT JOIN dvf d ON d.code_insee = e.code_insee AND d.rentree = e.rentree
    LEFT JOIN permis p ON p.code_insee = e.code_insee
    """
    df = pd.read_sql(text(query), engine)
    truncate_table("ml_dataset_commune")
    n = _to_db(df, "ml_dataset_commune")
    log_etl_run("ml_dataset_commune", n, "ok")
    print(f"  ml_dataset_commune: {n} lignes")


def run_all() -> None:
    print(f"ETL P13 — {datetime.now().isoformat()}")
    print(f"DATA_DIR: {DATA_DIR}")
    loaders = [
        load_communes,
        load_stats_communes,
        load_ecoles,
        load_population_2014,
        load_mutations_dvf,
        load_permis_construire,
        load_logements_parcelle,
        load_referentiel_batiment,
        build_ml_dataset,
    ]
    for loader in loaders:
        try:
            loader()
        except Exception as exc:
            log_etl_run(loader.__name__, 0, "error", str(exc))
            print(f"  ERREUR {loader.__name__}: {exc}", file=sys.stderr)
            raise
    print("ETL terminé avec succès.")


if __name__ == "__main__":
    run_all()
