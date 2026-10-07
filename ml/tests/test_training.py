import numpy as np
import pandas as pd
import pytest

from ml.training.evaluate import evaluate_model
from ml.training.models import build_models


@pytest.fixture
def tiny_dataset():
    rng = np.random.default_rng(42)
    n = 200
    return pd.DataFrame({
        "crop_type": rng.choice(["Tomato", "Cucumber", "Lettuce"], size=n),
        "avg_temperature_C": rng.normal(23.0, 3.0, n),
        "min_temperature_C": rng.normal(18.0, 2.0, n),
        "max_temperature_C": rng.normal(28.0, 2.0, n),
        "humidity_percent": rng.normal(70.0, 8.0, n),
        "co2_ppm": rng.normal(800.0, 100.0, n),
        "light_intensity_lux": rng.normal(25000.0, 5000.0, n),
        "photoperiod_hours": rng.normal(14.0, 1.0, n),
        "irrigation_mm": rng.normal(5.0, 1.5, n),
        "fertilizer_N_kg_ha": rng.normal(120.0, 30.0, n),
        "fertilizer_P_kg_ha": rng.normal(60.0, 15.0, n),
        "fertilizer_K_kg_ha": rng.normal(80.0, 20.0, n),
        "pest_severity": rng.uniform(0.0, 5.0, n),
        "soil_pH": rng.normal(6.5, 0.3, n),
        "days_to_maturity": rng.integers(45, 120, n),
        "yield_kg_per_m2": rng.normal(4.0, 0.8, n),
    })


def test_evaluate_model_returns_metrics():
    y_true = np.array([1.0, 2.0, 3.0, 4.0])
    y_pred = np.array([1.1, 1.9, 3.1, 3.8])
    m = evaluate_model(y_true, y_pred)
    assert "mae" in m and "rmse" in m and "r2" in m and "mape" in m
    assert m["mae"] > 0
    assert m["r2"] > 0.9


def test_build_models_returns_expected_names():
    models = build_models()
    assert "linear_regression" in models
    assert "random_forest" in models
    assert "gradient_boosting" in models
    # xgboost is optional but should be present when installed
    if "xgboost" in models:
        assert hasattr(models["xgboost"], "fit")


def test_models_can_fit_and_predict(tiny_dataset):
    from ml.features.build_features import build_preprocessor, prepare_xy
    from ml.training.models import build_models

    X, y = prepare_xy(tiny_dataset)
    pre = build_preprocessor()
    X_t = pre.fit_transform(X)
    for name, model in build_models().items():
        model.fit(X_t, y)
        preds = model.predict(X_t)
        assert len(preds) == len(y)