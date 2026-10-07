import logging
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.models.sensor import Sensor
from app.models.sensor_reading import SensorReading
from app.schemas.ingestion import SensorReadingCreate

logger = logging.getLogger(__name__)


def ingest_batch(
    db: Session, readings: List[SensorReadingCreate]
) -> Dict[str, int]:
    """Batch-ingest sensor readings with idempotency.

    - Rejects readings whose sensor_id does not exist.
    - Uses Postgres ON CONFLICT DO NOTHING on (sensor_id, timestamp) so
      re-sending the same batch is a no-op rather than a duplicate error.
    - After commit, triggers alert + recommendation evaluation for affected
      sensors only. Both evaluations are isolated: a failure in either never
      fails the ingestion request.

    Invariant: received == inserted + rejected + duplicates
    """
    received = len(readings)
    if received == 0:
        return {"received": 0, "inserted": 0, "rejected": 0, "duplicates": 0}

    requested_ids = {r.sensor_id for r in readings}
    existing_ids = set(
        db.scalars(select(Sensor.id).where(Sensor.id.in_(requested_ids))).all()
    )

    valid_rows = [
        {
            "sensor_id": r.sensor_id,
            "timestamp": r.timestamp,
            "value": r.value,
        }
        for r in readings
        if r.sensor_id in existing_ids
    ]
    rejected = received - len(valid_rows)

    if not valid_rows:
        return {
            "received": received,
            "inserted": 0,
            "rejected": rejected,
            "duplicates": 0,
        }

    stmt = (
        pg_insert(SensorReading)
        .values(valid_rows)
        .on_conflict_do_nothing(
            index_elements=["sensor_id", "timestamp"]
        )
        .returning(SensorReading.id)
    )
    result = db.execute(stmt)
    inserted = len(result.fetchall())
    db.commit()
    duplicates = len(valid_rows) - inserted

    stats = {
        "received": received,
        "inserted": inserted,
        "rejected": rejected,
        "duplicates": duplicates,
    }
    logger.info(
        "Ingestion: received=%d inserted=%d rejected=%d duplicates=%d",
        stats["received"], stats["inserted"], stats["rejected"], stats["duplicates"],
    )

    affected_sensor_ids = sorted(
        {r.sensor_id for r in readings if r.sensor_id in existing_ids}
    )

    # --- Alert evaluation (Phase 6) ---
    try:
        from app.services.alert_service import evaluate_sensors

        if affected_sensor_ids:
            evaluate_sensors(db, affected_sensor_ids)
    except Exception:  # noqa: BLE001
        logger.exception("Alert evaluation failed (ingestion already succeeded)")

    # --- Recommendation engine (Phase 10) ---
    try:
        from app.services import recommendation_service

        if affected_sensor_ids:
            zone_ids = recommendation_service.zone_ids_for_sensors(
                db, affected_sensor_ids
            )
            if zone_ids:
                recommendation_service.evaluate_zones(db, zone_ids)
    except Exception:  # noqa: BLE001
        logger.exception(
            "Recommendation engine failed (ingestion already succeeded)"
        )

    return stats