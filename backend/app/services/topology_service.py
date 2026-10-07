from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.greenhouse import Greenhouse
from app.models.zone import Zone


def get_topology(db: Session) -> List[Greenhouse]:
    """Return the full greenhouse -> zone -> sensor hierarchy.

    Uses selectinload to issue exactly 3 queries regardless of hierarchy size
    (one per level), avoiding N+1.
    """
    stmt = (
        select(Greenhouse)
        .options(selectinload(Greenhouse.zones).selectinload(Zone.sensors))
        .order_by(Greenhouse.id)
    )
    return list(db.scalars(stmt).all())