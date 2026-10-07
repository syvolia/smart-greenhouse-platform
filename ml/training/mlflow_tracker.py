"""Thin helpers so train.py stays readable.

Everything here is optional: if the MLflow client cannot reach a tracking
server, callers should treat tracking as best-effort. Model training never
depends on MLflow being up.
"""
import logging
from typing import Any, Optional

import mlflow
from mlflow.tracking import MlflowClient

from ml.features.feature_config import (
    MLFLOW_EXPERIMENT_NAME,
    MLFLOW_TRACKING_URI,
)

logger = logging.getLogger(__name__)


def configure() -> bool:
    """Point MLflow at the tracking server. Return True on success."""
    try:
        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        client = MlflowClient()
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("MLflow tracking disabled: %s", exc)
        return False


def log_dataset_version(path: str, version_hash: str) -> None:
    """Log dataset identity so a run is fully reproducible."""
    mlflow.log_param("dataset_path", path)
    mlflow.log_param("dataset_hash", version_hash)


def log_feature_list(features: list[str]) -> None:
    mlflow.log_param("feature_count", len(features))
    mlflow.log_text("\n".join(features), "features.txt")


def log_model_params(model: Any) -> None:
    try:
        params = model.get_params()
        # MLflow params must be strings/floats/ints — convert everything
        for k, v in params.items():
            try:
                mlflow.log_param(k, v if isinstance(v, (int, float, str, bool)) else str(v))
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass


def register_best_model(
    run_id: str, artifact_path: str, model_name: str
) -> Optional[str]:
    """Register the model from `run_id` as a new version of `model_name`.

    Returns the new version string, or None if registration failed.
    Does NOT transition the model to any stage — promotion is a manual step.
    """
    try:
        mv = mlflow.register_model(f"runs:/{run_id}/{artifact_path}", model_name)
        logger.info(
            "Registered model %s version %s (run %s)", model_name, mv.version, run_id
        )
        return str(mv.version)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Model registration failed: %s", exc)
        return None