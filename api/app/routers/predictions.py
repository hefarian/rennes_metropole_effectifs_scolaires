import io

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from api.app.schemas import LogementPredictionResponse, LogementRequest, PredictionResponse
from p13.ml.predict import predict_batch_csv, predict_commune, predict_logement

router = APIRouter()


@router.get("/commune/{code_insee}", response_model=PredictionResponse)
def predict_by_commune(code_insee: str):
    try:
        return predict_commune(code_insee)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/logement", response_model=LogementPredictionResponse)
def predict_by_logement(body: LogementRequest):
    try:
        return predict_logement(
            body.code_insee, body.surface_m2, body.nb_pieces, body.nb_logements
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/batch")
async def predict_batch(file: UploadFile = File(...)):
    """Prédiction batch depuis un CSV (code_insee, surface_m2, nb_pieces, [nb_logements])."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Fichier CSV requis")
    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content), sep=None, engine="python")
        df.columns = [c.strip().lower() for c in df.columns]
        df["code_insee"] = df["code_insee"].astype(str).str.strip().str.zfill(5)
        result = predict_batch_csv(df)
        return result.to_dict(orient="records")
    except Exception as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
