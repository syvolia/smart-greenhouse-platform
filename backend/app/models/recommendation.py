from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import (
    RecommendationPriority,
    RecommendationStatus,
    RecommendationType,
)


def _values(enum_cls):
    return lambda e: [m.value for m in e]


class Recommendation(Base):
    """An actionable recommendation derived from sensor data, alerts, or ML.

    Deduplication: a partial unique index on
    (greenhouse_id, COALESCE(zone_id, 0), recommendation_type) WHERE status='open'
    guarantees at most one open recommendation per condition per scope.
    """

    __tablename__ = "recommendations"
    __table_args__ = (
        Index("ix_recommendations_greenhouse_id", "greenhouse_id"),
        Index("ix_recommendations_zone_id", "zone_id"),
        Index("ix_recommendations_status", "status"),
        Index("ix_recommendations_priority", "priority"),
        Index("ix_recommendations_created_at", "created_at"),
        Index(
            "uq_recommendations_open_per_scope",
            "greenhouse_id",
            text("(COALESCE(zone_id, 0))"),
            "recommendation_type",
            unique=True,
            postgresql_where=text("status = 'open'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    greenhouse_id: Mapped[int] = mapped_column(
        ForeignKey("greenhouses.id", ondelete="CASCADE"), nullable=False
    )
    zone_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE"), nullable=True
    )
    sensor_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("sensors.id", ondelete="SET NULL"), nullable=True
    )

    recommendation_type: Mapped[RecommendationType] = mapped_column(
        SAEnum(RecommendationType, name="recommendation_type", native_enum=True,
               values_callable=_values(RecommendationType)),
        nullable=False,
    )
    priority: Mapped[RecommendationPriority] = mapped_column(
        SAEnum(RecommendationPriority, name="recommendation_priority",
               native_enum=True, values_callable=_values(RecommendationPriority)),
        nullable=False,
    )
    status: Mapped[RecommendationStatus] = mapped_column(
        SAEnum(RecommendationStatus, name="recommendation_status",
               native_enum=True, values_callable=_values(RecommendationStatus)),
        nullable=False,
        default=RecommendationStatus.OPEN,
        server_default=RecommendationStatus.OPEN.value,
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    greenhouse = relationship("Greenhouse")
    zone = relationship("Zone")
    sensor = relationship("Sensor")