"""Integration tests against the real FastAPI app.

Uses the actual frozen model/scaler artifacts (they're small and fast to
load) so the full validate -> scale -> infer -> explain -> hash pipeline is
exercised end to end, not mocked away. Each API-key test rebuilds the
`Settings` singleton so tests stay isolated from each other.
"""

from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient

from backend.core.config import get_settings

VALID_FEATURES = {
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


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    """Fresh app + settings + audit DB for each test."""
    monkeypatch.setenv("COGRAX_AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    monkeypatch.delenv("COGRAX_API_KEY", raising=False)
    get_settings.cache_clear()

    import backend.main as main_module

    importlib.reload(main_module)
    with TestClient(main_module.app) as client:
        yield client
    get_settings.cache_clear()


def test_health_is_open(app_client) -> None:
    resp = app_client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["model_loaded"] is True


def test_predict_end_to_end_and_audit_lookup(app_client) -> None:
    resp = app_client.post("/api/v1/predict", json={"features": VALID_FEATURES})
    assert resp.status_code == 200
    body = resp.json()
    assert 0 <= body["risk_score"] <= 100
    assert body["risk_level"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert len(body["top_positive_factors"]) > 0

    prediction_id = body["prediction_id"]
    audit_resp = app_client.get(f"/api/v1/audit/{prediction_id}")
    assert audit_resp.status_code == 200
    assert audit_resp.json()["prediction_id"] == prediction_id

    listing = app_client.get("/api/v1/audit")
    assert listing.status_code == 200
    assert any(r["prediction_id"] == prediction_id for r in listing.json())


def test_audit_endpoints_require_api_key_when_configured(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("COGRAX_AUDIT_DB_PATH", str(tmp_path / "audit.db"))
    monkeypatch.setenv("COGRAX_API_KEY", "test-secret-key")
    get_settings.cache_clear()

    import backend.main as main_module

    importlib.reload(main_module)
    with TestClient(main_module.app) as client:
        # No key -> the full audit history must not be enumerable.
        assert client.get("/api/v1/audit").status_code == 401
        assert client.get("/api/v1/audit/does-not-matter").status_code == 401
        assert client.get("/metrics").status_code == 401

        # Wrong key -> still rejected.
        assert (
            client.get("/api/v1/audit", headers={"X-API-Key": "wrong"}).status_code
            == 401
        )

        # Predict also requires the key.
        predict_resp = client.post("/api/v1/predict", json={"features": VALID_FEATURES})
        assert predict_resp.status_code == 401

        # Correct key -> allowed through.
        headers = {"X-API-Key": "test-secret-key"}
        assert client.get("/api/v1/audit", headers=headers).status_code == 200
        assert client.get("/metrics", headers=headers).status_code == 200
        ok_predict = client.post(
            "/api/v1/predict", json={"features": VALID_FEATURES}, headers=headers
        )
        assert ok_predict.status_code == 200

    get_settings.cache_clear()
    monkeypatch.delenv("COGRAX_API_KEY", raising=False)
