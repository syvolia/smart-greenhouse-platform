import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.config import settings
from app.models.alert import Alert
from app.models.enums import (
    AlertSeverity,
    AlertStatus,
    AlertType,
    SensorType,
)
from app.models.sensor import Sensor
from app.models.zone import Zone
from app.schemas.analytics import EnvironmentalStatus
from app.services.analytics_service import (
    ZONE_TARGET_FIELDS,
    classify_status,
    _fetch_latest_readings,
)
from app.services.anomaly_service import (
    ZScoreDetector,
    fetch_recent_readings_grouped,
)

logger = logging.getLogger(__name__)

_OPEN_STATES = (AlertStatus.OPEN, AlertStatus.ACKNOWLEDGED)


# ---------------------------------------------------------------------------
# Range resolution
# ---------------------------------------------------------------------------


def _zone_range(sensor_type: SensorType, zone: Zone) -> tuple[Optional[float], Optional[float]]:
    fields = ZONE_TARGET_FIELDS.get(sensor_type)
    if fields is None:
        return None, None
    lo = getattr(zone, fields[0], None)
    hi = getattr(zone, fields[1], None)
    return (
        float(lo) if lo is not None else None,
        float(hi) if hi is not None else None,
    )


def _global_range(sensor_type: SensorType) -> tuple[Optional[float], Optional[float]]:
    if sensor_type == SensorType.CO2:
        return float(settings.alert_co2_min_ppm), float(settings.alert_co2_max_ppm)
    return None, None


def _resolve_range(sensor_type: SensorType, zone: Zone) -> tuple[Optional[float], Optional[float]]:
    lo, hi = _zone_range(sensor_type, zone)
    if lo is None or hi is None:
        return _global_range(sensor_type)
    return lo, hi


# ---------------------------------------------------------------------------
# Alert upsert / resolve
# ---------------------------------------------------------------------------


def _upsert_open_alert(
    db: Session,
    existing_by_key: dict[tuple[int, AlertType], Alert],
    *,
    sensor: Sensor,
    alert_type: AlertType,
    severity: AlertSeverity,
    message: str,
    value: float,
    threshold: str,
) -> None:
    key = (sensor.id, alert_type)
    alert = existing_by_key.get(key)
    if alert is not None:
        alert.severity = severity
        alert.message = message
        alert.value = Decimal(str(round(value, 4)))
        alert.threshold = threshold
        return
    new_alert = Alert(
        greenhouse_id=sensor.zone.greenhouse_id,
        zone_id=sensor.zone_id,
        sensor_id=sensor.id,
        alert_type=alert_type,
        severity=severity,
        status=AlertStatus.OPEN,
        message=message,
        value=Decimal(str(round(value, 4))),
        threshold=threshold,
    )
    db.add(new_alert)
    existing_by_key[key] = new_alert


def _resolve_open_alert(
    existing_by_key: dict[tuple[int, AlertType], Alert],
    sensor_id: int,
    alert_type: AlertType,
) -> None:
    alert = existing_by_key.get((sensor_id, alert_type))
    if alert is None:
        return
    alert.status = AlertStatus.RESOLVED
    alert.resolved_at = datetime.now(timezone.utc)
    # remove from active set so subsequent upserts don't reuse it
    existing_by_key.pop((sensor_id, alert_type), None)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def load_open_alerts_for_sensors(
    db: Session, sensor_ids: list[int]
) -> dict[tuple[int, AlertType], Alert]:
    if not sensor_ids:
        return {}
    rows = db.scalars(
        select(Alert).where(
            Alert.sensor_id.in_(sensor_ids),
            Alert.status.in_(_OPEN_STATES),
        )
    ).all()
    return {(a.sensor_id, a.alert_type): a for a in rows}


def evaluate_sensors(db: Session, sensor_ids: list[int]) -> None:
    """Run rule-based + anomaly checks on the given sensors and persist
    any resulting alerts. Idempotent: repeated calls with the same data
    don't create duplicate alerts.
    """
    if not settings.alert_evaluation_enabled or not sensor_ids:
        return

    sensors = db.scalars(
        select(Sensor)
        .options(selectinload(Sensor.zone))
        .where(Sensor.id.in_(sensor_ids))
    ).all()
    if not sensors:
        return

    existing = load_open_alerts_for_sensors(db, sensor_ids)

    # --- Threshold rules ---
    latest = _fetch_latest_readings(
        db, sensor_ids, datetime(1970, 1, 1, tzinfo=timezone.utc),
        datetime.now(timezone.utc) + __import__("datetime").timedelta(days=1),
    )

    for sensor in sensors:
        row = latest.get(sensor.id)
        if row is None:
            continue
        _, value = row

        lo, hi = _resolve_range(sensor.sensor_type, sensor.zone)
        if lo is None or hi is None:
            continue

        status, deviation = classify_status(value, lo, hi)
        threshold_str = f"{lo}–{hi} {sensor.unit}"

        if status in (EnvironmentalStatus.NORMAL, EnvironmentalStatus.UNKNOWN):
            _resolve_open_alert(existing, sensor.id, AlertType.THRESHOLD_HIGH)
            _resolve_open_alert(existing, sensor.id, AlertType.THRESHOLD_LOW)
            continue

        if value > hi:
            alert_type = AlertType.THRESHOLD_HIGH
            direction = "above"
            boundary = hi
            opposite = AlertType.THRESHOLD_LOW
        else:
            alert_type = AlertType.THRESHOLD_LOW
            direction = "below"
            boundary = lo
            opposite = AlertType.THRESHOLD_HIGH

        _resolve_open_alert(existing, sensor.id, opposite)

        severity = (
            AlertSeverity.WARNING
            if status == EnvironmentalStatus.WARNING
            else AlertSeverity.CRITICAL
        )
        label = sensor.sensor_type.value.replace("_", " ").title()
        message = (
            f"{label} {value}{sensor.unit} is {direction} "
            f"target {boundary}{sensor.unit}"
        )
        _upsert_open_alert(
            db, existing,
            sensor=sensor,
            alert_type=alert_type,
            severity=severity,
            message=message,
            value=value,
            threshold=threshold_str,
        )

    # --- Anomaly detection ---
    window = settings.anomaly_window_size
    threshold = settings.anomaly_zscore_threshold
    detector = ZScoreDetector(window=window, threshold=threshold)
    grouped = fetch_recent_readings_grouped(db, sensor_ids, window)

    sensor_by_id = {s.id: s for s in sensors}
    for sid, readings in grouped.items():
        sensor = sensor_by_id.get(sid)
        if sensor is None:
            continue
        result = detector.detect(sensor_id=sid, readings=readings)
        if result.is_anomaly:
            label = sensor.sensor_type.value.replace("_", " ").title()
            message = (
                f"{label} {result.current_value}{sensor.unit} is a statistical "
                f"anomaly (z={result.z_score:.2f})"
            )
            _upsert_open_alert(
                db, existing,
                sensor=sensor,
                alert_type=AlertType.ANOMALY,
                severity=AlertSeverity.WARNING,
                message=message,
                value=float(result.current_value or 0.0),
                threshold=f"z>{threshold}",
            )
        else:
            _resolve_open_alert(existing, sid, AlertType.ANOMALY)

    db.commit()
    logger.info("Alert evaluation completed for %d sensors", len(sensors))