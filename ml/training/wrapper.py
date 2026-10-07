"""A picklable wrapper that packages preprocessor + estimator as one
MLflow pyfunc model. The backend loads this via models:/<name>/<stage>."""
from __future__ import annotations

from typing import Any

import mlflow.pyfunc
import pandas as pd

from ml.features.build_features import add_derived_features
from ml.features.feature_config import ALL_FEATURES


class YieldPredictorModel(mlflow.pyfunc.PythonModel):
    """MLflow pyfunc wrapper around (preprocessor, sklearn_estimator).

    Input: a DataFrame with the raw feature columns (see ALL_FEATURES minus
    derived features). The wrapper computes derived features itself, so
    callers only need to supply the "raw" columns.

    Output: 1-D numpy array of predicted yield (kg/m²).
    """

    def __init__(self, preprocessor: Any, model: Any) -> None:
        self.preprocessor = preprocessor
        self.model = model

    def predict(
        self,
        context: Any = None,
        model_input: pd.DataFrame | None = None,
        params: dict | None = None,
    ):
        if model_input is None:
            raise ValueError("model_input is required")
        df = add_derived_features(model_input.copy())
        X = df[ALL_FEATURES]
        Xt = self.preprocessor.transform(X)
        return self.model.predict(Xt)