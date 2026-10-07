"""Idempotent development seed for the greenhouse topology.

Runs inside the backend container:

    docker compose exec backend python -m app.db.seed

Creates:
    3 greenhouses x 4 zones x 6 sensors = 72 sensors
"""
import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.enums import GreenhouseStatus, SensorStatus, SensorType
from app.models.greenhouse import Greenhouse
from app.models.sensor import Sensor
from app.models.zone import Zone

logger = logging.getLogger(__name__)

GREENHOUSES = [
    {"name": "Greenhouse Alpha", "location": "Naivasha, Kenya"},
    {"name": "Greenhouse Beta", "location": "Nakuru, Kenya"},
    {"name": "Greenhouse Gamma", "location": "Kajiado, Kenya"},
]

ZONE_NAMES = ["Zone A", "Zone B", "Zone C", "Zone D"]

# Realistic tomato greenhouse targets
TOMATO_TARGETS = {
    "target_temperature_min": 18.0,
    "target_temperature_max": 26.0,
    "target_humidity_min": 60.0,
    "target_humidity_max": 80.0,
    "target_soil_moisture_min": 55.0,
    "target_soil_moisture_max": 75.0,
}

SENSOR_UNITS = {
    SensorType.TEMPERATURE: "\u00b0C",
    SensorType.HUMIDITY: "%",
    SensorType.SOIL_MOISTURE: "%",
    SensorType.LIGHT: "lux",
    SensorType.CO2: "ppm",
    SensorType.IRRIGATION: "L/min",
}


def seed(db: Session) -> None:
    """Insert seed data if the greenhouses table is empty (idempotent)."""
    if db.scalar(select(Greenhouse).limit(1)) is not None:
        logger.info("Seed skipped: greenhouses already exist")
        return

    for gh in GREENHOUSES:
        greenhouse = Greenhouse(
            name=gh["name"],
            location=gh["location"],
            status=GreenhouseStatus.ACTIVE,
        )
        db.add(greenhouse)
        db.flush()  # assign id

        for zone_name in ZONE_NAMES:
            zone = Zone(
                greenhouse_id=greenhouse.id,
                name=zone_name,
                crop_type="tomato",
                **TOMATO_TARGETS,
            )
            db.add(zone)
            db.flush()  # assign id

            for sensor_type, unit in SENSOR_UNITS.items():
                db.add(
                    Sensor(
                        zone_id=zone.id,
                        sensor_type=sensor_type,
                        unit=unit,
                        status=SensorStatus.ACTIVE,
                    )
                )

    db.commit()
    logger.info(
        "Seed complete: %d greenhouses, %d zones, %d sensors",
        len(GREENHOUSES),
        len(GREENHOUSES) * len(ZONE_NAMES),
        len(GREENHOUSES) * len(ZONE_NAMES) * len(SENSOR_UNITS),
    )


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    )
    with SessionLocal() as db:
        seed(db)


if __name__ == "__main__":
    main()