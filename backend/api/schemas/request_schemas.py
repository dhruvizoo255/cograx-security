"""Request schemas for the prediction API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenFeatures(BaseModel):
    """Raw, human-readable token/contract features.

    Field order here is intentionally readable; the FeatureService is
    responsible for re-ordering into the exact column order the frozen
    scaler/model expect (`scaler.feature_names_in_`).
    """

    token_address: str = Field(
        ...,
        pattern=r"^0x[a-fA-F0-9]{40}$",
        description="EVM contract address of the token.",
    )
    liquidity_locked_pct: float = Field(
        ..., ge=0, le=100, description="% of LP tokens locked."
    )
    owner_can_mint: bool = Field(
        ..., description="Owner/contract retains mint privilege."
    )
    owner_can_pause: bool = Field(..., description="Owner/contract can pause trading.")
    ownership_renounced: bool = Field(..., description="Ownership has been renounced.")
    contract_verified: bool = Field(
        ..., description="Source code is verified on-chain."
    )
    top_holder_pct: float = Field(
        ..., ge=0, le=100, description="% supply held by top holder."
    )
    number_of_holders: int = Field(
        ..., ge=0, description="Total distinct holder count."
    )
    buy_tax: float = Field(..., ge=0, le=100, description="Buy tax, percent.")
    sell_tax: float = Field(..., ge=0, le=100, description="Sell tax, percent.")
    lp_burned: bool = Field(..., description="LP tokens have been burned.")
    token_age_days: int = Field(
        ..., ge=0, description="Days since contract deployment."
    )
    liquidity_usd: float = Field(..., ge=0, description="Liquidity pool size, USD.")
    daily_volume_usd: float = Field(..., ge=0, description="24h trading volume, USD.")
    market_cap_usd: float = Field(..., ge=0, description="Market capitalization, USD.")

    class Config:
        json_schema_extra = {
            "example": {
                "token_address": "0x1234567890abcdef1234567890abcdef12345678",
                "liquidity_locked_pct": 51,
                "owner_can_mint": False,
                "owner_can_pause": False,
                "ownership_renounced": True,
                "contract_verified": True,
                "top_holder_pct": 30,
                "number_of_holders": 17535,
                "buy_tax": 2,
                "sell_tax": 22,
                "lp_burned": False,
                "token_age_days": 907,
                "liquidity_usd": 3730497,
                "daily_volume_usd": 21157,
                "market_cap_usd": 2420837,
            }
        }


class PredictionRequest(BaseModel):
    features: TokenFeatures
    wallet_address: str | None = Field(
        default=None,
        pattern=r"^0x[a-fA-F0-9]{40}$",
        description="Requesting wallet, stored on-chain for audit.",
    )
    store_on_chain: bool = Field(
        default=False,
        description="Whether to immediately anchor this prediction on-chain.",
    )
