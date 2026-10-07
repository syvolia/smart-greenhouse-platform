# Crop Yield ML Module

Predicts greenhouse crop yield (`yield_kg_per_m2`) from environmental and
agronomic features.

## Dataset

**Source:** [Greenhouse Crop Yields (IoT & AgriTech)](https://www.kaggle.com/datasets/moezalikhan/greenhouse-crop-yields-dataset)
**License:** CC0 Public Domain
**Rows:** 10,000+ synthetic greenhouse records
**Target:** `yield_kg_per_m2`

If the Kaggle API is unavailable (no credentials, offline), `data/download.py`
generates a statistically equivalent synthetic dataset so the pipeline is always
reproducible.

## Pipeline

1. **Download** — `python -m ml.data.download`
2. **Train** — `python -m ml.training.train`
3. Model is saved to `ml/models/` and loaded by the backend API at
   `POST /ml/predict-yield`.

## Reproducibility

- Random seed: 42 (set in `features/feature_config.py`)
- Train/validation/test split: 70/15/15, stratified by `crop_type`
- Preprocessor (imputer + one-hot + scaler) is fit **only** on training data
  and saved together with the model, preventing data leakage.
- The full pipeline (preprocessor + model) is persisted as a single `.joblib`
  artifact so the API can consume raw inputs.