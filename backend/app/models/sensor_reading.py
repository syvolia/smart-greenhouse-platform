from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Numeric, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.sensor import Sensor


class SensorReading(Base):
    """
    Time-series table for sensor readings.

    Designed for future high-volume ingestion:
    - BigInteger primary key
    - composite index (sensor_id, timestamp) supports `latest per sensor`
      and `range per sensor` queries efficiently
    - a standalone timestamp index supports cross-sensor time-window queries
    - numeric(12, 4) preserves precision without floating-point drift
    - future scale-out path: convert to declarative partitioning by RANGE(timestamp)
      without changing this ORM model
    """

    __tablename__ = "sensor_readings"
    __table_args__ = (
        UniqueConstraint(
            "sensor_id", "timestamp", name="uq_sensor_readings_sensor_ts"
        ),
        Index("ix_sensor_readings_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    sensor_id: Mapped[int] = mapped_column(
        ForeignKey("sensors.id", ondelete="CASCADE"),
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    sensor: Mapped["Sensor"] = relationship(back_populates="readings")