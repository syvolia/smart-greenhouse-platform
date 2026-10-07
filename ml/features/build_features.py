"""Reproducible feature engineering pipeline.

Uses scikit-learn's ColumnTransformer so the same transformations are applied
at training time and at inference time (via the persisted pipeline). The
preprocessor is fit ONLY on training data — no leakage.
"""
import logging

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from ml.features.feature_config import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)

logger = logging.getLogger(__name__)


def add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add engineered features that capture greenhouse stress signals."""
    df = df.copy()
    df["temp_range_C"] = df["max_temperature_C"] - df["min_temperature_C"]
    df["temp_deviation_C"] = (df["avg_temperature_C"] - 23.0).abs()
    df["light_daily_integral"] = df["light_intensity_lux"] * df["photoperiod_hours"]
    df["nutrient_total_kg_ha"] = (
        df["fertilizer_N_kg_ha"]
        + df["fertilizer_P_kg_ha"]
        + df["fertilizer_K_kg_ha"]
    )
    return df


def build_preprocessor() -> ColumnTransformer:
    """Return an unfitted ColumnTransformer.

    Numeric: median imputation -> standard scaling.
    Categorical: most-frequent imputation -> one-hot encoding.
    """
    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])

    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
    ])

    all_numeric = NUMERIC_FEATURES + [
        "temp_range_C",
        "temp_deviation_C",
        "light_daily_integral",
        "nutrient_total_kg_ha",
    ]

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, all_numeric),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ],
        remainder="drop",
    )


def prepare_xy(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series]:
    """Split a raw dataframe into feature matrix X and target y."""
    df = add_derived_features(df)
    from ml.features.feature_config import TARGET

    y = df[TARGET].astype(float)
    X = df[NUMERIC_FEATURES + CATEGORICAL_FEATURES + [
        "temp_range_C",
        "temp_deviation_C",
        "light_daily_integral",
        "nutrient_total_kg_ha",
    ]]
    return X, y