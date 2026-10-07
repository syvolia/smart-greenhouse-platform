"""Train candidate models, log every run to MLflow, register the best one.

MLflow is best-effort: if it can't be reached, training still completes and
the model is persisted to disk. This is important — a broken tracking server
must never block a training run.

Usage (inside Docker or on the host, both work):
    export MLFLOW_TRACKING_URI=http://localhost:5001
    python -m ml.training.train
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from mlflow.models import infer_signature
from sklearn.model_selection import train_test_split

from ml.data.download import OUTPUT_CSV, main as download_main
from ml.features.build_features import build_preprocessor, prepare_xy
from ml.features.feature_config import (
    ALL_FEATURES,
    METADATA_FILENAME,
    MLFLOW_MODEL_NAME,
    MODEL_FILENAME,
    MODEL_VERSION,
    RANDOM_SEED,
    TARGET,
)
from ml.training import mlflow_tracker
from ml.training.evaluate import evaluate_model, summarize
from ml.training.models import build_models
from ml.training.wrapper import YieldPredictorModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)


def _dataset_hash(path: Path) -> str:
    """Stable content hash of the raw CSV, for run reproducibility."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def load_dataset() -> pd.DataFrame:
    if not OUTPUT_CSV.exists():
        logger.info("Dataset not found; running downloader")
        download_main()
    return pd.read_csv(OUTPUT_CSV)


def split_data(df: pd.DataFrame):
    """70/15/15 train/val/test split, stratified by crop_type."""
    train_val, test = train_test_split(
        df, test_size=0.15, random_state=RANDOM_SEED, stratify=df["crop_type"]
    )
    val_size = 0.15 / 0.85
    train, val = train_test_split(
        train_val, test_size=val_size, random_state=RANDOM_SEED,
        stratify=train_val["crop_type"],
    )
    logger.info("Split: train=%d val=%d test=%d", len(train), len(val), len(test))
    return train, val, test


def _train_one(
    name: str,
    model,
    preprocessor,
    X_train_t,
    y_train,
    X_val_t,
    X_val_raw: pd.DataFrame,
    y_val,
    dataset_path: str,
    dataset_hash: str,
    tracking_enabled: bool,
) -> tuple[dict, str | None]:
    """Train one candidate, log to MLflow, return (val_metrics, run_id)."""
    run_id: str | None = None
    try:
        cm = mlflow.start_run(run_name=name) if tracking_enabled else _null_ctx()
        with cm as run:
            if run is not None:
                run_id = run.info.run_id

            model.fit(X_train_t, y_train)
            val_preds = model.predict(X_val_t)
            metrics = evaluate_model(y_val.to_numpy(), val_preds)

            if tracking_enabled and run is not None:
                mlflow.log_params({
                    "model_type": name,
                    "dataset_path": dataset_path,
                    "dataset_hash": dataset_hash,
                    "random_seed": RANDOM_SEED,
                    "train_rows": len(y_train),
                    "val_rows": len(y_val),
                })
                mlflow_tracker.log_model_params(model)
                mlflow_tracker.log_feature_list(list(ALL_FEATURES))
                mlflow.log_metrics({
                    f"val_{k}": float(v) for k, v in metrics.items()
                })
                mlflow.set_tags({
                    "model_version": MODEL_VERSION,
                    "target": TARGET,
                    "trained_at": datetime.now(timezone.utc).isoformat(),
                })

                # Log the wrapped pyfunc model so it can be registered later.
                wrapped = YieldPredictorModel(preprocessor, model)
                sample = X_val_raw.head(5)
                try:
                    signature = infer_signature(sample, val_preds[:5])
                except Exception:  # noqa: BLE001
                    signature = None
                mlflow.pyfunc.log_model(
                    artifact_path="model",
                    python_model=wrapped,
                    signature=signature,
                    input_example=sample,
                )
        logger.info(
            "%s | MAE=%.4f RMSE=%.4f R²=%.4f MAPE=%.2f%%",
            name, metrics["mae"], metrics["rmse"], metrics["r2"], metrics["mape"],
        )
        return metrics, run_id
    except Exception as exc:  # noqa: BLE001
        logger.exception("Training %s failed: %s", name, exc)
        raise


class _null_ctx:
    """No-op context manager for the tracking-disabled path."""
    def __enter__(self) -> None: return None
    def __exit__(self, *args) -> None: return None


def select_best(results: dict) -> str:
    """Best model by validation R²; tie-break on RMSE."""
    ranked = sorted(results.items(), key=lambda kv: (-kv[1]["r2"], kv[1]["rmse"]))
    return ranked[0][0]


def main() -> None:
    tracking_enabled = mlflow_tracker.configure()
    if not tracking_enabled:
        logger.warning(
            "MLflow tracking is disabled. Training will proceed and the model "
            "will be saved locally, but no runs will be logged."
        )

    df = load_dataset()
    dataset_hash = _dataset_hash(OUTPUT_CSV)
    logger.info("Dataset hash: %s", dataset_hash)

    train_df, val_df, test_df = split_data(df)

    X_train, y_train = prepare_xy(train_df)
    X_val, y_val = prepare_xy(val_df)
    X_test, y_test = prepare_xy(test_df)

    preprocessor = build_preprocessor()
    X_train_t = preprocessor.fit_transform(X_train)
    X_val_t = preprocessor.transform(X_val)
    X_test_t = preprocessor.transform(X_test)

    results: dict[str, dict] = {}
    run_ids: dict[str, str | None] = {}
    fitted: dict[str, object] = {}

    for name, model in build_models().items():
        logger.info("Training %s ...", name)
        metrics, rid = _train_one(
            name=name,
            model=model,
            preprocessor=preprocessor,
            X_train_t=X_train_t,
            y_train=y_train,
            X_val_t=X_val_t,
            X_val_raw=X_val,
            y_val=y_val,
            dataset_path=str(OUTPUT_CSV),
            dataset_hash=dataset_hash,
            tracking_enabled=tracking_enabled,
        )
        results[name] = metrics
        run_ids[name] = rid
        fitted[name] = model

    print("\n=== Validation leaderboard ===")
    print(summarize(results))
    print()

    best_name = select_best(results)
    logger.info("Selected model: %s", best_name)

    # Evaluate the winner on the held-out test set.
    test_preds = fitted[best_name].predict(X_test_t)
    test_metrics = evaluate_model(y_test.to_numpy(), test_preds)
    logger.info(
        "Test set | MAE=%.4f RMSE=%.4f R²=%.4f MAPE=%.2f%%",
        test_metrics["mae"], test_metrics["rmse"], test_metrics["r2"], test_metrics["mape"],
    )

    # Persist locally (always — this is the fallback path for the backend).
    pipeline = {
        "preprocessor": preprocessor,
        "model": fitted[best_name],
        "model_name": best_name,
    }
    model_path = MODELS_DIR / MODEL_FILENAME
    joblib.dump(pipeline, model_path)
    logger.info("Saved local model to %s", model_path)

    metadata = {
        "model_version": MODEL_VERSION,
        "model_name": best_name,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "dataset_rows": len(df),
        "dataset_hash": dataset_hash,
        "train_rows": len(train_df),
        "val_rows": len(val_df),
        "test_rows": len(test_df),
        "target": TARGET,
        "features": list(ALL_FEATURES),
        "validation_metrics": results[best_name],
        "test_metrics": test_metrics,
        "all_validation_metrics": results,
    }
    meta_path = MODELS_DIR / METADATA_FILENAME
    with open(meta_path, "w") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Saved metadata to %s", meta_path)

    leaderboard_path = MODELS_DIR / "leaderboard.json"
    with open(leaderboard_path, "w") as f:
        json.dump(results, f, indent=2)

    # Register with MLflow (no stage transition — that's a deliberate act).
    if tracking_enabled and run_ids.get(best_name):
        registered_version = mlflow_tracker.register_best_model(
            run_id=run_ids[best_name],
            artifact_path="model",
            model_name=MLFLOW_MODEL_NAME,
        )
        if registered_version:
            logger.info(
                "Registered as %s version %s. "
                "The model is NOT promoted automatically — see docs/mlops.md "
                "for the promotion workflow.",
                MLFLOW_MODEL_NAME, registered_version,
            )


if __name__ == "__main__":
    main()