from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from app.config import APP_VERSION
from app.schemas.prediction import PredictionInput, PredictionResponse
from app.services.ml_service import ml_service

router = APIRouter(prefix="/api")


@router.api_route("/health", methods=["GET", "HEAD"])
async def health_check() -> dict:
    model_loaded = ml_service.is_ready()
    return {
        "status": "healthy" if model_loaded else "degraded",
        "application": "VoltCast",
        "version": APP_VERSION,
        "model_loaded": model_loaded,
        "prediction_ready": model_loaded,
    }


@router.get("/model-info")
async def model_info() -> dict:
    return ml_service.get_model_info()


@router.get("/metrics")
async def metrics() -> dict:
    return ml_service.get_metrics()


@router.post("/predict", response_model=PredictionResponse)
async def predict(payload: PredictionInput) -> PredictionResponse:
    if not ml_service.is_ready():
        raise HTTPException(status_code=503, detail="Prediction model is not ready.")

    result = ml_service.predict(payload)
    return PredictionResponse(
        predicted_consumption=result["predicted_consumption"],
        unit=result["unit"],
        status=result["status"],
        model_name=result["model_name"],
        timestamp=result["timestamp"],
        metadata=result["metadata"],
    )
