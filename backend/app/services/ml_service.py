"""Loads the crop-yield model for prediction.

Precedence:
  1. MLflow Model Registry — models:/<name>/<stage>
  2. Local joblib artifact at /app/ml_models/yield_model_v1.joblib

MLflow-first, local-fallback. If MLflow is down or the requested stage has
no version, we fall back rather than fail the request. A production system
would alert on fallback; here we log a warning.
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import joblib
import pandas as pd

from app.config import settings
from app.schemas.ml import YieldPredictionRequest

logger = logging.getLogger(__name__)

MODEL_DIR = Path("/app/ml_models")
MODEL_PATH = MODEL_DIR / "yield_model_v1.joblib"
METADATA_PATH = MODEL_DIR / "yield_model_v1_metadata.json"

_cache: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# Local predictor (adapter with the same .predict(DataFrame) interface as MLflow)
# ---------------------------------------------------------------------------
class _LocalPredictor:
    def __init__(self, preprocessor, model):
        self.preprocessor = preprocessor
        self.model = model

    def predict(self, df: pd.DataFrame):
        from ml.features.build_features import add_derived_features  # type: ignore
        from ml.features.feature_config import ALL_FEATURES  # type: ignore

        df2 = add_derived_features(df.copy())
        X = df2[ALL_FEATURES]
        return self.model.predict(self.preprocessor.transform(X))


# ---------------------------------------------------------------------------
# MLflow loading
# ---------------------------------------------------------------------------
def _try_load_from_mlflow() -> bool:
    uri = getattr(settings, "mlflow_tracking_uri", None)
    model_name = getattr(settings, "mlflow_model_name", None)
    stage = getattr(settings, "mlflow_model_stage", None)
    if not (uri and model_name and stage):
        return False

    try:
        import mlflow
        from mlflow.tracking import MlflowClient

        mlflow.set_tracking_uri(uri)
        model_uri = f"models:/{model_name}/{stage}"
        loaded = mlflow.pyfunc.load_model(model_uri)

        # Pull version metadata
        client = MlflowClient()
        versions = client.get_latest_versions(model_name, stages=[stage])
        if not versions:
            return False
        version = versions[0]
        run = client.get_run(version.run_id)

        metadata = {
            "model_version": version.version,
            "model_name": model_name,
            "source": "mlflow",
            "stage": stage,
            "run_id": version.run_id,
            "trained_at": run.data.tags.get(
                "trained_at", str(run.info.start_time)
            ),
            "validation_metrics": {
                k.removeprefix("val_"): v
                for k, v in run.data.metrics.items()
                if k.startswith("val_")
            },
            "test_metrics": {},
            "features": list(ALL_FEATURE_NAMES),
        }

        _cache["model"] = loaded
        _cache["metadata"] = metadata
        _cache["source"] = "mlflow"
        logger.info(
            "Loaded MLflow model %s version %s (stage=%s, run=%s)",
            model_name, version.version, stage, version.run_id,
        )
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("MLflow model load failed (%s); will fall back to local", exc)
        return False


def _try_load_from_local() -> bool:
    if not MODEL_PATH.exists():
        return False
    pipeline = joblib.load(MODEL_PATH)
    metadata: dict[str, Any] = {}
    if METADATA_PATH.exists():
        with open(METADATA_PATH) as f:
            metadata = json.load(f)

    predictor = _LocalPredictor(pipeline["preprocessor"], pipeline["model"])
    _cache["model"] = predictor
    _cache["metadata"] = {
        **metadata,
        "source": "local",
        "model_name": metadata.get("model_name", pipeline.get("model_name", "unknown")),
    }
    _cache["source"] = "local"
    logger.info("Loaded local model from %s", MODEL_PATH)
    return True


def _load_artifacts() -> dict[str, Any]:
    if "source" in _cache:
        return _cache

    if _try_load_from_mlflow():
        return _cache

    if _try_load_from_local():
        return _cache

    raise FileNotFoundError(
        f"No model available. MLflow at {getattr(settings, 'mlflow_tracking_uri', '?')} "
        f"has no {getattr(settings, 'mlflow_model_stage', '?')} version, and no local "
        f"artifact found at {MODEL_PATH}. Run `python -m ml.training.train`."
    )


def _request_to_dataframe(req: YieldPredictionRequest) -> pd.DataFrame:
    return pd.DataFrame([{
        "crop_type": req.crop_type,
        "avg_temperature_C": req.avg_temperature_C,
        "min_temperature_C": req.min_temperature_C,
        "max_temperature_C": req.max_temperature_C,
        "humidity_percent": req.humidity_percent,
        "co2_ppm": req.co2_ppm,
        "light_intensity_lux": req.light_intensity_lux,
        "photoperiod_hours": req.photoperiod_hours,
        "irrigation_mm": req.irrigation_mm,
        "fertilizer_N_kg_ha": req.fertilizer_N_kg_ha,
        "fertilizer_P_kg_ha": req.fertilizer_P_kg_ha,
        "fertilizer_K_kg_ha": req.fertilizer_K_kg_ha,
        "pest_severity": req.pest_severity,
        "soil_pH": req.soil_pH,
        "days_to_maturity": req.days_to_maturity,
    }])


# Sourced once from the ml package so both paths agree.
try:
    from ml.features.feature_config import ALL_FEATURES as ALL_FEATURE_NAMES  # type: ignore
except Exception:  # noqa: BLE001
    ALL_FEATURE_NAMES = []


def predict_yield(req: YieldPredictionRequest) -> dict[str, Any]:
    cache = _load_artifacts()
    metadata = cache.get("metadata", {})
    model = cache["model"]

    df = _request_to_dataframe(req)
    raw_pred = model.predict(df)
    # MLflow returns numpy arrays; local returns numpy arrays.
    prediction = float(raw_pred[0]) if hasattr(raw_pred, "__len__") else float(raw_pred)
    prediction = max(0.0, round(prediction, 4))

    return {
        "predicted_yield_kg_per_m2": prediction,
        "model_version": str(metadata.get("model_version", "unknown")),
        "model_name": metadata.get("model_name", "unknown"),
        "prediction_timestamp": datetime.now(timezone.utc),
        "key_input_features": {
            "crop_type": req.crop_type,
            "avg_temperature_C": req.avg_temperature_C,
            "humidity_percent": req.humidity_percent,
            "co2_ppm": req.co2_ppm,
            "light_intensity_lux": req.light_intensity_lux,
            "irrigation_mm": req.irrigation_mm,
        },
    }


def model_info() -> Optional[dict[str, Any]]:
    try:
        cache = _load_artifacts()
    except FileNotFoundError:
        return None
    meta = cache.get("metadata", {})
    # Ensure the fields the schema expects exist.
    meta.setdefault("source", cache.get("source", "unknown"))
    meta.setdefault("validation_metrics", {})
    meta.setdefault("test_metrics", {})
    meta.setdefault("features", list(ALL_FEATURE_NAMES))
    return meta


def reload() -> None:
    """Force a reload on next request (used after a model promotion)."""
    _cache.clear()