import os
import sys

import streamlit as st

sys.path.insert(0, "/app/src")

st.set_page_config(
    page_title="P13 — Effectifs Scolaires",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.title("🏫 P13 — Estimation des Effectifs Scolaires")
st.markdown(
    """
    **Plateforme de prédiction des effectifs scolaires** (maternelle & élémentaire)
    pour **Rennes Métropole**.

    Anticipez les besoins en classes et enseignants lors de la livraison de nouveaux logements.

    ---
    ### Navigation
    Utilisez le menu latéral pour accéder aux modules :

    | Page | Description |
    |------|-------------|
    | **EDA** | Analyse exploratoire des données éducatives |
    | **Prédictions** | Estimation unitaire ou batch (CSV) |
    | **ML Training** | Entraînement et métriques des modèles |
    | **Explainability** | Importance des variables (SHAP) |
    | **Monitoring** | Suivi ETL et performances |

    ---
    ### Services Docker
    - **API FastAPI** : [Documentation Swagger](http://localhost:8000/docs)
    - **Jupyter Lab** : http://localhost:8889 (token: `p13-jupyter`)
    - **PostgreSQL** : localhost:5433
    """
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Périmètre", "43 communes", "Rennes Métropole")
with col2:
    st.metric("Niveaux", "Maternelle + Élémentaire")
with col3:
    st.metric("Stack", "Docker + ML")

try:
    import requests
    r = requests.get(f"{API_URL}/health", timeout=3)
    if r.ok:
        st.success(f"✅ API connectée ({API_URL})")
    else:
        st.warning("⚠️ API indisponible")
except Exception:
    st.error(f"❌ API non joignable ({API_URL})")
