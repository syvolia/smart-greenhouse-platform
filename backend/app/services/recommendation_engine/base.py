"""Core protocol and data shape for the recommendation engine.

Each rule:

  - reads from a RecommendationContext (no DB access),
  - returns zero or more CandidateRecommendation objects.

Rules MUST be pure functions of their input: same context → same output.
This makes them trivially unit-testable and lets us later add an LLM-based
rule that conforms to the same interface.
"""
from dataclasses import dataclass
from typing import Optional, Protocol

from app.models.enums import (
    RecommendationPriority,
    RecommendationType,
)


@dataclass(frozen=True)
class CandidateRecommendation:
    recommendation_type: RecommendationType
    priority: RecommendationPriority
    message: str
    reason: str
    greenhouse_id: int
    zone_id: Optional[int] = None
    sensor_id: Optional[int] = None


class RecommendationRule(Protocol):
    """All rules implement this protocol.

    `name` is a stable identifier used in logs and tests.
    """
    name: str

    def evaluate(self, ctx: "RecommendationContext") -> list[CandidateRecommendation]:
        ...