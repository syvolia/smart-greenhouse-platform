"""Evaluation metrics and report generation for regression models."""
from typing import Any

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    """Compute MAE, RMSE, R², and MAPE for a regression model."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    r2 = float(r2_score(y_true, y_pred))

    # MAPE: guard against zeros
    mask = y_true != 0
    if mask.any():
        mape = float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)
    else:
        mape = float("nan")

    return {"mae": mae, "rmse": rmse, "r2": r2, "mape": mape}


def summarize(results: dict[str, dict[str, Any]]) -> str:
    """Pretty-print a summary table of model → metrics."""
    lines = [
        f"{'model':<22} {'MAE':>10} {'RMSE':>10} {'R²':>8} {'MAPE %':>8}",
        "-" * 62,
    ]
    for name, metrics in sorted(results.items(), key=lambda kv: kv[1].get("r2", -999), reverse=True):
        lines.append(
            f"{name:<22} "
            f"{metrics.get('mae', float('nan')):>10.4f} "
            f"{metrics.get('rmse', float('nan')):>10.4f} "
            f"{metrics.get('r2', float('nan')):>8.4f} "
            f"{metrics.get('mape', float('nan')):>8.2f}"
        )
    return "\n".join(lines)