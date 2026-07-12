"""
Predictor service — the only place that calls `.transform()` and
`.predict_proba()` on the frozen scaler/model. Strictly read-only inference;
never calls `.fit()`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backend.core.exceptions import ModelNotLoadedError
from backend.repositories.model_repository import ModelRepository


@dataclass(frozen=True)
class InferenceResult:
    rug_pull_probability: float  # probability of class "1" (rug pull)
    confidence: float  # max(p, 1-p): how confident the model is either way
    scaled_features: np.ndarray


class PredictorService:
    """Runs the frozen scaler -> frozen XGBoost pipeline."""

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self._repository = repository or ModelRepository.instance()

    def predict(self, feature_vector: np.ndarray) -> InferenceResult:
        artifacts = self._repository.load()
        if artifacts is None:
            raise ModelNotLoadedError()

        scaled = artifacts.scaler.transform(feature_vector)
        proba = artifacts.model.predict_proba(scaled)[0]
        rug_pull_probability = float(proba[1])
        confidence = float(max(proba))
        return InferenceResult(
            rug_pull_probability=rug_pull_probability,
            confidence=confidence,
            scaled_features=scaled,
        )

    @property
    def model_version_tag(self) -> str:
        from backend.core.config import get_settings

        return get_settings().model_version
