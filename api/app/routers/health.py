from fastapi import APIRouter

from api.app.schemas import HealthResponse
from p13.db import get_engine

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check():
    db_status = "ok"
    try:
        with get_engine().connect() as conn:
            conn.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_status = "error"
    return HealthResponse(
        status="ok" if db_status == "ok" else "degraded",
        database=db_status,
    )
