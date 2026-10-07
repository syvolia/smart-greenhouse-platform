from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.dependencies.auth import any_user
from app.models.user import User
from app.models.enums import SensorType
from app.schemas.analytics import (
    GreenhouseOverview,
    HistoryResponse,
    LatestReadingsResponse,
    ZoneOverview,
)
from app.services import analytics_service

router = APIRouter(tags=["analytics"])


def _ensure_utc(dt: datetime) -> datetime:
    """Attach UTC to a naive datetime so comparisons are safe."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _resolve_window(
    start_time: Optional[datetime], end_time: Optional[datetime]
) -> tuple[datetime, datetime]:
    end = _ensure_utc(end_time) if end_time else datetime.now(timezone.utc)
    start = (
        _ensure_utc(start_time)
        if start_time
        else end - timedelta(hours=settings.analytics_overview_window_hours)
    )
    if start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time must be <= end_time",
        )
    return start, end


@router.get(
    "/greenhouses/{greenhouse_id}/overview",
    response_model=GreenhouseOverview,
)
def greenhouse_overview(
    greenhouse_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    _user: User = Depends(any_user),
    db: Session = Depends(get_db),
) -> GreenhouseOverview:
    start, end = _resolve_window(start_time, end_time)
    result = analytics_service.get_greenhouse_overview(db, greenhouse_id, start, end)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greenhouse {greenhouse_id} not found",
        )
    return result


@router.get("/zones/{zone_id}/overview", response_model=ZoneOverview)
def zone_overview(
    zone_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    _user: User = Depends(any_user),
    db: Session = Depends(get_db),
) -> ZoneOverview:
    start, end = _resolve_window(start_time, end_time)
    result = analytics_service.get_zone_overview(db, zone_id, start, end)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone {zone_id} not found",
        )
    return result


@router.get(
    "/greenhouses/{greenhouse_id}/latest-readings",
    response_model=LatestReadingsResponse,
)
def latest_readings(
    greenhouse_id: int, db: Session = Depends(get_db)
) -> LatestReadingsResponse:
    result = analytics_service.get_latest_readings(db, greenhouse_id)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greenhouse {greenhouse_id} not found",
        )
    return result


@router.get(
    "/greenhouses/{greenhouse_id}/history",
    response_model=HistoryResponse,
)
def greenhouse_history(
    greenhouse_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    sensor_type: Optional[SensorType] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    _user: User = Depends(any_user),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    start = _ensure_utc(start_time) if start_time else None
    end = _ensure_utc(end_time) if end_time else None
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time must be <= end_time",
        )
    result = analytics_service.get_greenhouse_history(
        db, greenhouse_id, start, end, sensor_type, limit, offset
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Greenhouse {greenhouse_id} not found",
        )
    return result


@router.get("/sensors/{sensor_id}/history", response_model=HistoryResponse)
def sensor_history(
    sensor_id: int,
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    _user: User = Depends(any_user),
    db: Session = Depends(get_db),
) -> HistoryResponse:
    start = _ensure_utc(start_time) if start_time else None
    end = _ensure_utc(end_time) if end_time else None
    if start and end and start > end:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time must be <= end_time",
        )
    result = analytics_service.get_sensor_history(
        db, sensor_id, start, end, limit, offset
    )
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sensor {sensor_id} not found",
        )
    return result