from __future__ import annotations

import math
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.config import DATA_PATH, MODEL_PATH

logger = logging.getLogger(__name__)


class MLService:
    def __init__(self, model_path: str | Path | None = None, data_path: str | Path | None = None) -> None:
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.data_path = Path(data_path) if data_path else DATA_PATH
        self.model = None
        self.model_name = "Unknown"
        self.feature_columns: list[str] = []
        self.scaler = None
        self.metrics: dict[str, Any] = {}
        self.dataset_summary: dict[str, Any] = {}
        self.load_error: str | None = None
        self._load_model()

    def _load_model(self) -> None:
        try:
            package = joblib.load(self.model_path)
            self.model = package.get("model")
            self.model_name = str(package.get("model_name", "Linear Regression"))
            self.feature_columns = list(package.get("feature_columns", []))
            self.scaler = package.get("scaler")
            self.metrics = package.get("metrics", {})
            if self.model is None or self.scaler is None or not self.feature_columns:
                raise ValueError("Model artifact is missing required model, scaler, or feature data.")
        except Exception as exc:
            self.model = None
            self.model_name = "Unavailable"
            self.feature_columns = []
            self.scaler = None
            self.metrics = {}
            self.load_error = str(exc)
            logger.exception("Could not load model artifact at %s", self.model_path)
        self.dataset_summary = self._load_dataset_summary()

    def _load_dataset_summary(self) -> dict[str, Any]:
        try:
            df = pd.read_csv(self.data_path)
            required_columns = {"Datetime", "PowerConsumption_Zone1", "Temperature"}
            missing_columns = required_columns.difference(df.columns)
            if missing_columns:
                raise ValueError(f"Dataset is missing required columns: {sorted(missing_columns)}")

            df["Datetime"] = pd.to_datetime(df["Datetime"], errors="coerce")
            zone_1 = pd.to_numeric(df["PowerConsumption_Zone1"], errors="coerce")
            valid_zone_1 = zone_1.dropna()
            if valid_zone_1.empty:
                raise ValueError("Dataset has no valid Zone 1 consumption values.")

            history = df[["Datetime", "PowerConsumption_Zone1", "Temperature"]].copy()
            history = history.dropna().tail(24).reset_index(drop=True)
            summary = {
                "dataset_loaded": True,
                "dataset_name": "Tetouan City Power Consumption Dataset",
                "records_count": int(len(df)),
                "zone_1_unit": "kW",
                "start_datetime": df["Datetime"].min().isoformat() if df["Datetime"].notna().any() else None,
                "end_datetime": df["Datetime"].max().isoformat() if df["Datetime"].notna().any() else None,
                "historical_average_zone1_kw": round(float(valid_zone_1.mean()), 2),
                "historical_min_zone1_kw": round(float(valid_zone_1.min()), 2),
                "historical_max_zone1_kw": round(float(valid_zone_1.max()), 2),
                "historical_sample": [
                    {
                        "timestamp": row["Datetime"].isoformat(),
                        "power_consumption_zone1_kw": round(float(row["PowerConsumption_Zone1"]), 2),
                        "temperature_c": round(float(row["Temperature"]), 2),
                    }
                    for _, row in history.iterrows()
                ],
            }
            return summary
        except (OSError, ValueError, KeyError, pd.errors.ParserError) as exc:
            logger.exception("Could not load dataset at %s", self.data_path)
            return {
                "dataset_loaded": False,
                "dataset_name": "Tetouan City Power Consumption Dataset",
                "records_count": None,
                "historical_sample": [],
                "dataset_error": "Dataset unavailable; historical analytics are disabled.",
            }

    def is_ready(self) -> bool:
        return (
            self.load_error is None
            and self.model is not None
            and self.scaler is not None
            and bool(self.feature_columns)
        )

    def _build_feature_row(self, payload: Any) -> pd.DataFrame:
        if not self.is_ready():
            raise HTTPException(status_code=503, detail="Prediction model is not ready.")

        dt: datetime = payload.timestamp
        month = dt.month
        day_of_week = dt.weekday()
        hour = dt.hour
        is_weekend = 1 if day_of_week >= 5 else 0

        feature_values = {
            "temperature": float(payload.temperature),
            "humidity": float(payload.humidity),
            "windspeed": float(payload.windspeed),
            "generaldiffuseflows": float(payload.general_diffuse_flows),
            "diffuseflows": float(payload.diffuse_flows),
            "month": int(month),
            "day_of_week": int(day_of_week),
            "hour": int(hour),
            "is_weekend": int(is_weekend),
            "hour_sin": math.sin(2 * math.pi * hour / 24),
            "hour_cos": math.cos(2 * math.pi * hour / 24),
            "day_sin": math.sin(2 * math.pi * day_of_week / 7),
            "day_cos": math.cos(2 * math.pi * day_of_week / 7),
            "month_sin": math.sin(2 * math.pi * month / 12),
            "month_cos": math.cos(2 * math.pi * month / 12),
            "total_solar_flow": float(payload.general_diffuse_flows) + float(payload.diffuse_flows),
            "temperature_humidity": float(payload.temperature) * float(payload.humidity),
        }

        ordered = {key: feature_values[key] for key in self.feature_columns}
        frame = pd.DataFrame([ordered])

        if hasattr(self.scaler, "feature_names_in_"):
            continuous = [name for name in self.scaler.feature_names_in_ if name in frame.columns]
            if continuous:
                scaled = frame.copy()
                scaled[continuous] = self.scaler.transform(frame[continuous])
                return scaled

        return frame

    def predict(self, payload: Any) -> dict[str, Any]:
        if not self.is_ready():
            raise HTTPException(status_code=503, detail="Prediction model is not ready.")

        feature_frame = self._build_feature_row(payload)
        raw_prediction = self.model.predict(feature_frame)[0]
        predicted_consumption = float(raw_prediction)

        return {
            "predicted_consumption": round(predicted_consumption, 2),
            "unit": "kW",
            "status": "success",
            "model_name": self.model_name,
            "timestamp": payload.timestamp.isoformat(),
            "metadata": {
                "feature_columns": self.feature_columns,
                "dataset_average_zone1_kw": self.dataset_summary.get("historical_average_zone1_kw"),
            },
        }

    def get_model_info(self) -> dict[str, Any]:
        return {
            "application": "VoltCast",
            "model_loaded": self.is_ready(),
            "model_name": self.model_name,
            "feature_columns": self.feature_columns,
            "metrics": self.metrics,
            "dataset": self.dataset_summary,
        }

    def get_metrics(self) -> dict[str, Any]:
        return {
            "application": "VoltCast",
            "model_loaded": self.is_ready(),
            "model_name": self.model_name,
            "metrics": self.metrics,
            "dataset_summary": self.dataset_summary,
        }


ml_service = MLService()
