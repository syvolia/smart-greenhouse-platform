from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from app.models.enums import SensorType
from datetime import datetime

class EnvironmentalStatus(str, Enum):
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class SensorReadingSummary(BaseModel):
    sensor_id: int
    zone_id: int
    sensor_type: SensorType
    unit: str
    current_value: Optional[float]
    last_updated: Optional[datetime]
    min_value: Optional[float]
    max_value: Optional[float]
    avg_value: Optional[float]
    reading_count: int
    status: EnvironmentalStatus
    target_min: Optional[float] = None
    target_max: Optional[float] = None
    deviation_percent: Optional[float] = None


class ZoneOverview(BaseModel):
    zone_id: int
    greenhouse_id: int
    name: str
    crop_type: str
    overall_status: EnvironmentalStatus
    readings: list[SensorReadingSummary]


class GreenhouseOverview(BaseModel):
    greenhouse_id: int
    name: str
    location: str
    overall_status: EnvironmentalStatus
    window_start: datetime
    window_end: datetime
    zones: list[ZoneOverview]
    open_alerts_count: int = 0
    critical_alerts_count: int = 0
    open_recommendations_count: int = 0
    high_priority_recommendations_count: int = 0


class LatestReading(BaseModel):
    sensor_id: int
    zone_id: int
    sensor_type: SensorType
    unit: str
    value: float
    timestamp: datetime


class LatestReadingsResponse(BaseModel):
    greenhouse_id: int
    readings: list[LatestReading]


class ReadingOut(BaseModel):
    id: int
    sensor_id: int
    timestamp: datetime
    value: float


class HistoryResponse(BaseModel):
    readings: list[ReadingOut]
    count: int
    limit: int
    offset: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]