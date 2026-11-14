from __future__ import annotations

from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class PredictionInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid", allow_inf_nan=False)

    timestamp: datetime = Field(..., description="Prediction timestamp in ISO 8601 format.")
    temperature: float = Field(..., ge=0, le=45, description="Temperature in °C.")
    humidity: float = Field(..., ge=0, le=100, description="Relative humidity in %.")
    windspeed: float = Field(..., ge=0, le=10, description="Wind speed in m/s.")
    general_diffuse_flows: float = Field(
        ...,
        ge=0,
        le=1200,
        description="General diffuse flow in W/m².",
        validation_alias=AliasChoices(
            "general_diffuse_flows",
            "generalDiffuseFlows",
            "generaldiffuseflows",
        ),
    )
    diffuse_flows: float = Field(
        ...,
        ge=0,
        le=1000,
        description="Diffuse flow in W/m².",
        validation_alias=AliasChoices("diffuse_flows", "diffuseFlows", "diffuseflows"),
    )


class PredictionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    predicted_consumption: float
    unit: str = "kW"
    status: str = "success"
    model_name: str
    timestamp: str
    metadata: dict
