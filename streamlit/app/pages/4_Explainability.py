import sys

import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, "/app/src")
from p13.config import MODELS_DIR
from p13.db import read_sql
from p13.ml.features import FEATURE_COLUMNS

st.set_page_config(page_title="TerriSchool35 — Explainability", page_icon="🔍", layout="wide")
st.title("🔍 TerriSchool35 — Importance des Variables")

st.markdown("""
Interprétation des facteurs influençant les prédictions d'effectifs scolaires sur Rennes Métropole.
Analyse basée sur les corrélations du dataset d'entraînement et les métadonnées modèle.
""")

df = read_sql("SELECT * FROM ml_dataset_commune")
if df.empty:
    st.warning("Dataset ML vide. Lancez l'ETL puis l'entraînement.")
    st.stop()

target = st.selectbox(
    "Variable cible",
    ["nb_eleves_maternelle", "nb_eleves_elementaire", "nb_classes"],
)

corr = df[FEATURE_COLUMNS + [target]].corr()[target].drop(target).sort_values(ascending=True)
fig = px.bar(
    x=corr.values, y=corr.index, orientation="h",
    title=f"Corrélation des features avec {target}",
    labels={"x": "Corrélation de Pearson", "y": "Feature"},
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Interprétation métier")
interpretations = {
    "population": "Taille de la commune — principal driver des effectifs",
    "pop_0_14_pct": "Part des 0-14 ans — proxy de la population scolarisable",
    "natalite": "Dynamique démographique future",
    "densite": "Urbanisation et concentration des ménages",
    "log_collectif": "Parc de logements collectifs",
    "log_individuel": "Parc de logements individuels",
    "plh_logements": "Logements prévus au PLH 2023-2028",
    "nb_mutations": "Activité immobilière récente",
    "nb_permis_logements": "Offre de logements en construction",
}
for feat in corr.abs().sort_values(ascending=False).head(5).index:
    st.markdown(f"- **{feat}** (r={corr[feat]:.2f}) : {interpretations.get(feat, '—')}")

meta_path = MODELS_DIR / f"{target}_meta.json"
if meta_path.exists():
    import json
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    st.subheader(f"Modèle retenu : {meta.get('model')}")
    st.json(meta.get("metrics", {}))

st.info(
    "Pour une analyse SHAP complète (locale/globale), "
    "utilisez le notebook Jupyter `02_ml_shap.ipynb`."
)
