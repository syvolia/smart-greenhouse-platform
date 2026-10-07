"""Tests for the MLflow-aware loader + fallback behavior.

These tests don't require a running MLflow server. They exercise:
  - fallback to local when MLflow is unreachable
  - model_info() returns the expected shape regardless of source
  - predict_yield works via either path
"""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services import ml_service


VALID_PAYLOAD = {
    "crop_type": "Tomato",
    "avg_temperature_C": 24.5,
    "min_temperature_C": 18.0,
    "max_temperature_C": 30.0,
    "humidity_percent": 72.0,
    "co2_ppm": 800.0,
    "light_intensity_lux": 25000.0,
    "photoperiod_hours": 14.0,
    "irrigation_mm": 5.0,
    "fertilizer_N_kg_ha": 120.0,
    "fertilizer_P_kg_ha": 60.0,
    "fertilizer_K_kg_ha": 80.0,
    "pest_severity": 2.0,
    "soil_pH": 6.5,
    "days_to_maturity": 90,
}


@pytest.fixture(autouse=True)
def clear_cache():
    ml_service.reload()
    yield
    ml_service.reload()


def _model_available() -> bool:
    return Path("/app/ml_models/yield_model_v1.joblib").exists()


def test_model_info_shape(client: TestClient):
    if not _model_available():
        pytest.skip("No local model; train first.")
    r = client.get("/ml/model-info")
    assert r.status_code == 200
    body = r.json()
    for key in ("model_version", "model_name", "source", "trained_at",
                "validation_metrics", "test_metrics", "features"):
        assert key in body, f"missing key {key}"
    assert body["source"] in ("mlflow", "local")


def test_predict_works_with_fallback(client: TestClient):
    if not _model_available():
        pytest.skip("No local model; train first.")
    r = client.post("/ml/predict-yield", json=VALID_PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert body["predicted_yield_kg_per_m2"] >= 0.0
    assert body["model_version"]


def test_reload_endpoint(client: TestClient):
    r = client.post("/ml/reload")
    assert r.status_code == 204


def test_local_predictor_matches_direct():
    """The adapter's predict() must produce the same value as the raw pipeline."""
    if not _model_available():
        pytest.skip("No local model.")
    import joblib
    import pandas as pd
    from ml.features.build_features import add_derived_features
    from ml.features.feature_config import ALL_FEATURES
    from app.services.ml_service import _LocalPredictor, _request_to_dataframe
    from app.schemas.ml import YieldPredictionRequest

    pipeline = joblib.load("/app/ml_models/yield_model_v1.joblib")
    predictor = _LocalPredictor(pipeline["preprocessor"], pipeline["model"])

    req = YieldPredictionRequest(**VALID_PAYLOAD)
    df = _request_to_dataframe(req)

    # Adapter path
    via_adapter = float(predictor.predict(df)[0])

    # Direct path
    X = add_derived_features(df.copy())[ALL_FEATURES]
    direct = float(pipeline["model"].predict(pipeline["preprocessor"].transform(X))[0])

    assert abs(via_adapter - direct) < 1e-6