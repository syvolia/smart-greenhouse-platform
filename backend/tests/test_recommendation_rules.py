from datetime import datetime, timedelta, timezone

import pytest

from app.models.enums import (
    RecommendationPriority,
    RecommendationType,
    SensorType,
)
from app.services.recommendation_engine.base import CandidateRecommendation
from app.services.recommendation_engine.context import (
    OpenAlertView,
    RecommendationContext,
    SensorView,
    ZoneView,
)
from app.services.recommendation_engine.rules import (
    AnomalyReviewRule,
    CO2OutOfRangeRule,
    HumidityHighRiskRule,
    IrrigationNeededRule,
    TemperatureHighRule,
    TemperatureLowRule,
    YieldRiskRule,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _sensor(
    sid: int,
    zone_id: int,
    sensor_type: SensorType,
    unit: str,
    values_newest_first: list[float],
) -> SensorView:
    now = _now()
    rows = [
        (now - timedelta(seconds=i * 5), v)
        for i, v in enumerate(values_newest_first)
    ]
    return SensorView(
        id=sid,
        zone_id=zone_id,
        sensor_type=sensor_type,
        unit=unit,
        current_value=values_newest_first[0] if values_newest_first else None,
        last_timestamp=rows[0][0] if rows else None,
        recent_values=rows,
    )


def _zone(
    zone_id: int = 1,
    greenhouse_id: int = 1,
    name: str = "Zone A",
    crop_type: str = "tomato",
    temp_range=(18.0, 26.0),
    humidity_range=(60.0, 80.0),
    soil_range=(55.0, 75.0),
    sensors: list[SensorView] | None = None,
) -> ZoneView:
    return ZoneView(
        id=zone_id,
        greenhouse_id=greenhouse_id,
        name=name,
        crop_type=crop_type,
        target_temperature=temp_range,
        target_humidity=humidity_range,
        target_soil_moisture=soil_range,
        sensors=sensors or [],
    )


# ---------------------------------------------------------------------------
# IrrigationNeededRule
# ---------------------------------------------------------------------------


def test_irrigation_needed_high_when_below_min():
    zone = _zone(sensors=[
        _sensor(10, 1, SensorType.SOIL_MOISTURE, "%", [40.0]),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = IrrigationNeededRule().evaluate(ctx)
    assert len(out) == 1
    assert out[0].recommendation_type == RecommendationType.IRRIGATION_NEEDED
    assert out[0].priority == RecommendationPriority.HIGH
    assert out[0].sensor_id == 10


def test_irrigation_needed_critical_when_far_below_min():
    zone = _zone(sensors=[
        _sensor(10, 1, SensorType.SOIL_MOISTURE, "%", [20.0]),  # far below 55
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = IrrigationNeededRule().evaluate(ctx)
    assert out[0].priority == RecommendationPriority.CRITICAL


def test_irrigation_not_needed_when_in_range():
    zone = _zone(sensors=[
        _sensor(10, 1, SensorType.SOIL_MOISTURE, "%", [65.0]),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    assert IrrigationNeededRule().evaluate(ctx) == []


# ---------------------------------------------------------------------------
# TemperatureHighRule / TemperatureLowRule
# ---------------------------------------------------------------------------


def test_temperature_high_requires_sustained_readings():
    # 5 readings all above 26 → recommend
    zone = _zone(sensors=[
        _sensor(20, 1, SensorType.TEMPERATURE, "°C", [28.0] * 5),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = TemperatureHighRule().evaluate(ctx)
    assert len(out) == 1
    assert out[0].recommendation_type == RecommendationType.TEMPERATURE_HIGH


def test_temperature_high_needs_full_window():
    # Only 3 readings, window requires 5 → no recommendation
    zone = _zone(sensors=[
        _sensor(20, 1, SensorType.TEMPERATURE, "°C", [28.0] * 3),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    assert TemperatureHighRule().evaluate(ctx) == []


def test_temperature_high_not_triggered_by_one_spike():
    zone = _zone(sensors=[
        _sensor(20, 1, SensorType.TEMPERATURE, "°C", [28.0, 24.0, 24.0, 24.0, 24.0]),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    assert TemperatureHighRule().evaluate(ctx) == []


def test_temperature_low_sustained():
    zone = _zone(sensors=[
        _sensor(20, 1, SensorType.TEMPERATURE, "°C", [10.0] * 5),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = TemperatureLowRule().evaluate(ctx)
    assert out and out[0].recommendation_type == RecommendationType.TEMPERATURE_LOW


# ---------------------------------------------------------------------------
# HumidityHighRiskRule
# ---------------------------------------------------------------------------


def test_humidity_high_risk_when_above_max():
    zone = _zone(sensors=[
        _sensor(30, 1, SensorType.HUMIDITY, "%", [85.0]),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = HumidityHighRiskRule().evaluate(ctx)
    assert out and "disease" in out[0].message.lower()


def test_humidity_high_risk_critical_when_far_above():
    zone = _zone(sensors=[
        _sensor(30, 1, SensorType.HUMIDITY, "%", [92.0]),  # +12 above 80
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = HumidityHighRiskRule().evaluate(ctx)
    assert out[0].priority == RecommendationPriority.HIGH


# ---------------------------------------------------------------------------
# CO2OutOfRangeRule
# ---------------------------------------------------------------------------


def test_co2_out_of_range_high():
    zone = _zone(sensors=[
        _sensor(40, 1, SensorType.CO2, "ppm", [2500.0]),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    out = CO2OutOfRangeRule().evaluate(ctx)
    assert out and "above" in out[0].message


def test_co2_in_range_no_recommendation():
    zone = _zone(sensors=[
        _sensor(40, 1, SensorType.CO2, "ppm", [800.0]),
    ])
    ctx = RecommendationContext(zones=[zone], open_alerts=[])
    assert CO2OutOfRangeRule().evaluate(ctx) == []


# ---------------------------------------------------------------------------
# AnomalyReviewRule
# ---------------------------------------------------------------------------


def test_anomaly_review_from_open_alert():
    alert = OpenAlertView(
        id=1,
        greenhouse_id=1,
        zone_id=1,
        sensor_id=20,
        alert_type="anomaly",
        severity="warning",
        message="Temperature 55°C is a statistical anomaly",
    )
    zone = _zone()
    ctx = RecommendationContext(zones=[zone], open_alerts=[alert])
    out = AnomalyReviewRule().evaluate(ctx)
    assert len(out) == 1
    assert out[0].recommendation_type == RecommendationType.ANOMALY_REVIEW


def test_anomaly_review_ignores_non_anomaly_alerts():
    alert = OpenAlertView(
        id=1, greenhouse_id=1, zone_id=1, sensor_id=20,
        alert_type="threshold_high", severity="critical",
        message="x",
    )
    ctx = RecommendationContext(zones=[_zone()], open_alerts=[alert])
    assert AnomalyReviewRule().evaluate(ctx) == []


# ---------------------------------------------------------------------------
# YieldRiskRule
# ---------------------------------------------------------------------------


def test_yield_risk_fires_when_predicted_below_baseline():
    zone = _zone(crop_type="tomato")
    ctx = RecommendationContext(
        zones=[zone],
        open_alerts=[],
        predicted_yield_by_zone={1: 2.0},  # tomato baseline = 4.8
        model_version="v1",
    )
    out = YieldRiskRule().evaluate(ctx)
    assert out and out[0].recommendation_type == RecommendationType.YIELD_RISK


def test_yield_risk_silent_when_prediction_near_baseline():
    zone = _zone(crop_type="tomato")
    ctx = RecommendationContext(
        zones=[zone],
        open_alerts=[],
        predicted_yield_by_zone={1: 4.7},
        model_version="v1",
    )
    assert YieldRiskRule().evaluate(ctx) == []


def test_yield_risk_skips_unknown_crop():
    zone = _zone(crop_type="kale")  # not in _BASELINE_BY_CROP
    ctx = RecommendationContext(
        zones=[zone],
        open_alerts=[],
        predicted_yield_by_zone={1: 0.5},
        model_version="v1",
    )
    assert YieldRiskRule().evaluate(ctx) == []