from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.sensor import Sensor
from app.models.zone import Zone


def get_zone(db: Session, zone_id: int) -> Optional[Zone]:
    return db.get(Zone, zone_id)


def list_sensors(db: Session, zone_id: int) -> List[Sensor]:
    stmt = select(Sensor).where(Sensor.zone_id == zone_id).order_by(Sensor.id)
    return list(db.scalars(stmt).all())