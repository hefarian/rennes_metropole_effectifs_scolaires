import io
import os
import sys

import pandas as pd
import requests
import streamlit as st

sys.path.insert(0, "/app/src")
from p13.db import read_sql

st.set_page_config(page_title="Prédictions", page_icon="🔮", layout="wide")
st.title("🔮 Prédictions d'Effectifs Scolaires")

API_URL = os.getenv("API_URL", "http://localhost:8000")

communes = read_sql("SELECT code_insee, nom_commune FROM communes ORDER BY nom_commune")
commune_map = dict(zip(communes["nom_commune"], communes["code_insee"]))

tab_unit, tab_batch, tab_commune = st.tabs(["Logement unitaire", "Batch CSV", "Par commune"])

with tab_unit:
    st.subheader("Impact d'un logement à livrer")
    col1, col2 = st.columns(2)
    with col1:
        nom = st.selectbox("Commune", communes["nom_commune"])
        code = commune_map[nom]
    with col2:
        surface = st.number_input("Surface (m²)", min_value=20.0, max_value=3000.0, value=75.0)
        pieces = st.number_input("Nombre de pièces", min_value=1, max_value=15, value=4)
        nb_log = st.number_input("Nombre de logements", min_value=1, max_value=100, value=1)

    if st.button("Prédire", type="primary"):
        try:
            r = requests.post(
                f"{API_URL}/predictions/logement",
                json={"code_insee": code, "surface_m2": surface,
                      "nb_pieces": pieces, "nb_logements": nb_log},
                timeout=30,
            )
            if r.ok:
                data = r.json()
                st.success(f"Prédiction pour **{data['nom_commune']}** ({code})")
                c1, c2, c3, c4 = st.columns(4)
                impact = data["impact_logement"]
                pred = data["predictions"]
                c1.metric("Enfants estimés (logement)", impact["enfants_estimes"])
                c2.metric("Maternelle (impact)", impact["maternelle_estimee"])
                c3.metric("Élémentaire (impact)", impact["elementaire_estimee"])
                c4.metric("Classes suppl.", impact["classes_supplementaires"])
                st.markdown("#### Effectifs communaux prédits")
                c5, c6, c7 = st.columns(3)
                c5.metric("Maternelle commune", pred["nb_eleves_maternelle"])
                c6.metric("Élémentaire commune", pred["nb_eleves_elementaire"])
                c7.metric("Classes estimées", pred["nb_classes_estimees"])
            else:
                st.error(r.json().get("detail", r.text))
        except Exception as exc:
            st.error(f"Erreur API : {exc}")

with tab_batch:
    st.subheader("Fichier CSV de logements")
    st.markdown(
        "Colonnes requises : `code_insee`, `surface_m2`, `nb_pieces` "
        "(optionnel : `nb_logements`)"
    )
    template = pd.DataFrame([
        {"code_insee": "35238", "surface_m2": 65, "nb_pieces": 3, "nb_logements": 1},
        {"code_insee": "35051", "surface_m2": 90, "nb_pieces": 4, "nb_logements": 2},
    ])
    st.download_button(
        "Télécharger modèle CSV",
        template.to_csv(index=False).encode(),
        "modele_logements.csv",
        "text/csv",
    )
    uploaded = st.file_uploader("Importer CSV", type=["csv"])
    if uploaded and st.button("Lancer batch"):
        try:
            files = {"file": ("logements.csv", uploaded.getvalue(), "text/csv")}
            r = requests.post(f"{API_URL}/predictions/batch", files=files, timeout=60)
            if r.ok:
                st.dataframe(pd.DataFrame(r.json()), use_container_width=True)
            else:
                st.error(r.json().get("detail", r.text))
        except Exception as exc:
            st.error(str(exc))

with tab_commune:
    nom2 = st.selectbox("Commune (effectifs globaux)", communes["nom_commune"], key="c2")
    if st.button("Prédire commune"):
        code2 = commune_map[nom2]
        try:
            r = requests.get(f"{API_URL}/predictions/commune/{code2}", timeout=30)
            if r.ok:
                data = r.json()
                p = data["predictions"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Maternelle", p["nb_eleves_maternelle"])
                c2.metric("Élémentaire", p["nb_eleves_elementaire"])
                c3.metric("Classes", p["nb_classes_estimees"])
            else:
                st.error(r.json().get("detail", r.text))
        except Exception as exc:
            st.error(str(exc))
