from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ZoneRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    greenhouse_id: int
    name: str
    crop_type: str
    target_temperature_min: float
    target_temperature_max: float
    target_humidity_min: float
    target_humidity_max: float
    target_soil_moisture_min: float
    target_soil_moisture_max: float
    created_at: datetime
    updated_at: datetime