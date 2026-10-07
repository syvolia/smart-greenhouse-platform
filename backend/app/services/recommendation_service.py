"""Persists recommendations produced by the rule engine.

Flow:
  1. Build a RecommendationContext for the affected zones.
  2. Optionally enrich it with ML-predicted yields (best-effort).
  3. Run every registered rule; collect candidate recommendations.
  4. Upsert against existing OPEN recommendations (dedup on scope + type).
  5. Auto-complete OPEN recommendations whose underlying condition no longer
     holds (i.e., no rule produced a candidate for that scope + type).
"""
import logging
from datetime import datetime, timezone
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.models.enums import (
    RecommendationStatus,
    SensorType,
)
from app.models.recommendation import Recommendation
from app.services.recommendation_engine import RULES, RecommendationContext
from app.services.recommendation_engine.base import CandidateRecommendation
from app.services.recommendation_engine.context import build_context

logger = logging.getLogger(__name__)

_OPEN = (RecommendationStatus.OPEN,)


# ---------------------------------------------------------------------------
# ML enrichment (best-effort, never blocking)
# ---------------------------------------------------------------------------


def _enrich_with_ml(ctx: RecommendationContext) -> None:
    """Populate ctx.predicted_yield_by_zone by calling the ML service on
    each zone's current averaged conditions. Failures are logged and skipped.
    """
    try:
        from app.schemas.ml import YieldPredictionRequest  # local import
        from app.services import ml_service
    except Exception as exc:  # noqa: BLE001
        logger.warning("ML enrichment disabled: %s", exc)
        return

    predictions: dict[int, float] = {}
    model_version = "unknown"
    for zone in ctx.zones:
        temp = zone.sensor(SensorType.TEMPERATURE)
        hum = zone.sensor(SensorType.HUMIDITY)
        soil = zone.sensor(SensorType.SOIL_MOISTURE)
        co2 = zone.sensor(SensorType.CO2)
        light = zone.sensor(SensorType.LIGHT)
        if not (temp and hum and soil and temp.current_value is not None):
            continue
        try:
            req = YieldPredictionRequest(
                crop_type=zone.crop_type.capitalize() if zone.crop_type else "Tomato",
                avg_temperature_C=float(temp.current_value or 22.0),
                min_temperature_C=float(temp.current_value or 22.0) - 5.0,
                max_temperature_C=float(temp.current_value or 22.0) + 5.0,
                humidity_percent=float(hum.current_value or 70.0) if hum else 70.0,
                co2_ppm=float(co2.current_value or 800.0) if co2 else 800.0,
                light_intensity_lux=float(light.current_value or 20000.0) if light else 20000.0,
                photoperiod_hours=14.0,
                irrigation_mm=5.0,
                fertilizer_N_kg_ha=120.0,
                fertilizer_P_kg_ha=60.0,
                fertilizer_K_kg_ha=80.0,
                pest_severity=2.0,
                soil_pH=6.5,
                days_to_maturity=90,
            )
            result = ml_service.predict_yield(req)
            predictions[zone.id] = float(result["predicted_yield_kg_per_m2"])
            model_version = str(result.get("model_version", model_version))
        except Exception as exc:  # noqa: BLE001
            logger.debug("Yield prediction failed for zone %s: %s", zone.id, exc)

    ctx.predicted_yield_by_zone = predictions
    ctx.model_version = model_version


# ---------------------------------------------------------------------------
# Upsert helpers
# ---------------------------------------------------------------------------


def _scope_key(gh_id: int, zone_id: int | None, rtype) -> tuple[int, int, str]:
    return (gh_id, zone_id or 0, rtype.value)


def _load_open(
    db: Session, greenhouse_ids: set[int]
) -> dict[tuple[int, int, str], Recommendation]:
    if not greenhouse_ids:
        return {}
    rows = db.scalars(
        select(Recommendation).where(
            Recommendation.greenhouse_id.in_(greenhouse_ids),
            Recommendation.status == RecommendationStatus.OPEN,
        )
    ).all()
    return {
        _scope_key(r.greenhouse_id, r.zone_id, r.recommendation_type): r
        for r in rows
    }


def _upsert(
    db: Session,
    existing: dict[tuple[int, int, str], Recommendation],
    cand: CandidateRecommendation,
) -> None:
    key = _scope_key(cand.greenhouse_id, cand.zone_id, cand.recommendation_type)
    current = existing.get(key)
    if current is not None:
        # Update in place — priority/message/reason may have evolved.
        current.priority = cand.priority
        current.message = cand.message
        current.reason = cand.reason
        current.sensor_id = cand.sensor_id
        return
    new = Recommendation(
        greenhouse_id=cand.greenhouse_id,
        zone_id=cand.zone_id,
        sensor_id=cand.sensor_id,
        recommendation_type=cand.recommendation_type,
        priority=cand.priority,
        message=cand.message,
        reason=cand.reason,
        status=RecommendationStatus.OPEN,
    )
    db.add(new)
    existing[key] = new


def _auto_complete(
    existing: dict[tuple[int, int, str], Recommendation],
    produced_keys: set[tuple[int, int, str]],
) -> int:
    """Close OPEN recommendations whose conditions no longer hold."""
    now = datetime.now(timezone.utc)
    closed = 0
    for key, rec in existing.items():
        if key in produced_keys:
            continue
        rec.status = RecommendationStatus.COMPLETED
        rec.resolved_at = now
        closed += 1
    return closed


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def evaluate_zones(db: Session, zone_ids: list[int]) -> dict[str, int]:
    """Run the engine against the given zones. Idempotent."""
    if not settings.recommendation_evaluation_enabled or not zone_ids:
        return {"produced": 0, "created": 0, "updated": 0, "closed": 0}

    ctx = build_context(db, zone_ids)
    if not ctx.zones:
        return {"produced": 0, "created": 0, "updated": 0, "closed": 0}

    _enrich_with_ml(ctx)

    candidates: list[CandidateRecommendation] = []
    for rule in RULES:
        try:
            candidates.extend(rule.evaluate(ctx))
        except Exception:  # noqa: BLE001
            logger.exception("Rule %s failed", getattr(rule, "name", "?"))

    greenhouse_ids = {z.greenhouse_id for z in ctx.zones}
    existing = _load_open(db, greenhouse_ids)
    pre_existing_ids = {id(r) for r in existing.values()}

    produced_keys: set[tuple[int, int, str]] = set()
    for cand in candidates:
        _upsert(db, existing, cand)
        produced_keys.add(
            _scope_key(cand.greenhouse_id, cand.zone_id, cand.recommendation_type)
        )

    closed = _auto_complete(existing, produced_keys)
    db.commit()

    created = sum(
        1 for r in existing.values() if id(r) not in pre_existing_ids
    )
    updated = len(produced_keys) - created

    stats = {
        "produced": len(produced_keys),
        "created": created,
        "updated": max(0, updated),
        "closed": closed,
    }
    logger.info(
        "Recommendation engine: produced=%d created=%d updated=%d closed=%d",
        stats["produced"], stats["created"], stats["updated"], stats["closed"],
    )
    return stats


def dismiss(db: Session, recommendation_id: int) -> Recommendation | None:
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        return None
    if rec.status == RecommendationStatus.OPEN:
        rec.status = RecommendationStatus.DISMISSED
        rec.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
    return rec


def complete(db: Session, recommendation_id: int) -> Recommendation | None:
    rec = db.get(Recommendation, recommendation_id)
    if rec is None:
        return None
    if rec.status == RecommendationStatus.OPEN:
        rec.status = RecommendationStatus.COMPLETED
        rec.resolved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(rec)
    return rec


def zone_ids_for_sensors(db: Session, sensor_ids: list[int]) -> list[int]:
    if not sensor_ids:
        return []
    from app.models.sensor import Sensor

    return sorted(
        set(db.scalars(select(Sensor.zone_id).where(Sensor.id.in_(sensor_ids))).all())
    )