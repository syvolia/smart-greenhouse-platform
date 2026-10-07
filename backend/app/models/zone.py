from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List, TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.greenhouse import Greenhouse
    from app.models.sensor import Sensor


class Zone(Base):
    __tablename__ = "zones"
    __table_args__ = (
        UniqueConstraint("greenhouse_id", "name", name="uq_zones_greenhouse_name"),
        CheckConstraint(
            "target_temperature_min < target_temperature_max",
            name="ck_zones_temp_range",
        ),
        CheckConstraint(
            "target_humidity_min < target_humidity_max",
            name="ck_zones_humidity_range",
        ),
        CheckConstraint(
            "target_soil_moisture_min < target_soil_moisture_max",
            name="ck_zones_soil_moisture_range",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    greenhouse_id: Mapped[int] = mapped_column(
        ForeignKey("greenhouses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    crop_type: Mapped[str] = mapped_column(String(80), nullable=False)

    target_temperature_min: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    target_temperature_max: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    target_humidity_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_humidity_max: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_soil_moisture_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_soil_moisture_max: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    greenhouse: Mapped["Greenhouse"] = relationship(back_populates="zones")
    sensors: Mapped[List["Sensor"]] = relationship(
        back_populates="zone",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Sensor.id",
    )