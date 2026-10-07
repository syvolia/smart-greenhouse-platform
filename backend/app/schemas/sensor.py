from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import SensorStatus, SensorType


class SensorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    zone_id: int
    sensor_type: SensorType
    unit: str
    status: SensorStatus
    created_at: datetime