"""Registry of active rules.

To add a rule, append an instance to RULES. To add an LLM-based rule later,
implement a class that conforms to RecommendationRule and add it here —
nothing else in the codebase needs to change.
"""
from app.services.recommendation_engine.rules import (
    AnomalyReviewRule,
    CO2OutOfRangeRule,
    HumidityHighRiskRule,
    IrrigationNeededRule,
    TemperatureHighRule,
    TemperatureLowRule,
    YieldRiskRule,
)

RULES = [
    IrrigationNeededRule(),
    TemperatureHighRule(),
    TemperatureLowRule(),
    HumidityHighRiskRule(),
    CO2OutOfRangeRule(),
    AnomalyReviewRule(),
    YieldRiskRule(),
]