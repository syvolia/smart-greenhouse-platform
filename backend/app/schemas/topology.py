from pydantic import BaseModel, ConfigDict

from app.models.enums import GreenhouseStatus, SensorStatus, SensorType


class SensorSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sensor_type: SensorType
    unit: str
    status: SensorStatus


class ZoneTopology(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    crop_type: str
    target_temperature_min: float
    target_temperature_max: float
    target_humidity_min: float
    target_humidity_max: float
    target_soil_moisture_min: float
    target_soil_moisture_max: float
    sensors: list[SensorSummary] = []


class GreenhouseTopology(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    status: GreenhouseStatus
    zones: list[ZoneTopology] = []