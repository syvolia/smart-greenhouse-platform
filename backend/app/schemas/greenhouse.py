from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import GreenhouseStatus


class GreenhouseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str
    status: GreenhouseStatus
    created_at: datetime
    updated_at: datetime