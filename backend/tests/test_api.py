from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient

from app.api import routes
from app.main import app
from app.services.ml_service import MLService

client = TestClient(app)


def test_root_endpoint() -> None:
    response = client.get("/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["application"] == "VoltCast"


def test_health_endpoint() -> None:
    response = client.get("/api/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["application"] == "VoltCast"
    assert payload["status"] == "degraded"
    assert payload["prediction_ready"] is False
    head = client.head("/api/health")
    assert head.status_code == 200
    assert head.content == b""


def test_model_info_endpoint() -> None:
    response = client.get("/api/model-info")
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_name"] == "Unavailable"
    assert isinstance(payload["feature_columns"], list)
    assert payload["feature_columns"] == []


def test_valid_prediction_endpoint(monkeypatch) -> None:
    class ReadyService:
        @staticmethod
        def is_ready() -> bool:
            return True

        @staticmethod
        def predict(payload):
            return {
                "predicted_consumption": 1234.5,
                "unit": "kW",
                "status": "success",
                "model_name": "Test Model",
                "timestamp": payload.timestamp.isoformat(),
                "metadata": {"feature_columns": []},
            }

    monkeypatch.setattr(routes, "ml_service", ReadyService())
    payload = {
        "timestamp": "2024-01-15T18:30:00",
        "temperature": 20.0,
        "humidity": 60.0,
        "windspeed": 3.5,
        "general_diffuse_flows": 120.0,
        "diffuse_flows": 80.0,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "success"
    assert body["unit"] == "kW"
    assert body["predicted_consumption"] == 1234.5


def test_invalid_prediction_endpoint() -> None:
    payload = {
        "timestamp": "2024-01-15T18:30:00",
        "temperature": 20.0,
        "humidity": 60.0,
        "windspeed": 3.5,
        "general_diffuse_flows": 120.0,
    }
    response = client.post("/api/predict", json=payload)
    assert response.status_code == 422


def test_out_of_dataset_range_prediction_is_rejected() -> None:
    response = client.post(
        "/api/predict",
        json={
            "timestamp": "2024-01-15T18:30:00",
            "temperature": 100,
            "humidity": 60,
            "windspeed": 3.5,
            "general_diffuse_flows": 120,
            "diffuse_flows": 80,
        },
    )
    assert response.status_code == 422


def test_metrics_endpoint() -> None:
    response = client.get("/api/metrics")
    assert response.status_code == 200
    payload = response.json()
    assert payload["model_name"] == "Unavailable"
    assert payload["dataset_summary"]["dataset_loaded"] is False
    assert payload["dataset_summary"]["records_count"] is None


def test_missing_model_reports_degraded_and_rejects_predictions(tmp_path: Path, monkeypatch) -> None:
    unavailable_service = MLService(model_path=tmp_path / "missing-model.joblib")
    monkeypatch.setattr(routes, "ml_service", unavailable_service)

    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "degraded"
    assert health.json()["model_loaded"] is False

    prediction = client.post(
        "/api/predict",
        json={
            "timestamp": "2024-01-15T18:30:00",
            "temperature": 20,
            "humidity": 60,
            "windspeed": 3.5,
            "general_diffuse_flows": 120,
            "diffuse_flows": 80,
        },
    )
    assert prediction.status_code == 503


def test_missing_dataset_is_reported_without_fake_metrics(tmp_path: Path) -> None:
    service = MLService(data_path=tmp_path / "missing-dataset.csv")

    assert service.dataset_summary["dataset_loaded"] is False
    assert "historical_average_zone1_kw" not in service.dataset_summary


def test_cors_allows_local_frontend_origin() -> None:
    response = client.options(
        "/api/predict",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_unexpected_prediction_error_is_sanitized(monkeypatch) -> None:
    class FailingService:
        @staticmethod
        def is_ready() -> bool:
            return True

        @staticmethod
        def predict(_payload):
            raise RuntimeError("internal implementation detail")

    monkeypatch.setattr(routes, "ml_service", FailingService())
    response = TestClient(app, raise_server_exceptions=False).post(
        "/api/predict",
        json={
            "timestamp": "2024-01-15T18:30:00",
            "temperature": 20,
            "humidity": 60,
            "windspeed": 3.5,
            "general_diffuse_flows": 120,
            "diffuse_flows": 80,
        },
    )
    assert response.status_code == 500
    assert response.json() == {"detail": "An unexpected server error occurred."}
