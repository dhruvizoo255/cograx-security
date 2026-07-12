from backend.api.schemas.response_schemas import RiskLevel
from backend.services.hash_service import (
    hash_features,
    hash_prediction,
    verify_prediction_integrity,
)
from backend.services.risk_engine import classify_risk, score_from_probability


def test_feature_hash_is_canonical_and_address_case_insensitive() -> None:
    first = hash_features({"B": 2.0, "A": 1.0}, "0xABC")
    second = hash_features({"A": 1.0, "B": 2.0}, "0xabc")
    assert first == second


def test_prediction_hash_verifies_and_detects_tampering() -> None:
    digest = hash_prediction("features", 12.5, 0.875, "v1", "2026-01-01T00:00:00+00:00")
    assert verify_prediction_integrity(
        "features", 12.5, 0.875, "v1", "2026-01-01T00:00:00+00:00", digest
    )
    assert not verify_prediction_integrity(
        "features", 12.6, 0.875, "v1", "2026-01-01T00:00:00+00:00", digest
    )


def test_risk_bands_and_score() -> None:
    assert score_from_probability(0.1234) == 12.34
    assert classify_risk(0.24) is RiskLevel.LOW
    assert classify_risk(0.25) is RiskLevel.MEDIUM
    assert classify_risk(0.50) is RiskLevel.HIGH
    assert classify_risk(0.75) is RiskLevel.CRITICAL
