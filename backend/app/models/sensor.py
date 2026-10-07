from __future__ import annotations

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import SensorStatus, SensorType

if TYPE_CHECKING:
    from app.models.sensor_reading import SensorReading
    from app.models.zone import Zone


class Sensor(Base):
    __tablename__ = "sensors"
    __table_args__ = (
        UniqueConstraint("zone_id", "sensor_type", name="uq_sensors_zone_type"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    zone_id: Mapped[int] = mapped_column(
        ForeignKey("zones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    sensor_type: Mapped[SensorType] = mapped_column(
        SAEnum(
            SensorType,
            name="sensor_type",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
    )
    unit: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[SensorStatus] = mapped_column(
        SAEnum(
            SensorStatus,
            name="sensor_status",
            native_enum=True,
            values_callable=lambda e: [m.value for m in e],
        ),
        nullable=False,
        default=SensorStatus.ACTIVE,
        server_default=SensorStatus.ACTIVE.value,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    zone: Mapped["Zone"] = relationship(back_populates="sensors")
    readings: Mapped[List["SensorReading"]] = relationship(
        back_populates="sensor",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )