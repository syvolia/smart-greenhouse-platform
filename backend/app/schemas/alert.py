from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import AlertSeverity, AlertStatus, AlertType


class AlertRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    greenhouse_id: int
    zone_id: Optional[int]
    sensor_id: Optional[int]
    alert_type: AlertType
    severity: AlertSeverity
    status: AlertStatus
    message: str
    value: Optional[float]
    threshold: Optional[str]
    created_at: datetime
    acknowledged_at: Optional[datetime]
    resolved_at: Optional[datetime]


class AlertListResponse(BaseModel):
    alerts: list[AlertRead]
    total: int
    limit: int
    offset: int