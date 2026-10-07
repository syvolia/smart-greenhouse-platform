import pytest
from fastapi.testclient import TestClient

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


@pytest.fixture
def model_available() -> bool:
    from pathlib import Path
    return Path("/app/ml_models/yield_model_v1.joblib").exists()


def test_predict_yield_returns_expected_shape(client: TestClient, model_available: bool):
    if not model_available:
        pytest.skip("Model not trained; run `python -m ml.training.train` first.")
    r = client.post("/ml/predict-yield", json=VALID_PAYLOAD)
    assert r.status_code == 200
    body = r.json()
    assert "predicted_yield_kg_per_m2" in body
    assert isinstance(body["predicted_yield_kg_per_m2"], float)
    assert body["predicted_yield_kg_per_m2"] >= 0.0
    assert "model_version" in body
    assert "prediction_timestamp" in body
    assert "key_input_features" in body


def test_predict_yield_rejects_invalid_payload(client: TestClient):
    bad = dict(VALID_PAYLOAD)
    bad["crop_type"] = "Banana"
    r = client.post("/ml/predict-yield", json=bad)
    assert r.status_code == 422


def test_predict_yield_rejects_out_of_range(client: TestClient):
    bad = dict(VALID_PAYLOAD)
    bad["humidity_percent"] = 150.0
    r = client.post("/ml/predict-yield", json=bad)
    assert r.status_code == 422


def test_model_info_endpoint(client: TestClient, model_available: bool):
    if not model_available:
        pytest.skip("Model not trained.")
    r = client.get("/ml/model-info")
    assert r.status_code == 200
    body = r.json()
    assert "model_version" in body
    assert "features" in body
    assert len(body["features"]) > 0