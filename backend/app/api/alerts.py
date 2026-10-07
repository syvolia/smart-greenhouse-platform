from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import any_user, require_agronomist
from app.models.alert import Alert
from app.models.enums import AlertSeverity, AlertStatus
from app.models.user import User
from app.schemas.alert import AlertListResponse, AlertRead

router = APIRouter(tags=["alerts"])


def _base_query(
    greenhouse_id: Optional[int],
    severity: Optional[AlertSeverity],
    status_: Optional[AlertStatus],
):
    stmt = select(Alert)
    if greenhouse_id is not None:
        stmt = stmt.where(Alert.greenhouse_id == greenhouse_id)
    if severity is not None:
        stmt = stmt.where(Alert.severity == severity)
    if status_ is not None:
        stmt = stmt.where(Alert.status == status_)
    return stmt


@router.get("/alerts", response_model=AlertListResponse)
def list_alerts(
    greenhouse_id: Optional[int] = Query(None),
    severity: Optional[AlertSeverity] = Query(None),
    status: Optional[AlertStatus] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> AlertListResponse:
    total = db.scalar(
        select(func.count()).select_from(
            _base_query(greenhouse_id, severity, status).subquery()
        )
    ) or 0
    rows = db.scalars(
        _base_query(greenhouse_id, severity, status)
        .order_by(Alert.created_at.desc())
        .limit(limit)
        .offset(offset)
    ).all()
    return AlertListResponse(
        alerts=[AlertRead.model_validate(a) for a in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/greenhouses/{greenhouse_id}/alerts", response_model=AlertListResponse
)
def list_greenhouse_alerts(
    greenhouse_id: int,
    severity: Optional[AlertSeverity] = Query(None),
    status: Optional[AlertStatus] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> AlertListResponse:
    return list_alerts(
        greenhouse_id=greenhouse_id,
        severity=severity,
        status=status,
        limit=limit,
        offset=offset,
        db=db,
        _user=_user,
    )


def _get_alert(db: Session, alert_id: int) -> Alert:
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Alert {alert_id} not found",
        )
    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertRead)
def acknowledge_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_agronomist),
) -> AlertRead:
    from datetime import datetime, timezone

    alert = _get_alert(db, alert_id)
    if alert.status == AlertStatus.OPEN:
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return AlertRead.model_validate(alert)


@router.post("/alerts/{alert_id}/resolve", response_model=AlertRead)
def resolve_alert(
    alert_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_agronomist),
) -> AlertRead:
    from datetime import datetime, timezone

    alert = _get_alert(db, alert_id)
    if alert.status != AlertStatus.RESOLVED:
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(alert)
    return AlertRead.model_validate(alert)