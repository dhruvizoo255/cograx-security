"""Feature engineering / validation service.

Responsible ONLY for turning a `TokenFeatures` request into the exact,
correctly-ordered numeric vector the frozen scaler/model expect. Does not
perform any scaling or inference itself.
"""

from __future__ import annotations

from typing import Dict, List

import numpy as np

from backend.api.schemas.request_schemas import TokenFeatures
from backend.core.exceptions import FeatureValidationError

# Maps the frozen scaler's expected column name -> TokenFeatures attribute name.
_COLUMN_TO_FIELD: Dict[str, str] = {
    "Liquidity_Locked_Pct": "liquidity_locked_pct",
    "Owner_Can_Mint": "owner_can_mint",
    "Owner_Can_Pause": "owner_can_pause",
    "Ownership_Renounced": "ownership_renounced",
    "Contract_Verified": "contract_verified",
    "TopHolder_Pct": "top_holder_pct",
    "Number_of_Holders": "number_of_holders",
    "Buy_Tax": "buy_tax",
    "Sell_Tax": "sell_tax",
    "LP_Burned": "lp_burned",
    "Token_Age_Days": "token_age_days",
    "Liquidity_USD": "liquidity_usd",
    "Daily_Volume_USD": "daily_volume_usd",
    "Market_Cap_USD": "market_cap_usd",
}


class FeatureService:
    """Builds the ordered feature vector required by the frozen artifacts."""

    def __init__(self, feature_order: List[str]) -> None:
        missing = [c for c in feature_order if c not in _COLUMN_TO_FIELD]
        if missing:
            raise FeatureValidationError(
                f"Frozen model expects unknown columns not mapped in "
                f"FeatureService: {missing}"
            )
        self._feature_order = feature_order

    @property
    def feature_order(self) -> List[str]:
        return self._feature_order

    def to_vector(self, features: TokenFeatures) -> np.ndarray:
        """Return a (1, n_features) float array in the exact frozen column order."""
        try:
            values = [
                float(getattr(features, _COLUMN_TO_FIELD[col]))
                for col in self._feature_order
            ]
        except (TypeError, ValueError) as exc:
            raise FeatureValidationError(f"Invalid feature value: {exc}") from exc
        return np.array(values, dtype=float).reshape(1, -1)

    def to_named_dict(self, features: TokenFeatures) -> Dict[str, float]:
        """Human-readable {column_name: value} in frozen order, for SHAP labeling."""
        return {
            col: float(getattr(features, _COLUMN_TO_FIELD[col]))
            for col in self._feature_order
        }
