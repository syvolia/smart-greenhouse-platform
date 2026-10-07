"""Statistical anomaly detection, decoupled from threshold rules.

The `AnomalyDetector` protocol lets us swap in an ML-backed detector later
without touching call sites.
"""
import logging
import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor_reading import SensorReading

logger = logging.getLogger(__name__)


@dataclass
class AnomalyResult:
    sensor_id: int
    is_anomaly: bool
    z_score: Optional[float]
    current_value: Optional[float]
    mean: Optional[float]
    std: Optional[float]


class AnomalyDetector(Protocol):
    def detect(
        self,
        sensor_id: int,
        readings: list[tuple[datetime, float]],
    ) -> AnomalyResult: ...


class ZScoreDetector:
    """Rolling z-score detector.

    `readings` must be sorted newest-first. The most recent point is scored
    against the previous `window` points.
    """

    def __init__(self, window: int, threshold: float) -> None:
        self.window = window
        self.threshold = threshold

    def detect(
        self,
        sensor_id: int,
        readings: list[tuple[datetime, float]],
    ) -> AnomalyResult:
        if len(readings) < 10:
            return AnomalyResult(sensor_id, False, None, None, None, None)

        current_value = readings[0][1]
        historical = [v for _, v in readings[1 : self.window + 1]]
        if len(historical) < 5:
            return AnomalyResult(sensor_id, False, None, current_value, None, None)

        mean = statistics.fmean(historical)
        std = statistics.pstdev(historical)
        if std < 1e-9:
            z = 0.0
        else:
            z = (current_value - mean) / std

        return AnomalyResult(
            sensor_id=sensor_id,
            is_anomaly=abs(z) > self.threshold,
            z_score=z,
            current_value=current_value,
            mean=mean,
            std=std,
        )


def fetch_recent_readings_grouped(
    db: Session,
    sensor_ids: list[int],
    window: int,
    max_age_hours: int = 24,
) -> dict[int, list[tuple[datetime, float]]]:
    """Return {sensor_id: [(ts, value), ...]} newest-first, at most `window` per sensor.

    Uses a single window-function query to avoid N+1.
    """
    if not sensor_ids:
        return {}

    cutoff = datetime.now(timezone.utc) - timedelta(hours=max_age_hours)

    # Portable approach: one query per sensor is simpler, but for 72 sensors
    # we prefer a single windowed query.
    from sqlalchemy import text as sql_text

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
        WHERE rn <= :window
        ORDER BY sensor_id, rn
        """
    )
    rows = db.execute(
        sql, {"ids": sensor_ids, "cutoff": cutoff, "window": window}
    ).all()

    out: dict[int, list[tuple[datetime, float]]] = {}
    for r in rows:
        out.setdefault(r.sensor_id, []).append((r.timestamp, float(r.value)))
    return out