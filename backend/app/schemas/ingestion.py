from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class SensorReadingCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sensor_id: int = Field(..., gt=0)
    timestamp: datetime
    value: float


class SensorReadingBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    readings: List[SensorReadingCreate] = Field(..., max_length=500)


class IngestionStats(BaseModel):
    received: int
    inserted: int
    rejected: int
    duplicates: int