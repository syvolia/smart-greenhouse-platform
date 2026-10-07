from __future__ import annotations

from app.config import settings
from app.models.enums import (
    RecommendationPriority,
    RecommendationType,
    SensorType,
)
from app.services.recommendation_engine.base import CandidateRecommendation
from app.services.recommendation_engine.context import (
    RecommendationContext,
    SensorView,  # noqa: F401
    ZoneView,  # noqa: F401
)


def _fmt(value: float, unit: str = "") -> str:
    s = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{s}{unit}" if unit else s


def _label(sensor_type: SensorType) -> str:
    return sensor_type.value.replace("_", " ").title()


class IrrigationNeededRule:
    name = "irrigation_needed"

    def evaluate(self, ctx: RecommendationContext) -> list[CandidateRecommendation]:
        out: list[CandidateRecommendation] = []
        for zone in ctx.zones:
            target = zone.target_soil_moisture
            sensor = zone.sensor(SensorType.SOIL_MOISTURE)
            if target is None or sensor is None or sensor.current_value is None:
                continue
            lo, hi = target
            value = sensor.current_value
            if value >= lo:
                continue
            deficit = lo - value
            priority = (
                RecommendationPriority.CRITICAL
                if deficit >= (hi - lo) * 0.5
                else RecommendationPriority.HIGH
            )
            out.append(
                CandidateRecommendation(
                    recommendation_type=RecommendationType.IRRIGATION_NEEDED,
                    priority=priority,
                    greenhouse_id=zone.greenhouse_id,
                    zone_id=zone.id,
                    sensor_id=sensor.id,
                    message=(
                        f"Soil moisture in {zone.name} is {_fmt(value, '%')}, "
                        f"below the target minimum of {_fmt(lo, '%')}. "
                        f"Irrigation is recommended."
                    ),
                    reason=(
                        f"Zone target for soil moisture is "
                        f"{_fmt(lo, '%')}-{_fmt(hi, '%')}. Latest reading from "
                        f"sensor #{sensor.id} ({_label(sensor.sensor_type)}) is "
                        f"{_fmt(value, '%')}."
                    ),
                )
            )
        return out


class _SustainedTempRule:
    direction: str
    recommendation_type: RecommendationType
    priority: RecommendationPriority

    def evaluate(self, ctx: RecommendationContext) -> list[CandidateRecommendation]:
        needed = settings.recommendation_sustained_window
        out: list[CandidateRecommendation] = []
        for zone in ctx.zones:
            target = zone.target_temperature
            sensor = zone.sensor(SensorType.TEMPERATURE)
            if target is None or sensor is None or sensor.current_value is None:
                continue
            lo, hi = target
            boundary = hi if self.direction == "above" else lo
            recent = sensor.recent_values[:needed]
            if len(recent) < needed:
                continue
            if self.direction == "above":
                all_beyond = all(v > boundary for _, v in recent)
            else:
                all_beyond = all(v < boundary for _, v in recent)
            if not all_beyond:
                continue

            avg = sum(v for _, v in recent) / len(recent)
            minutes = max(1, int((recent[0][0] - recent[-1][0]).total_seconds() // 60))
            action = "Increase ventilation" if self.direction == "above" else "Activate heating"
            out.append(
                CandidateRecommendation(
                    recommendation_type=self.recommendation_type,
                    priority=self.priority,
                    greenhouse_id=zone.greenhouse_id,
                    zone_id=zone.id,
                    sensor_id=sensor.id,
                    message=(
                        f"{zone.name} temperature has been {self.direction} the crop "
                        f"target for the last ~{minutes} minutes "
                        f"(avg {_fmt(avg, 'C')} vs target "
                        f"{_fmt(lo, 'C')}-{_fmt(hi, 'C')}). {action}."
                    ),
                    reason=(
                        f"Last {needed} temperature readings from sensor #{sensor.id} "
                        f"were all {self.direction} {_fmt(boundary, 'C')}."
                    ),
                )
            )
        return out


class TemperatureHighRule(_SustainedTempRule):
    name = "temperature_high"
    direction = "above"
    recommendation_type = RecommendationType.TEMPERATURE_HIGH
    priority = RecommendationPriority.HIGH


class TemperatureLowRule(_SustainedTempRule):
    name = "temperature_low"
    direction = "below"
    recommendation_type = RecommendationType.TEMPERATURE_LOW
    priority = RecommendationPriority.HIGH


class HumidityHighRiskRule:
    name = "humidity_high_risk"

    def evaluate(self, ctx: RecommendationContext) -> list[CandidateRecommendation]:
        out: list[CandidateRecommendation] = []
        for zone in ctx.zones:
            target = zone.target_humidity
            sensor = zone.sensor(SensorType.HUMIDITY)
            if target is None or sensor is None or sensor.current_value is None:
                continue
            lo, hi = target
            value = sensor.current_value
            if value <= hi:
                continue
            excess = value - hi
            priority = (
                RecommendationPriority.HIGH
                if excess >= 10.0
                else RecommendationPriority.MEDIUM
            )
            out.append(
                CandidateRecommendation(
                    recommendation_type=RecommendationType.HUMIDITY_HIGH_RISK,
                    priority=priority,
                    greenhouse_id=zone.greenhouse_id,
                    zone_id=zone.id,
                    sensor_id=sensor.id,
                    message=(
                        f"Humidity in {zone.name} is {_fmt(value, '%')}, above the "
                        f"target maximum of {_fmt(hi, '%')}. Sustained high humidity "
                        f"increases fungal disease risk."
                    ),
                    reason=(
                        f"Zone humidity target is {_fmt(lo, '%')}-{_fmt(hi, '%')}. "
                        f"Latest reading from sensor #{sensor.id} is "
                        f"{_fmt(value, '%')}."
                    ),
                )
            )
        return out


class CO2OutOfRangeRule:
    name = "co2_out_of_range"

    def evaluate(self, ctx: RecommendationContext) -> list[CandidateRecommendation]:
        out: list[CandidateRecommendation] = []
        lo_cfg = float(settings.alert_co2_min_ppm)
        hi_cfg = float(settings.alert_co2_max_ppm)
        for zone in ctx.zones:
            sensor = zone.sensor(SensorType.CO2)
            if sensor is None or sensor.current_value is None:
                continue
            value = sensor.current_value
            if lo_cfg <= value <= hi_cfg:
                continue
            direction = "above" if value > hi_cfg else "below"
            out.append(
                CandidateRecommendation(
                    recommendation_type=RecommendationType.CO2_OUT_OF_RANGE,
                    priority=RecommendationPriority.MEDIUM,
                    greenhouse_id=zone.greenhouse_id,
                    zone_id=zone.id,
                    sensor_id=sensor.id,
                    message=(
                        f"CO2 in {zone.name} is {_fmt(value, ' ppm')}, {direction} the "
                        f"acceptable range ({int(lo_cfg)}-{int(hi_cfg)} ppm)."
                    ),
                    reason=(
                        f"Latest CO2 reading from sensor #{sensor.id} is "
                        f"{_fmt(value, ' ppm')} against configured bounds "
                        f"{int(lo_cfg)}-{int(hi_cfg)} ppm."
                    ),
                )
            )
        return out


class AnomalyReviewRule:
    name = "anomaly_review"

    def evaluate(self, ctx: RecommendationContext) -> list[CandidateRecommendation]:
        out: list[CandidateRecommendation] = []
        for alert in ctx.open_alerts:
            if alert.alert_type != "anomaly":
                continue
            zone = ctx.zone(alert.zone_id) if alert.zone_id else None
            zone_name = zone.name if zone else f"zone #{alert.zone_id}"
            out.append(
                CandidateRecommendation(
                    recommendation_type=RecommendationType.ANOMALY_REVIEW,
                    priority=(
                        RecommendationPriority.HIGH
                        if alert.severity == "critical"
                        else RecommendationPriority.MEDIUM
                    ),
                    greenhouse_id=alert.greenhouse_id,
                    zone_id=alert.zone_id,
                    sensor_id=alert.sensor_id,
                    message=(
                        f"Statistical anomaly detected in {zone_name}. "
                        f"Review recent readings and confirm sensor integrity."
                    ),
                    reason=f"Open anomaly alert #{alert.id}: {alert.message}",
                )
            )
        return out


_BASELINE_BY_CROP = {
    "tomato": "yield_baseline_tomato",
    "cucumber": "yield_baseline_cucumber",
    "lettuce": "yield_baseline_lettuce",
    "pepper": "yield_baseline_pepper",
}


class YieldRiskRule:
    name = "yield_risk"

    def evaluate(self, ctx: RecommendationContext) -> list[CandidateRecommendation]:
        if not ctx.predicted_yield_by_zone:
            return []
        ratio_threshold = settings.recommendation_yield_risk_ratio
        out: list[CandidateRecommendation] = []
        for zone in ctx.zones:
            pred = ctx.predicted_yield_by_zone.get(zone.id)
            if pred is None:
                continue
            attr = _BASELINE_BY_CROP.get(zone.crop_type.lower())
            if attr is None:
                continue
            baseline = float(getattr(settings, attr))
            if baseline <= 0:
                continue
            if pred >= baseline * ratio_threshold:
                continue
            delta_pct = (baseline - pred) / baseline * 100.0
            out.append(
                CandidateRecommendation(
                    recommendation_type=RecommendationType.YIELD_RISK,
                    priority=RecommendationPriority.HIGH,
                    greenhouse_id=zone.greenhouse_id,
                    zone_id=zone.id,
                    sensor_id=None,
                    message=(
                        f"Current environmental trends in {zone.name} may reduce "
                        f"predicted yield to {_fmt(pred, ' kg/m2')} "
                        f"(baseline {_fmt(baseline, ' kg/m2')})."
                    ),
                    reason=(
                        f"ML model {ctx.model_version} predicts yield "
                        f"{delta_pct:.1f}% below the {zone.crop_type} baseline "
                        f"under the zone's current averaged conditions."
                    ),
                )
            )
        return out
