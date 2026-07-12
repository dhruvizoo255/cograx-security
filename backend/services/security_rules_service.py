"""
Security rule engine — deterministic, explainable checks that run
independently of the ML model. These mirror the kinds of heuristic checks
real tools (GoPlus, Token Sniffer, etc.) surface, and are used to build the
security checklist + recommendations shown to the user.
"""

from __future__ import annotations

from typing import List

from backend.api.schemas.request_schemas import TokenFeatures
from backend.api.schemas.response_schemas import SecurityCheck


def run_security_checks(features: TokenFeatures) -> List[SecurityCheck]:
    """Run all deterministic heuristic checks against the submitted token."""
    checks: List[SecurityCheck] = []

    checks.append(
        SecurityCheck(
            name="Mint Permission",
            passed=not features.owner_can_mint,
            severity="critical" if features.owner_can_mint else "info",
            detail=(
                "Owner/contract can mint new tokens at will, diluting holders."
                if features.owner_can_mint
                else "No mint privilege detected."
            ),
        )
    )
    checks.append(
        SecurityCheck(
            name="Pause / Blacklist Authority",
            passed=not features.owner_can_pause,
            severity="high" if features.owner_can_pause else "info",
            detail=(
                "Owner can pause trading or blacklist wallets."
                if features.owner_can_pause
                else "No pause/blacklist authority detected."
            ),
        )
    )
    checks.append(
        SecurityCheck(
            name="Ownership Renouncement",
            passed=features.ownership_renounced,
            severity="medium" if not features.ownership_renounced else "info",
            detail=(
                "Ownership has been renounced."
                if features.ownership_renounced
                else "Ownership has NOT been renounced; owner retains privileged control."
            ),
        )
    )
    checks.append(
        SecurityCheck(
            name="Contract Verification",
            passed=features.contract_verified,
            severity="high" if not features.contract_verified else "info",
            detail=(
                "Source code is verified on-chain."
                if features.contract_verified
                else "Source code is NOT verified; behavior cannot be independently audited."
            ),
        )
    )
    checks.append(
        SecurityCheck(
            name="Liquidity Lock",
            passed=features.liquidity_locked_pct >= 70,
            severity=(
                "high"
                if features.liquidity_locked_pct < 30
                else "medium" if features.liquidity_locked_pct < 70 else "info"
            ),
            detail=f"{features.liquidity_locked_pct:.1f}% of LP tokens are locked.",
        )
    )
    checks.append(
        SecurityCheck(
            name="LP Burned",
            passed=features.lp_burned,
            severity="medium" if not features.lp_burned else "info",
            detail=(
                "LP tokens burned."
                if features.lp_burned
                else "LP tokens have not been burned."
            ),
        )
    )
    checks.append(
        SecurityCheck(
            name="Holder Concentration",
            passed=features.top_holder_pct <= 20,
            severity=(
                "critical"
                if features.top_holder_pct > 50
                else "high" if features.top_holder_pct > 20 else "info"
            ),
            detail=f"Top holder controls {features.top_holder_pct:.1f}% of supply.",
        )
    )
    checks.append(
        SecurityCheck(
            name="Tax Structure",
            passed=(features.buy_tax + features.sell_tax) <= 15,
            severity=(
                "critical"
                if (features.buy_tax + features.sell_tax) > 30
                else "medium" if (features.buy_tax + features.sell_tax) > 15 else "info"
            ),
            detail=f"Combined buy+sell tax is {features.buy_tax + features.sell_tax:.1f}%.",
        )
    )
    checks.append(
        SecurityCheck(
            name="Token Maturity",
            passed=features.token_age_days >= 30,
            severity="medium" if features.token_age_days < 30 else "info",
            detail=f"Token is {features.token_age_days} days old.",
        )
    )
    checks.append(
        SecurityCheck(
            name="Liquidity Depth",
            passed=features.liquidity_usd >= 50_000,
            severity=(
                "high"
                if features.liquidity_usd < 10_000
                else "medium" if features.liquidity_usd < 50_000 else "info"
            ),
            detail=f"Liquidity pool holds ${features.liquidity_usd:,.0f}.",
        )
    )
    return checks


def build_recommendations(checks: List[SecurityCheck]) -> List[str]:
    """Turn failed checks into concrete, actionable recommendations."""
    recs: List[str] = []
    mapping = {
        "Mint Permission": "Remove mint privilege or renounce minting authority.",
        "Pause / Blacklist Authority": "Remove pause/blacklist authority from the contract.",
        "Ownership Renouncement": "Renounce contract ownership to reduce centralized control risk.",
        "Contract Verification": "Verify contract source code publicly for independent audit.",
        "Liquidity Lock": "Increase the percentage of locked liquidity.",
        "LP Burned": "Burn LP tokens to remove rug-pull withdrawal risk.",
        "Holder Concentration": (
            "Encourage broader token distribution to reduce holder concentration."
        ),
        "Tax Structure": (
            "Reduce buy/sell tax to levels consistent with market norms (<15% combined)."
        ),
        "Token Maturity": "Allow the token to mature before large-scale promotion.",
        "Liquidity Depth": "Increase liquidity pool depth to reduce slippage and exit-scam risk.",
    }
    for check in checks:
        if not check.passed and check.name in mapping:
            recs.append(mapping[check.name])
    return recs
