"""Data shapes and the DB-facing context builder.

Rules consume plain dataclasses — they never touch SQLAlchemy. The builder
issues a fixed number of queries regardless of the number of zones/sensors,
avoiding N+1.
"""
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select, text as sql_text
from sqlalchemy.orm import Session, selectinload

from app.models.alert import Alert
from app.models.enums import AlertStatus, SensorType
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.zone import Zone

logger = logging.getLogger(__name__)

_OPEN_ALERT_STATES = (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)
_RECENT_WINDOW_HOURS = 1
_MAX_RECENT_PER_SENSOR = 30


@dataclass(frozen=True)
class SensorView:
    id: int
    zone_id: int
    sensor_type: SensorType
    unit: str
    current_value: Optional[float]
    last_timestamp: Optional[datetime]
    recent_values: list[tuple[datetime, float]]  # newest first


@dataclass(frozen=True)
class ZoneView:
    id: int
    greenhouse_id: int
    name: str
    crop_type: str
    target_temperature: Optional[tuple[float, float]]
    target_humidity: Optional[tuple[float, float]]
    target_soil_moisture: Optional[tuple[float, float]]
    sensors: list[SensorView]

    def sensor(self, sensor_type: SensorType) -> Optional[SensorView]:
        for s in self.sensors:
            if s.sensor_type == sensor_type:
                return s
        return None


@dataclass(frozen=True)
class OpenAlertView:
    id: int
    greenhouse_id: int
    zone_id: Optional[int]
    sensor_id: Optional[int]
    alert_type: str
    severity: str
    message: str


@dataclass
class RecommendationContext:
    zones: list[ZoneView]
    open_alerts: list[OpenAlertView]
    # Filled by the service after calling the ML model — one entry per zone.
    predicted_yield_by_zone: dict[int, float] = field(default_factory=dict)
    model_version: str = "unknown"

    def zone(self, zone_id: int) -> Optional[ZoneView]:
        for z in self.zones:
            if z.id == zone_id:
                return z
        return None


# ---------------------------------------------------------------------------
# Context builder
# ---------------------------------------------------------------------------


def _to_range(lo, hi) -> Optional[tuple[float, float]]:
    if lo is None or hi is None:
        return None
    return (float(lo), float(hi))


def _fetch_recent_readings(
    db: Session, sensor_ids: list[int]
) -> dict[int, list[tuple[datetime, float]]]:
    """Return {sensor_id: [(ts, value), ...]} newest-first, capped per sensor."""
    if not sensor_ids:
        return {}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=_RECENT_WINDOW_HOURS)
    sql = sql_text(
        """
        SELECT sensor_id, timestamp, value
        FROM (
            SELECT sensor_id, timestamp, value,
                   ROW_NUMBER() OVER (
                       PARTITION BY sensor_id ORDER BY timestamp DESC
                   ) AS rn
            FROM sensor_readings
            WHERE sensor_id = ANY(:ids)
              AND timestamp >= :cutoff
        ) t
        WHERE rn <= :lim
        ORDER BY sensor_id, rn
        """
    )
    rows = db.execute(
        sql, {"ids": sensor_ids, "cutoff": cutoff, "lim": _MAX_RECENT_PER_SENSOR}
    ).all()
    out: dict[int, list[tuple[datetime, float]]] = {}
    for r in rows:
        out.setdefault(r.sensor_id, []).append((r.timestamp, float(r.value)))
    return out


def build_context(db: Session, zone_ids: list[int]) -> RecommendationContext:
    if not zone_ids:
        return RecommendationContext(zones=[], open_alerts=[])

    zones = db.scalars(
        select(Zone)
        .options(selectinload(Zone.sensors))
        .where(Zone.id.in_(zone_ids))
    ).all()

    sensor_ids = [s.id for z in zones for s in z.sensors]
    recent = _fetch_recent_readings(db, sensor_ids)

    zone_views: list[ZoneView] = []
    for z in zones:
        sensor_views: list[SensorView] = []
        for s in z.sensors:
            rows = recent.get(s.id, [])
            current = rows[0][1] if rows else None
            last_ts = rows[0][0] if rows else None
            sensor_views.append(
                SensorView(
                    id=s.id,
                    zone_id=s.zone_id,
                    sensor_type=s.sensor_type,
                    unit=s.unit,
                    current_value=current,
                    last_timestamp=last_ts,
                    recent_values=rows,
                )
            )
        zone_views.append(
            ZoneView(
                id=z.id,
                greenhouse_id=z.greenhouse_id,
                name=z.name,
                crop_type=z.crop_type,
                target_temperature=_to_range(
                    z.target_temperature_min, z.target_temperature_max
                ),
                target_humidity=_to_range(
                    z.target_humidity_min, z.target_humidity_max
                ),
                target_soil_moisture=_to_range(
                    z.target_soil_moisture_min, z.target_soil_moisture_max
                ),
                sensors=sensor_views,
            )
        )

    alerts = db.scalars(
        select(Alert).where(
            Alert.zone_id.in_(zone_ids),
            Alert.status.in_(_OPEN_ALERT_STATES),
        )
    ).all()

    alert_views = [
        OpenAlertView(
            id=a.id,
            greenhouse_id=a.greenhouse_id,
            zone_id=a.zone_id,
            sensor_id=a.sensor_id,
            alert_type=a.alert_type.value if hasattr(a.alert_type, "value") else str(a.alert_type),
            severity=a.severity.value if hasattr(a.severity, "value") else str(a.severity),
            message=a.message,
        )
        for a in alerts
    ]

    return RecommendationContext(zones=zone_views, open_alerts=alert_views)