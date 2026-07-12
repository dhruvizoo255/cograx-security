"""Risk engine — converts the frozen model's raw probability into the
product-facing 0-100 risk score and LOW/MEDIUM/HIGH/CRITICAL band.

This is business logic layered ON TOP of the frozen binary classifier; it
does not change the model's prediction, only how it's presented.
"""

from __future__ import annotations

from backend.api.schemas.response_schemas import RiskLevel
from backend.core.config import Settings, get_settings


def score_from_probability(probability: float) -> float:
    """Map a [0,1] probability to a [0,100] risk score."""
    return round(probability * 100, 2)


def classify_risk(probability: float, settings: Settings | None = None) -> RiskLevel:
    settings = settings or get_settings()
    if probability < settings.risk_threshold_low:
        return RiskLevel.LOW
    if probability < settings.risk_threshold_medium:
        return RiskLevel.MEDIUM
    if probability < settings.risk_threshold_high:
        return RiskLevel.HIGH
    return RiskLevel.CRITICAL
