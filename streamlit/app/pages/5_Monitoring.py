import os
import sys

import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, "/app/src")
from p13.db import read_sql

st.set_page_config(page_title="Monitoring", page_icon="📡", layout="wide")
st.title("📡 Monitoring — ETL & Modèles")

API_URL = os.getenv("API_URL", "http://localhost:8000")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Historique ETL")
    etl = read_sql("SELECT * FROM etl_runs ORDER BY loaded_at DESC LIMIT 20")
    if etl.empty:
        st.info("Aucun chargement ETL enregistré.")
    else:
        st.dataframe(etl, use_container_width=True)
        ok = (etl["status"] == "ok").sum()
        st.metric("Tables chargées OK", f"{ok}/{len(etl)}")

with col2:
    st.subheader("Santé API")
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        if r.ok:
            st.success("API opérationnelle")
            st.json(r.json())
        else:
            st.error("API dégradée")
    except Exception as exc:
        st.error(f"API hors ligne : {exc}")

st.divider()
st.subheader("Comptages tables PostgreSQL")

tables = [
    "communes", "stats_communes", "ecoles_effectifs", "population_2014",
    "mutations_dvf", "permis_construire", "logements_parcelle",
    "referentiel_batiment", "ml_dataset_commune",
]
counts = []
for t in tables:
    try:
        n = read_sql(f"SELECT COUNT(*) AS n FROM {t}").iloc[0]["n"]
        counts.append({"table": t, "lignes": n})
    except Exception:
        counts.append({"table": t, "lignes": "—"})

st.dataframe(pd.DataFrame(counts), use_container_width=True)

st.subheader("Métriques modèles")
try:
    r = requests.get(f"{API_URL}/ml/metrics", timeout=10)
    if r.ok:
        st.json(r.json())
    else:
        st.info("Modèles non encore entraînés.")
except Exception:
    pass
