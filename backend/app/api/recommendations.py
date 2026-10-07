from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status as http_status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import any_user, require_agronomist
from app.models.user import User
from app.models.enums import RecommendationPriority, RecommendationStatus
from app.models.recommendation import Recommendation
from app.schemas.recommendation import (
    RecommendationListResponse,
    RecommendationRead,
)
from app.services import recommendation_service

router = APIRouter(tags=["recommendations"])


def _base_query(
    greenhouse_id: Optional[int],
    zone_id: Optional[int],
    priority: Optional[RecommendationPriority],
    status_: Optional[RecommendationStatus],
):
    stmt = select(Recommendation)
    if greenhouse_id is not None:
        stmt = stmt.where(Recommendation.greenhouse_id == greenhouse_id)
    if zone_id is not None:
        stmt = stmt.where(Recommendation.zone_id == zone_id)
    if priority is not None:
        stmt = stmt.where(Recommendation.priority == priority)
    if status_ is not None:
        stmt = stmt.where(Recommendation.status == status_)
    return stmt


@router.get("/recommendations", response_model=RecommendationListResponse)
def list_recommendations(
    greenhouse_id: Optional[int] = Query(None),
    zone_id: Optional[int] = Query(None),
    priority: Optional[RecommendationPriority] = Query(None),
    status: Optional[RecommendationStatus] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> RecommendationListResponse:
    base = _base_query(greenhouse_id, zone_id, priority, status)
    total = db.scalar(
        select(func.count()).select_from(base.subquery())
    ) or 0
    rows = db.scalars(
        base.order_by(
            Recommendation.created_at.desc(), Recommendation.id.desc()
        ).limit(limit).offset(offset)
    ).all()
    return RecommendationListResponse(
        recommendations=[RecommendationRead.model_validate(r) for r in rows],
        total=int(total),
        limit=limit,
        offset=offset,
    )


@router.get(
    "/greenhouses/{greenhouse_id}/recommendations",
    response_model=RecommendationListResponse,
)
def list_greenhouse_recommendations(
    greenhouse_id: int,
    priority: Optional[RecommendationPriority] = Query(None),
    status: Optional[RecommendationStatus] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    _user: User = Depends(any_user),
) -> RecommendationListResponse:
    return list_recommendations(
        greenhouse_id=greenhouse_id,
        zone_id=None,
        priority=priority,
        status=status,
        limit=limit,
        offset=offset,
        db=db,
    )


def _get(db: Session, rec_id: int) -> Recommendation:
    rec = db.get(Recommendation, rec_id)
    if rec is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {rec_id} not found",
        )
    return rec


@router.post("/recommendations/{rec_id}/dismiss", response_model=RecommendationRead)
def dismiss(
    rec_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_agronomist),
) -> RecommendationRead:
    rec = recommendation_service.dismiss(db, rec_id)
    if rec is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {rec_id} not found",
        )
    return RecommendationRead.model_validate(rec)


@router.post("/recommendations/{rec_id}/complete", response_model=RecommendationRead)
def complete(
    rec_id: int,
    db: Session = Depends(get_db),
    _user: User = Depends(require_agronomist),
) -> RecommendationRead:
    rec = recommendation_service.complete(db, rec_id)
    if rec is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Recommendation {rec_id} not found",
        )
    return RecommendationRead.model_validate(rec)