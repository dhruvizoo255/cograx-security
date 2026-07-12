"""
Explainability service — computes SHAP contributions for a single prediction
against the frozen XGBoost model. Purely read-only / inference-time use of
`shap.TreeExplainer`; does not alter the model in any way.
"""

from __future__ import annotations

import threading
from typing import List

import numpy as np

from backend.api.schemas.response_schemas import FeatureContribution
from backend.repositories.model_repository import ModelRepository


class ExplainabilityService:
    """Wraps a lazily-built `shap.TreeExplainer` around the frozen model."""

    _explainer_lock = threading.Lock()

    def __init__(self, repository: ModelRepository | None = None) -> None:
        self._repository = repository or ModelRepository.instance()
        self._explainer = None

    def _get_explainer(self):
        if self._explainer is None:
            with self._explainer_lock:
                if self._explainer is None:
                    import shap  # local import: heavy dependency, load on first use

                    artifacts = self._repository.load()
                    self._explainer = shap.TreeExplainer(artifacts.model)
        return self._explainer

    def explain(
        self,
        scaled_features: np.ndarray,
        feature_order: List[str],
        raw_values: List[float],
    ) -> tuple[List[FeatureContribution], List[FeatureContribution]]:
        """Return (top_positive, top_negative) SHAP feature contributions."""
        explainer = self._get_explainer()
        shap_values = explainer.shap_values(scaled_features)

        # shap_values may be a single array (binary XGBoost) shape (1, n_features)
        values = np.array(shap_values).reshape(-1)

        contributions = [
            FeatureContribution(
                feature=feature_order[i],
                value=raw_values[i],
                shap_value=float(values[i]),
                direction="increases_risk" if values[i] > 0 else "decreases_risk",
            )
            for i in range(len(feature_order))
        ]

        positive = sorted(
            [c for c in contributions if c.shap_value > 0],
            key=lambda c: c.shap_value,
            reverse=True,
        )[:5]
        negative = sorted(
            [c for c in contributions if c.shap_value < 0],
            key=lambda c: c.shap_value,
        )[:5]
        return positive, negative

    @staticmethod
    def to_natural_language(
        positive: List[FeatureContribution],
        negative: List[FeatureContribution],
        risk_level: str,
    ) -> str:
        """Render a short human-readable explanation from SHAP factors."""
        parts = [f"This token is classified as {risk_level} risk."]
        if positive:
            top = ", ".join(f"{c.feature.replace('_', ' ')}" for c in positive[:3])
            parts.append(f"The strongest risk-increasing factors are: {top}.")
        if negative:
            top = ", ".join(f"{c.feature.replace('_', ' ')}" for c in negative[:3])
            parts.append(f"These factors reduce risk: {top}.")
        return " ".join(parts)
