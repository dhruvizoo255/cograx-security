"""Health and metrics endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.schemas.response_schemas import HealthResponse, MetricsResponse
from backend.api.security import require_api_key
from backend.core.config import get_settings
from backend.repositories.audit_repository import get_audit_repository
from backend.repositories.model_repository import ModelRepository
from backend.services.blockchain_service import BlockchainService

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthResponse, summary="Service health check")
async def health() -> HealthResponse:
    settings = get_settings()
    repo = ModelRepository.instance()
    model_loaded = False
    scaler_loaded = False
    try:
        artifacts = repo.load()
        model_loaded = artifacts.model is not None
        scaler_loaded = artifacts.scaler is not None
    except Exception:
        pass

    blockchain_connected = BlockchainService().is_connected

    return HealthResponse(
        status="ok" if model_loaded and scaler_loaded else "degraded",
        model_loaded=model_loaded,
        scaler_loaded=scaler_loaded,
        blockchain_connected=blockchain_connected,
        version=settings.app_version,
    )


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Aggregate prediction metrics",
    dependencies=[Depends(require_api_key)],
)
async def metrics() -> MetricsResponse:
    repo = get_audit_repository()
    records = repo.all()
    total = len(records)
    high = sum(1 for r in records if 75 > r["risk_score"] >= 50)
    critical = sum(1 for r in records if r["risk_score"] >= 75)
    avg_score = sum(r["risk_score"] for r in records) / total if total else 0.0
    stored = sum(1 for r in records if r["blockchain_status"].get("stored"))

    return MetricsResponse(
        total_predictions=total,
        high_risk_predictions=high,
        critical_risk_predictions=critical,
        average_risk_score=round(avg_score, 2),
        blockchain_stored_count=stored,
    )
