import sys

import plotly.express as px
import streamlit as st

sys.path.insert(0, "/app/src")
from p13.db import read_sql

st.set_page_config(page_title="EDA", page_icon="📊", layout="wide")
st.title("📊 Analyse Exploratoire — Données Scolaires")

tab1, tab2, tab3, tab4 = st.tabs([
    "Effectifs par commune", "Évolution temporelle", "Démographie", "Logements & DVF"
])

with tab1:
    df = read_sql("""
        SELECT v.nom_commune, v.rentree, v.nb_eleves_maternelle,
               v.nb_eleves_elementaire, v.nb_classes, v.nb_eleves_total
        FROM v_effectifs_commune_annee v
        ORDER BY v.rentree DESC, v.nb_eleves_total DESC
    """)
    if df.empty:
        st.warning("Aucune donnée. Lancez l'ETL : `docker compose --profile etl run --rm etl`")
    else:
        latest = df["rentree"].max()
        st.subheader(f"Rentée {latest}")
        latest_df = df[df["rentree"] == latest]
        fig = px.bar(
            latest_df.sort_values("nb_eleves_total", ascending=True).tail(20),
            x="nb_eleves_total", y="nom_commune", orientation="h",
            color="nb_eleves_maternelle",
            title="Top communes — effectifs totaux",
            labels={"nb_eleves_total": "Élèves", "nom_commune": "Commune"},
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(latest_df, use_container_width=True)

with tab2:
    evo = read_sql("""
        SELECT rentree,
               SUM(nb_eleves_maternelle) AS maternelle,
               SUM(nb_eleves_elementaire) AS elementaire,
               SUM(nb_classes) AS classes
        FROM v_effectifs_commune_annee
        GROUP BY rentree ORDER BY rentree
    """)
    if not evo.empty:
        fig = px.line(
            evo, x="rentree", y=["maternelle", "elementaire"],
            title="Évolution des effectifs — Rennes Métropole",
            markers=True,
        )
        st.plotly_chart(fig, use_container_width=True)
        ratio = evo.copy()
        ratio["eleves_par_classe"] = (ratio["maternelle"] + ratio["elementaire"]) / ratio["classes"]
        fig2 = px.line(ratio, x="rentree", y="eleves_par_classe",
                       title="Ratio élèves / classes (métropole)", markers=True)
        st.plotly_chart(fig2, use_container_width=True)

with tab3:
    demo = read_sql("""
        SELECT c.nom_commune, c.population, s.natalite_2022, s.cat_0_14_2020,
               s.densite_2021, s.pop_proj_2030
        FROM communes c
        JOIN stats_communes s ON s.code_insee = c.code_insee
        ORDER BY c.population DESC
    """)
    if not demo.empty:
        fig = px.scatter(
            demo, x="population", y="cat_0_14_2020", size="densite_2021",
            hover_name="nom_commune", title="Population vs part 0-14 ans (2020)",
            labels={"cat_0_14_2020": "% 0-14 ans", "population": "Population"},
        )
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    col_a, col_b = st.columns(2)
    with col_a:
        permis = read_sql("""
            SELECT commune, SUM(logements_crees) AS logements
            FROM permis_construire GROUP BY commune ORDER BY logements DESC LIMIT 15
        """)
        if not permis.empty:
            st.plotly_chart(
                px.bar(permis, x="logements", y="commune", orientation="h",
                       title="Permis de construire — logements créés"),
                use_container_width=True,
            )
    with col_b:
        dvf = read_sql("""
            SELECT nom_commune, COUNT(*) AS mutations, AVG(prix_bati_m2) AS prix_m2
            FROM mutations_dvf GROUP BY nom_commune ORDER BY mutations DESC LIMIT 15
        """)
        if not dvf.empty:
            st.plotly_chart(
                px.bar(dvf, x="mutations", y="nom_commune", orientation="h",
                       title="Mutations DVF par commune"),
                use_container_width=True,
            )
