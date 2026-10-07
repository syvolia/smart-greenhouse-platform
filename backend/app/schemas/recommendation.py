from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import (
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
)


class RecommendationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    greenhouse_id: int
    zone_id: Optional[int]
    sensor_id: Optional[int]
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    status: RecommendationStatus
    message: str
    reason: str
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]


class RecommendationListResponse(BaseModel):
    recommendations: list[RecommendationRead]
    total: int
    limit: int
    offset: int