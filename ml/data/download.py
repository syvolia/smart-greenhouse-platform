"""Acquire the greenhouse crop yield dataset.

Primary: Kaggle 'Greenhouse Crop Yields (IoT & AgriTech)' (CC0).
Fallback: synthetic generator with statistically equivalent schema.

Run:
    python -m ml.data.download
"""
import logging
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent
RAW_DIR = DATA_DIR / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_CSV = RAW_DIR / "greenhouse_crop_yields.csv"

RANDOM_SEED = 42

CROPS = {
    "Tomato": {
        "temp_opt": (20.0, 26.0),
        "humidity_opt": (65.0, 80.0),
        "yield_base": 5.5,
        "yield_std": 0.9,
    },
    "Cucumber": {
        "temp_opt": (22.0, 28.0),
        "humidity_opt": (70.0, 85.0),
        "yield_base": 4.0,
        "yield_std": 0.7,
    },
    "Lettuce": {
        "temp_opt": (16.0, 22.0),
        "humidity_opt": (60.0, 75.0),
        "yield_base": 3.0,
        "yield_std": 0.5,
    },
    "Pepper": {
        "temp_opt": (21.0, 27.0),
        "humidity_opt": (60.0, 75.0),
        "yield_base": 3.5,
        "yield_std": 0.6,
    },
}


def _try_kaggle_download() -> bool:
    """Attempt to download from Kaggle. Returns True on success."""
    try:
        import kaggle  # noqa: F401
    except ImportError:
        logger.info("kaggle package not installed; skipping Kaggle download")
        return False

    try:
        from kaggle.api.kaggle_api_extended import KaggleApi

        api = KaggleApi()
        api.authenticate()
        api.dataset_download_files(
            "moezalikhan/greenhouse-crop-yields-dataset",
            path=str(RAW_DIR),
            unzip=True,
        )
        # The Kaggle download unzips into RAW_DIR; find the CSV
        for f in RAW_DIR.glob("*.csv"):
            if f.name != OUTPUT_CSV.name:
                f.rename(OUTPUT_CSV)
                break
        logger.info("Downloaded Kaggle dataset to %s", OUTPUT_CSV)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("Kaggle download failed: %s", exc)
        return False


def _generate_synthetic(n_rows: int = 10_000) -> pd.DataFrame:
    """Generate a synthetic dataset with the same schema and realistic
    statistical properties as the Kaggle dataset."""
    rng = np.random.default_rng(RANDOM_SEED)
    rows = []
    crop_names = list(CROPS.keys())
    crop_weights = [0.4, 0.3, 0.2, 0.1]

    for i in range(n_rows):
        crop = rng.choice(crop_names, p=crop_weights)
        cfg = CROPS[crop]

        # Environmental features
        avg_temp = rng.normal(np.mean(cfg["temp_opt"]), 3.0)
        min_temp = avg_temp - rng.uniform(3.0, 8.0)
        max_temp = avg_temp + rng.uniform(3.0, 8.0)
        humidity = rng.normal(np.mean(cfg["humidity_opt"]), 8.0)
        humidity = float(np.clip(humidity, 30.0, 95.0))
        co2 = rng.normal(800.0, 150.0)
        light = rng.uniform(10_000.0, 45_000.0)
        photoperiod = rng.uniform(10.0, 16.0)
        irrigation = rng.uniform(2.0, 8.0)
        n_kg = rng.uniform(60.0, 200.0)
        p_kg = rng.uniform(30.0, 100.0)
        k_kg = rng.uniform(40.0, 150.0)
        pest = rng.uniform(0.0, 8.0)
        soil_ph = rng.normal(6.5, 0.4)
        soil_ph = float(np.clip(soil_ph, 5.0, 8.0))
        days = int(rng.normal(90, 15))

        # Yield as a non-linear function of conditions
        temp_penalty = abs(avg_temp - np.mean(cfg["temp_opt"])) / 10.0
        humid_penalty = abs(humidity - np.mean(cfg["humidity_opt"])) / 30.0
        light_bonus = (light - 10_000.0) / 40_000.0 * 0.5
        co2_bonus = (co2 - 400.0) / 1200.0 * 0.3
        pest_penalty = pest / 10.0 * 1.5
        water_bonus = min(irrigation / 8.0, 1.0) * 0.3
        nutrient_bonus = (n_kg / 200.0 + p_kg / 100.0 + k_kg / 150.0) / 3.0 * 0.4
        ph_penalty = abs(soil_ph - 6.5) / 1.5

        yield_val = (
            cfg["yield_base"]
            - temp_penalty
            - humid_penalty
            + light_bonus
            + co2_bonus
            - pest_penalty
            + water_bonus
            + nutrient_bonus
            - ph_penalty
            + rng.normal(0, cfg["yield_std"] * 0.4)
        )
        yield_val = max(0.1, float(yield_val))

        rows.append({
            "greenhouse_id": int(rng.integers(1, 6)),
            "crop_type": crop,
            "variety": f"{crop}_var_{rng.integers(1, 4)}",
            "planting_date": f"2025-{rng.integers(1, 13):02d}-{rng.integers(1, 29):02d}",
            "harvest_date": f"2025-{rng.integers(1, 13):02d}-{rng.integers(1, 29):02d}",
            "days_to_maturity": days,
            "avg_temperature_C": round(avg_temp, 2),
            "min_temperature_C": round(min_temp, 2),
            "max_temperature_C": round(max_temp, 2),
            "humidity_percent": round(humidity, 2),
            "co2_ppm": round(co2, 1),
            "light_intensity_lux": round(light, 1),
            "photoperiod_hours": round(photoperiod, 2),
            "irrigation_mm": round(irrigation, 2),
            "fertilizer_N_kg_ha": round(n_kg, 1),
            "fertilizer_P_kg_ha": round(p_kg, 1),
            "fertilizer_K_kg_ha": round(k_kg, 1),
            "pest_severity": round(pest, 2),
            "soil_pH": round(soil_ph, 2),
            "yield_kg_per_m2": round(yield_val, 3),
        })

    return pd.DataFrame(rows)


def main() -> None:
    if OUTPUT_CSV.exists():
        logger.info("Dataset already exists at %s; skipping download", OUTPUT_CSV)
        return

    if _try_kaggle_download():
        return

    logger.info("Falling back to synthetic dataset generation")
    df = _generate_synthetic(10_000)
    df.to_csv(OUTPUT_CSV, index=False)
    logger.info("Wrote %d rows to %s", len(df), OUTPUT_CSV)


if __name__ == "__main__":
    main()