"""
Hash service — computes deterministic SHA-256 fingerprints of input features
and of the final prediction payload, used for on-chain evidence, integrity
verification, and duplicate-prediction detection.
"""

from __future__ import annotations

import hashlib
import json
from typing import Dict


def hash_features(named_features: Dict[str, float], token_address: str) -> str:
    """SHA-256 of the canonicalized feature set + token address."""
    payload = {"token_address": token_address.lower(), "features": named_features}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def hash_prediction(
    feature_hash: str,
    risk_score: float,
    confidence: float,
    model_version: str,
    timestamp: str,
) -> str:
    """SHA-256 combining the feature hash with the model's output, for
    on-chain evidence and tamper-detection of the final result."""
    payload = {
        "feature_hash": feature_hash,
        "risk_score": round(risk_score, 4),
        "confidence": round(confidence, 4),
        "model_version": model_version,
        "timestamp": timestamp,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verify_prediction_integrity(
    feature_hash: str,
    risk_score: float,
    confidence: float,
    model_version: str,
    timestamp: str,
    expected_hash: str,
) -> bool:
    """Recompute the prediction hash and compare against a stored/on-chain value."""
    recomputed = hash_prediction(
        feature_hash, risk_score, confidence, model_version, timestamp
    )
    return recomputed == expected_hash
