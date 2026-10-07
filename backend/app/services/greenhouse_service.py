from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.greenhouse import Greenhouse
from app.models.zone import Zone


def list_greenhouses(db: Session) -> List[Greenhouse]:
    return list(db.scalars(select(Greenhouse).order_by(Greenhouse.id)).all())


def get_greenhouse(db: Session, greenhouse_id: int) -> Optional[Greenhouse]:
    return db.get(Greenhouse, greenhouse_id)


def list_zones(db: Session, greenhouse_id: int) -> List[Zone]:
    stmt = (
        select(Zone)
        .where(Zone.greenhouse_id == greenhouse_id)
        .order_by(Zone.id)
    )
    return list(db.scalars(stmt).all())