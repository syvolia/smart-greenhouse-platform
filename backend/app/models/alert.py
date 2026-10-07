from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
    text,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.enums import AlertSeverity, AlertStatus, AlertType

if TYPE_CHECKING:
    from app.models.greenhouse import Greenhouse
    from app.models.sensor import Sensor
    from app.models.zone import Zone


def _values(enum_cls):
    return lambda e: [m.value for m in e]


class Alert(Base):
    """An alert raised by the rule engine or the anomaly detector.

    Deduplication: a partial unique index guarantees at most one
    non-resolved alert per (sensor_id, alert_type). See migration 0003.
    """

    __tablename__ = "alerts"
    __table_args__ = (
        Index("ix_alerts_greenhouse_id", "greenhouse_id"),
        Index("ix_alerts_status", "status"),
        Index("ix_alerts_severity", "severity"),
        Index("ix_alerts_created_at", "created_at"),
        Index(
            "uq_alerts_open_per_sensor_type",
            "sensor_id",
            "alert_type",
            unique=True,
            postgresql_where=text("status IN ('open', 'acknowledged')"),
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
        ForeignKey("sensors.id", ondelete="CASCADE"), nullable=True
    )

    alert_type: Mapped[AlertType] = mapped_column(
        SAEnum(AlertType, name="alert_type", native_enum=True,
               values_callable=_values(AlertType)),
        nullable=False,
    )
    severity: Mapped[AlertSeverity] = mapped_column(
        SAEnum(AlertSeverity, name="alert_severity", native_enum=True,
               values_callable=_values(AlertSeverity)),
        nullable=False,
    )
    status: Mapped[AlertStatus] = mapped_column(
        SAEnum(AlertStatus, name="alert_status", native_enum=True,
               values_callable=_values(AlertStatus)),
        nullable=False,
        default=AlertStatus.OPEN,
        server_default=AlertStatus.OPEN.value,
    )

    message: Mapped[str] = mapped_column(Text, nullable=False)
    value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 4), nullable=True)
    threshold: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    acknowledged_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    greenhouse: Mapped["Greenhouse"] = relationship()
    zone: Mapped[Optional["Zone"]] = relationship()
    sensor: Mapped[Optional["Sensor"]] = relationship()