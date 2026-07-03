import json
import os
import sys

import requests
import streamlit as st

sys.path.insert(0, "/app/src")

st.set_page_config(page_title="ML Training", page_icon="🤖", layout="wide")
st.title("🤖 Entraînement & Métriques ML")

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.markdown("""
Modèles comparés : **Régression linéaire**, **Ridge**, **Random Forest**, **Gradient Boosting**.

Métriques : RMSE, MAE, R², MAPE — tracking via **MLflow**.
""")

if st.button("🚀 Lancer l'entraînement", type="primary"):
    with st.spinner("Entraînement en cours..."):
        try:
            r = requests.post(f"{API_URL}/ml/train", timeout=300)
            if r.ok:
                st.success("Entraînement terminé !")
                st.json(r.json()["results"])
            else:
                st.error(r.json().get("detail", r.text))
        except Exception as exc:
            st.error(str(exc))

st.divider()
st.subheader("Modèles actuels")

try:
    r = requests.get(f"{API_URL}/ml/models", timeout=10)
    if r.ok:
        models = r.json()
        for target, meta in models.items():
            with st.expander(f"🎯 {target} — {meta.get('model', 'N/A')}"):
                st.write(f"Entraîné le : {meta.get('trained_at', '—')}")
                st.write(f"Échantillons : {meta.get('n_samples', '—')}")
                metrics = meta.get("metrics", {})
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("R²", f"{metrics.get('r2', 0):.3f}")
                c2.metric("RMSE", f"{metrics.get('rmse', 0):.1f}")
                c3.metric("MAE", f"{metrics.get('mae', 0):.1f}")
                c4.metric("MAPE", f"{metrics.get('mape', 0):.1f}%")
                st.write("Features :", meta.get("features", []))
    else:
        st.info("Aucun modèle entraîné. Cliquez sur « Lancer l'entraînement ».")
except Exception as exc:
    st.warning(f"API indisponible : {exc}")
