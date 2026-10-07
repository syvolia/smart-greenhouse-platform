import logging
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.alert import Alert
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    RecommendationPriority,
    RecommendationStatus,
    SensorType,
)
from app.models.greenhouse import Greenhouse
from app.models.recommendation import Recommendation
from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.models.zone import Zone
from app.schemas.analytics import (
    EnvironmentalStatus,
    GreenhouseOverview,
    LatestReading,
    LatestReadingsResponse,
    ReadingOut,
    HistoryResponse,
    SensorReadingSummary,
    ZoneOverview,
)

logger = logging.getLogger(__name__)

# Maps a sensor type to the Zone columns holding its target range.
# Types not present here (co2, light, irrigation) have no zone-level targets.
ZONE_TARGET_FIELDS: dict[SensorType, tuple[str, str]] = {
    SensorType.TEMPERATURE: ("target_temperature_min", "target_temperature_max"),
    SensorType.HUMIDITY: ("target_humidity_min", "target_humidity_max"),
    SensorType.SOIL_MOISTURE: (
        "target_soil_moisture_min",
        "target_soil_moisture_max",
    ),
}

_OPEN_ALERT_STATES = (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)

_SEVERITY = {
    EnvironmentalStatus.UNKNOWN: 0,
    EnvironmentalStatus.NORMAL: 1,
    EnvironmentalStatus.WARNING: 2,
    EnvironmentalStatus.CRITICAL: 3,
}


# ---------------------------------------------------------------------------
# Status classification
# ---------------------------------------------------------------------------


def classify_status(
    value: Optional[float],
    target_min: Optional[float],
    target_max: Optional[float],
) -> tuple[EnvironmentalStatus, Optional[float]]:
    """Return (status, deviation_percent) for a value relative to a target range.

    - NORMAL   if target_min <= value <= target_max
    - WARNING  if outside the range but within tolerance_percent of the span
    - CRITICAL if beyond the tolerance band
    - UNKNOWN  if value or targets are missing
    """
    if value is None or target_min is None or target_max is None:
        return EnvironmentalStatus.UNKNOWN, None

    if target_min <= value <= target_max:
        return EnvironmentalStatus.NORMAL, 0.0

    span = target_max - target_min
    if span <= 0:
        return EnvironmentalStatus.UNKNOWN, None

    tolerance = span * settings.analytics_warning_tolerance_percent / 100.0

    if value < target_min:
        deviation = target_min - value
        deviation_percent = -(deviation / span) * 100.0
    else:
        deviation = value - target_max
        deviation_percent = (deviation / span) * 100.0

    if deviation <= tolerance:
        return EnvironmentalStatus.WARNING, round(deviation_percent, 2)
    return EnvironmentalStatus.CRITICAL, round(deviation_percent, 2)


def combine_statuses(statuses: list[EnvironmentalStatus]) -> EnvironmentalStatus:
    """Return the worst status in the list."""
    result = EnvironmentalStatus.UNKNOWN
    for s in statuses:
        if _SEVERITY[s] > _SEVERITY[result]:
            result = s
    return result


def _zone_targets_for(
    sensor_type: SensorType, zone: Zone
) -> tuple[Optional[float], Optional[float]]:
    fields = ZONE_TARGET_FIELDS.get(sensor_type)
    if fields is None:
        return None, None
    min_attr, max_attr = fields
    lo = getattr(zone, min_attr, None)
    hi = getattr(zone, max_attr, None)
    return (
        float(lo) if lo is not None else None,
        float(hi) if hi is not None else None,
    )


# ---------------------------------------------------------------------------
# Bulk queries (avoid N+1)
# ---------------------------------------------------------------------------


def _fetch_latest_readings(
    db: Session, sensor_ids: list[int], start: datetime, end: datetime
) -> dict[int, tuple[datetime, float]]:
    """Return {sensor_id: (timestamp, value)} for the latest reading per sensor
    inside [start, end]. Uses Postgres DISTINCT ON with the composite index."""
    if not sensor_ids:
        return {}
    stmt = (
        select(
            SensorReading.sensor_id,
            SensorReading.timestamp,
            SensorReading.value,
        )
        .where(
            SensorReading.sensor_id.in_(sensor_ids),
            SensorReading.timestamp >= start,
            SensorReading.timestamp <= end,
        )
        .distinct(SensorReading.sensor_id)
        .order_by(SensorReading.sensor_id, SensorReading.timestamp.desc())
    )
    rows = db.execute(stmt).all()
    return {row.sensor_id: (row.timestamp, float(row.value)) for row in rows}


def _fetch_stats(
    db: Session, sensor_ids: list[int], start: datetime, end: datetime
) -> dict[int, dict[str, Any]]:
    """Return per-sensor aggregations (min/max/avg/count/last_updated)."""
    if not sensor_ids:
        return {}
    stmt = (
        select(
            SensorReading.sensor_id.label("sensor_id"),
            func.min(SensorReading.value).label("min_value"),
            func.max(SensorReading.value).label("max_value"),
            func.avg(SensorReading.value).label("avg_value"),
            func.count(SensorReading.id).label("reading_count"),
            func.max(SensorReading.timestamp).label("last_updated"),
        )
        .where(
            SensorReading.sensor_id.in_(sensor_ids),
            SensorReading.timestamp >= start,
            SensorReading.timestamp <= end,
        )
        .group_by(SensorReading.sensor_id)
    )
    out: dict[int, dict[str, Any]] = {}
    for row in db.execute(stmt).all():
        out[row.sensor_id] = {
            "min_value": float(row.min_value) if row.min_value is not None else None,
            "max_value": float(row.max_value) if row.max_value is not None else None,
            "avg_value": float(row.avg_value) if row.avg_value is not None else None,
            "reading_count": int(row.reading_count),
            "last_updated": row.last_updated,
        }
    return out


def _build_sensor_summary(
    sensor: Sensor,
    zone: Zone,
    latest: dict[int, tuple[datetime, float]],
    stats: dict[int, dict[str, Any]],
) -> SensorReadingSummary:
    latest_row = latest.get(sensor.id)
    stats_row = stats.get(sensor.id, {})

    current_value = latest_row[1] if latest_row else None
    last_updated = latest_row[0] if latest_row else stats_row.get("last_updated")

    target_min, target_max = _zone_targets_for(sensor.sensor_type, zone)
    status, deviation = classify_status(current_value, target_min, target_max)

    return SensorReadingSummary(
        sensor_id=sensor.id,
        zone_id=zone.id,
        sensor_type=sensor.sensor_type,
        unit=sensor.unit,
        current_value=current_value,
        last_updated=last_updated,
        min_value=stats_row.get("min_value"),
        max_value=stats_row.get("max_value"),
        avg_value=stats_row.get("avg_value"),
        reading_count=stats_row.get("reading_count", 0),
        status=status,
        target_min=target_min,
        target_max=target_max,
        deviation_percent=deviation,
    )


def _count_open_alerts(
    db: Session, greenhouse_id: int, severity: Optional[AlertSeverity] = None
) -> int:
    stmt = select(func.count(Alert.id)).where(
        Alert.greenhouse_id == greenhouse_id,
        Alert.status.in_(_OPEN_ALERT_STATES),
    )
    if severity is not None:
        stmt = stmt.where(Alert.severity == severity)
    return int(db.scalar(stmt) or 0)


def _count_open_recommendations(
    db: Session, greenhouse_id: int, min_priority: Optional[str] = None
) -> int:
    """Count open recommendations for a greenhouse.

    If min_priority == 'high', counts only HIGH and CRITICAL.
    """
    stmt = select(func.count(Recommendation.id)).where(
        Recommendation.greenhouse_id == greenhouse_id,
        Recommendation.status == RecommendationStatus.OPEN,
    )
    if min_priority == "high":
        stmt = stmt.where(
            Recommendation.priority.in_(
                [RecommendationPriority.HIGH, RecommendationPriority.CRITICAL]
            )
        )
    return int(db.scalar(stmt) or 0)


# ---------------------------------------------------------------------------
# Overviews
# ---------------------------------------------------------------------------


def get_zone_overview(
    db: Session, zone_id: int, start: datetime, end: datetime
) -> Optional[ZoneOverview]:
    stmt = select(Zone).options(selectinload(Zone.sensors)).where(Zone.id == zone_id)
    zone = db.scalars(stmt).one_or_none()
    if zone is None:
        return None

    sensor_ids = [s.id for s in zone.sensors]
    latest = _fetch_latest_readings(db, sensor_ids, start, end)
    stats = _fetch_stats(db, sensor_ids, start, end)

    summaries = [_build_sensor_summary(s, zone, latest, stats) for s in zone.sensors]
    overall = combine_statuses([s.status for s in summaries])

    return ZoneOverview(
        zone_id=zone.id,
        greenhouse_id=zone.greenhouse_id,
        name=zone.name,
        crop_type=zone.crop_type,
        overall_status=overall,
        readings=summaries,
    )


def get_greenhouse_overview(
    db: Session, greenhouse_id: int, start: datetime, end: datetime
) -> Optional[GreenhouseOverview]:
    stmt = (
        select(Greenhouse)
        .options(selectinload(Greenhouse.zones).selectinload(Zone.sensors))
        .where(Greenhouse.id == greenhouse_id)
    )
    gh = db.scalars(stmt).one_or_none()
    if gh is None:
        return None

    sensor_ids = [s.id for z in gh.zones for s in z.sensors]
    latest = _fetch_latest_readings(db, sensor_ids, start, end)
    stats = _fetch_stats(db, sensor_ids, start, end)

    zones_out: list[ZoneOverview] = []
    for zone in gh.zones:
        summaries = [_build_sensor_summary(s, zone, latest, stats) for s in zone.sensors]
        zones_out.append(
            ZoneOverview(
                zone_id=zone.id,
                greenhouse_id=gh.id,
                name=zone.name,
                crop_type=zone.crop_type,
                overall_status=combine_statuses([s.status for s in summaries]),
                readings=summaries,
            )
        )

    overall = combine_statuses([z.overall_status for z in zones_out])

    open_alert_count = _count_open_alerts(db, greenhouse_id)
    critical_alert_count = _count_open_alerts(db, greenhouse_id, AlertSeverity.CRITICAL)
    open_rec_count = _count_open_recommendations(db, greenhouse_id)
    high_priority_rec_count = _count_open_recommendations(
        db, greenhouse_id, min_priority="high"
    )

    return GreenhouseOverview(
        greenhouse_id=gh.id,
        name=gh.name,
        location=gh.location,
        overall_status=overall,
        window_start=start,
        window_end=end,
        zones=zones_out,
        open_alerts_count=open_alert_count,
        critical_alerts_count=critical_alert_count,
        open_recommendations_count=open_rec_count,
        high_priority_recommendations_count=high_priority_rec_count,
    )


# ---------------------------------------------------------------------------
# Latest readings
# ---------------------------------------------------------------------------


def get_latest_readings(
    db: Session, greenhouse_id: int
) -> Optional[LatestReadingsResponse]:
    exists = db.scalar(select(Greenhouse.id).where(Greenhouse.id == greenhouse_id))
    if exists is None:
        return None

    stmt = (
        select(
            Sensor.id.label("sensor_pk"),
            Sensor.zone_id,
            Sensor.sensor_type,
            Sensor.unit,
            SensorReading.timestamp,
            SensorReading.value,
        )
        .join(Sensor, SensorReading.sensor_id == Sensor.id)
        .join(Zone, Sensor.zone_id == Zone.id)
        .where(Zone.greenhouse_id == greenhouse_id)
        .distinct(SensorReading.sensor_id)
        .order_by(SensorReading.sensor_id, SensorReading.timestamp.desc())
    )
    rows = db.execute(stmt).all()
    return LatestReadingsResponse(
        greenhouse_id=greenhouse_id,
        readings=[
            LatestReading(
                sensor_id=row.sensor_pk,
                zone_id=row.zone_id,
                sensor_type=row.sensor_type,
                unit=row.unit,
                value=float(row.value),
                timestamp=row.timestamp,
            )
            for row in rows
        ],
    )


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


def _history_query(
    sensor_ids_filter: Any,
    start: Optional[datetime],
    end: Optional[datetime],
    limit: int,
    offset: int,
):
    stmt = (
        select(
            SensorReading.id,
            SensorReading.sensor_id,
            SensorReading.timestamp,
            SensorReading.value,
        )
        .where(sensor_ids_filter)
    )
    if start is not None:
        stmt = stmt.where(SensorReading.timestamp >= start)
    if end is not None:
        stmt = stmt.where(SensorReading.timestamp <= end)
    return stmt.order_by(SensorReading.timestamp.desc()).limit(limit).offset(offset)


def get_sensor_history(
    db: Session,
    sensor_id: int,
    start: Optional[datetime],
    end: Optional[datetime],
    limit: int,
    offset: int,
) -> Optional[HistoryResponse]:
    sensor = db.get(Sensor, sensor_id)
    if sensor is None:
        return None

    stmt = _history_query(
        SensorReading.sensor_id == sensor_id, start, end, limit, offset
    )
    rows = db.execute(stmt).all()
    return HistoryResponse(
        readings=[
            ReadingOut(
                id=row.id,
                sensor_id=row.sensor_id,
                timestamp=row.timestamp,
                value=float(row.value),
            )
            for row in rows
        ],
        count=len(rows),
        limit=limit,
        offset=offset,
        start_time=start,
        end_time=end,
    )


def get_greenhouse_history(
    db: Session,
    greenhouse_id: int,
    start: Optional[datetime],
    end: Optional[datetime],
    sensor_type: Optional[SensorType],
    limit: int,
    offset: int,
) -> Optional[HistoryResponse]:
    exists = db.scalar(select(Greenhouse.id).where(Greenhouse.id == greenhouse_id))
    if exists is None:
        return None

    sensor_subq = (
        select(Sensor.id)
        .join(Zone, Sensor.zone_id == Zone.id)
        .where(Zone.greenhouse_id == greenhouse_id)
    )
    if sensor_type is not None:
        sensor_subq = sensor_subq.where(Sensor.sensor_type == sensor_type)

    stmt = _history_query(
        SensorReading.sensor_id.in_(sensor_subq), start, end, limit, offset
    )
    rows = db.execute(stmt).all()
    return HistoryResponse(
        readings=[
            ReadingOut(
                id=row.id,
                sensor_id=row.sensor_id,
                timestamp=row.timestamp,
                value=float(row.value),
            )
            for row in rows
        ],
        count=len(rows),
        limit=limit,
        offset=offset,
        start_time=start,
        end_time=end,
    )