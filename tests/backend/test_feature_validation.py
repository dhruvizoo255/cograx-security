import pytest
from pydantic import ValidationError

from backend.api.schemas.request_schemas import TokenFeatures


def test_percentage_bounds_are_enforced() -> None:
    payload = {
        "token_address": "0x1234567890abcdef1234567890abcdef12345678",
        "liquidity_locked_pct": 101,
        "owner_can_mint": False,
        "owner_can_pause": False,
        "ownership_renounced": True,
        "contract_verified": True,
        "top_holder_pct": 10,
        "number_of_holders": 1,
        "buy_tax": 0,
        "sell_tax": 0,
        "lp_burned": True,
        "token_age_days": 1,
        "liquidity_usd": 1,
        "daily_volume_usd": 1,
        "market_cap_usd": 1,
    }
    with pytest.raises(ValidationError):
        TokenFeatures(**payload)
