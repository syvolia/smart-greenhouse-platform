from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import any_user
from app.models.user import User
from app.schemas.greenhouse import GreenhouseRead
from app.schemas.zone import ZoneRead
from app.services import greenhouse_service

router = APIRouter(prefix="/greenhouses", tags=["greenhouses"])


@router.get("", response_model=list[GreenhouseRead])
def list_greenhouses(
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> list[GreenhouseRead]:
    return greenhouse_service.list_greenhouses(db)


@router.get("/{greenhouse_id}", response_model=GreenhouseRead)
def get_greenhouse(
    greenhouse_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> GreenhouseRead:
    gh = greenhouse_service.get_greenhouse(db, greenhouse_id)
    if gh is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greenhouse {greenhouse_id} not found",
        )
    return gh


@router.get("/{greenhouse_id}/zones", response_model=list[ZoneRead])
def list_greenhouse_zones(
    greenhouse_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> list[ZoneRead]:
    gh = greenhouse_service.get_greenhouse(db, greenhouse_id)
    if gh is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greenhouse {greenhouse_id} not found",
        )
    return greenhouse_service.list_zones(db, greenhouse_id)