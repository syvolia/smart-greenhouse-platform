"""Feature configuration: which columns are numeric, categorical, or target.

Changing anything here requires retraining the model. Keep it in sync with
the API request schema (backend/app/schemas/ml.py).
"""
from typing import Final
import os

RANDOM_SEED: Final[int] = 42

TARGET: Final[str] = "yield_kg_per_m2"

NUMERIC_FEATURES: Final[list[str]] = [
    "avg_temperature_C",
    "min_temperature_C",
    "max_temperature_C",
    "humidity_percent",
    "co2_ppm",
    "light_intensity_lux",
    "photoperiod_hours",
    "irrigation_mm",
    "fertilizer_N_kg_ha",
    "fertilizer_P_kg_ha",
    "fertilizer_K_kg_ha",
    "pest_severity",
    "soil_pH",
    "days_to_maturity",
]

CATEGORICAL_FEATURES: Final[list[str]] = [
    "crop_type",
]

# Derived features added by the feature builder.
# Documented here so the API request schema can compute them too.
DERIVED_FEATURES: Final[list[str]] = [
    "temp_range_C",          # max - min
    "temp_deviation_C",      # |avg - 23|, a proxy for temperature stress
    "light_daily_integral",  # light_intensity_lux * photoperiod_hours
    "nutrient_total_kg_ha",  # N + P + K
]

ALL_FEATURES: Final[list[str]] = (
    NUMERIC_FEATURES + CATEGORICAL_FEATURES + DERIVED_FEATURES
)

MODEL_VERSION: Final[str] = "v1"
MODEL_FILENAME: Final[str] = "yield_model_v1.joblib"
METADATA_FILENAME: Final[str] = "yield_model_v1_metadata.json"

MLFLOW_TRACKING_URI: Final[str] = os.environ.get(
    "MLFLOW_TRACKING_URI", "http://localhost:5001"
)
MLFLOW_EXPERIMENT_NAME: Final[str] = "greenhouse-yield-prediction"
MLFLOW_MODEL_NAME: Final[str] = os.environ.get(
    "MLFLOW_MODEL_NAME", "greenhouse-yield-predictor"
)
# Stages the pipeline is aware of. We never auto-transition; a human or CI does.
MLFLOW_STAGES: Final[list[str]] = ["None", "Staging", "Production", "Archived"]