from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import any_user
from app.models.user import User
from app.schemas.sensor import SensorRead
from app.services import zone_service

router = APIRouter(prefix="/zones", tags=["zones"])


@router.get("/{zone_id}/sensors", response_model=list[SensorRead])
def list_zone_sensors(
    zone_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> list[SensorRead]:
    zone = zone_service.get_zone(db, zone_id)
    if zone is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found",
        )
    return zone_service.list_sensors(db, zone_id)