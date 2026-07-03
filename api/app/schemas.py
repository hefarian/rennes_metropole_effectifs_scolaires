from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    database: str


class CommuneResponse(BaseModel):
    code_insee: str
    nom_commune: str
    population: int | None = None
    densite_hab_km2: float | None = None


class LogementRequest(BaseModel):
    code_insee: str = Field(..., example="35238", description="Code INSEE de la commune")
    surface_m2: float = Field(..., gt=0, example=75.0)
    nb_pieces: int = Field(..., ge=1, example=4)
    nb_logements: int = Field(1, ge=1, example=1)


class PredictionsBlock(BaseModel):
    nb_eleves_maternelle: float
    nb_eleves_elementaire: float
    nb_classes_estimees: float
    nb_eleves_total: float


class PredictionResponse(BaseModel):
    code_insee: str
    nom_commune: str
    predictions: PredictionsBlock
    features_utilisees: dict[str, float]


class LogementImpact(BaseModel):
    enfants_estimes: float
    maternelle_estimee: float
    elementaire_estimee: float
    classes_supplementaires: float


class LogementPredictionResponse(PredictionResponse):
    logement: dict
    impact_logement: LogementImpact


class TrainResponse(BaseModel):
    status: str
    results: dict
