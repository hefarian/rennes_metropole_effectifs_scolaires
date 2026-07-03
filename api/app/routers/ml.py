from fastapi import APIRouter, HTTPException

from api.app.schemas import TrainResponse
from p13.ml.predict import get_model_metadata
from p13.ml.train import train_all

router = APIRouter()


@router.post("/train", response_model=TrainResponse)
def train_models():
    try:
        results = train_all()
        return TrainResponse(status="ok", results=results)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/models")
def list_models():
    meta = get_model_metadata()
    if not meta:
        raise HTTPException(
            status_code=404,
            detail="Aucun modèle entraîné. POST /ml/train pour lancer l'entraînement.",
        )
    return meta


@router.get("/metrics")
def get_metrics():
    meta = get_model_metadata()
    return {
        target: data.get("metrics", {})
        for target, data in meta.items()
    }
