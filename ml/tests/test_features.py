import numpy as np
import pandas as pd
import pytest

from ml.features.build_features import add_derived_features, build_preprocessor, prepare_xy


@pytest.fixture
def sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "crop_type": ["Tomato", "Cucumber", "Lettuce"],
        "avg_temperature_C": [24.0, 25.0, 19.0],
        "min_temperature_C": [18.0, 20.0, 15.0],
        "max_temperature_C": [30.0, 31.0, 23.0],
        "humidity_percent": [70.0, 78.0, 65.0],
        "co2_ppm": [800.0, 850.0, 750.0],
        "light_intensity_lux": [25000.0, 30000.0, 20000.0],
        "photoperiod_hours": [14.0, 14.0, 12.0],
        "irrigation_mm": [5.0, 6.0, 4.0],
        "fertilizer_N_kg_ha": [120.0, 130.0, 100.0],
        "fertilizer_P_kg_ha": [60.0, 70.0, 50.0],
        "fertilizer_K_kg_ha": [80.0, 90.0, 70.0],
        "pest_severity": [2.0, 1.0, 3.0],
        "soil_pH": [6.5, 6.4, 6.6],
        "days_to_maturity": [90, 60, 45],
        "yield_kg_per_m2": [5.2, 4.1, 3.0],
    })


def test_derived_features(sample_df):
    out = add_derived_features(sample_df)
    assert "temp_range_C" in out.columns
    assert "temp_deviation_C" in out.columns
    assert "light_daily_integral" in out.columns
    assert "nutrient_total_kg_ha" in out.columns
    assert out["temp_range_C"].iloc[0] == 12.0
    assert out["nutrient_total_kg_ha"].iloc[0] == 260.0


def test_prepare_xy(sample_df):
    X, y = prepare_xy(sample_df)
    assert "yield_kg_per_m2" not in X.columns
    assert len(X) == len(y) == 3
    assert y.dtype == float


def test_preprocessor_fit_transform(sample_df):
    X, _ = prepare_xy(sample_df)
    pre = build_preprocessor()
    X_t = pre.fit_transform(X)
    assert X_t.shape[0] == 3
    assert X_t.shape[1] > 0
    # No NaN in the transformed output
    assert not np.isnan(X_t).any()