"""API FastAPI — Prédiction des effectifs scolaires."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.app.routers import communes, health, ml, predictions

app = FastAPI(
    title="P13 — Effectifs Scolaires Rennes Métropole",
    description=(
        "API de prédiction des effectifs scolaires (maternelle / élémentaire) "
        "pour anticiper les besoins en classes lors de livraisons de logements."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Santé"])
app.include_router(communes.router, prefix="/communes", tags=["Communes"])
app.include_router(predictions.router, prefix="/predictions", tags=["Prédictions"])
app.include_router(ml.router, prefix="/ml", tags=["Machine Learning"])
