from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

CropType = Literal["Tomato", "Cucumber", "Lettuce", "Pepper"]


class YieldPredictionRequest(BaseModel):
    """Input features for crop yield prediction.

    Field names mirror the training dataset columns so the same preprocessor
    pipeline (fitted during training) can be applied at inference.
    """
    model_config = ConfigDict(extra="forbid")

    crop_type: CropType
    avg_temperature_C: float = Field(..., ge=-10.0, le=50.0)
    min_temperature_C: float = Field(..., ge=-20.0, le=40.0)
    max_temperature_C: float = Field(..., ge=-5.0, le=60.0)
    humidity_percent: float = Field(..., ge=0.0, le=100.0)
    co2_ppm: float = Field(..., ge=0.0, le=5000.0)
    light_intensity_lux: float = Field(..., ge=0.0, le=100000.0)
    photoperiod_hours: float = Field(..., ge=0.0, le=24.0)
    irrigation_mm: float = Field(..., ge=0.0, le=100.0)
    fertilizer_N_kg_ha: float = Field(..., ge=0.0, le=500.0)
    fertilizer_P_kg_ha: float = Field(..., ge=0.0, le=300.0)
    fertilizer_K_kg_ha: float = Field(..., ge=0.0, le=400.0)
    pest_severity: float = Field(..., ge=0.0, le=10.0)
    soil_pH: float = Field(..., ge=3.0, le=10.0)
    days_to_maturity: int = Field(..., ge=1, le=365)


class YieldPredictionResponse(BaseModel):
    predicted_yield_kg_per_m2: float
    model_version: str
    model_name: str
    prediction_timestamp: datetime
    key_input_features: dict[str, float | str]


class ModelInfoResponse(BaseModel):
    model_version: str
    model_name: str
    source: str
    stage: Optional[str] = None
    run_id: Optional[str] = None
    trained_at: str
    validation_metrics: dict[str, float] = {}
    test_metrics: dict[str, float] = {}
    features: list[str] = []