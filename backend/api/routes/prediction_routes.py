"""Prediction, audit, and reporting routes."""

from __future__ import annotations

from io import BytesIO

from fastapi import APIRouter, Depends, Response
from fastapi.responses import StreamingResponse

from backend.api.schemas.request_schemas import PredictionRequest
from backend.api.schemas.response_schemas import AuditRecord, PredictionResponse
from backend.api.security import protect_prediction_endpoint, require_api_key
from backend.core.exceptions import AuditNotFoundError
from backend.repositories.audit_repository import get_audit_repository
from backend.services.prediction_service import PredictionService
from backend.services.report_service import generate_pdf_report

router = APIRouter(tags=["prediction"])

_prediction_service = PredictionService()


@router.post(
    "/predict",
    response_model=PredictionResponse,
    summary="Assess rug-pull risk for a token",
)
async def predict(
    request: PredictionRequest, _: None = Depends(protect_prediction_endpoint)
) -> PredictionResponse:
    """Run the full prediction pipeline: validate -> scale -> infer ->
    classify -> explain (SHAP) -> hash -> optionally anchor on-chain."""
    return _prediction_service.predict(request)


@router.get(
    "/audit/{prediction_id}",
    response_model=AuditRecord,
    summary="Retrieve an audit record",
    dependencies=[Depends(require_api_key)],
)
async def get_audit(prediction_id: str) -> AuditRecord:
    """Fetch a single audit record by id. Requires ``X-API-Key`` whenever
    ``COGRAX_API_KEY`` is configured (always true in production) so audit
    evidence cannot be pulled by an unauthenticated caller."""
    repo = get_audit_repository()
    record = repo.get(prediction_id)
    if record is None:
        raise AuditNotFoundError(f"No audit record found for id={prediction_id}")
    return AuditRecord(**record)


@router.get(
    "/audit",
    response_model=list[AuditRecord],
    summary="List all audit records",
    dependencies=[Depends(require_api_key)],
)
async def list_audit() -> list[AuditRecord]:
    """List every audit record. Requires ``X-API-Key`` -- this is the
    endpoint that would otherwise make the full audit history publicly
    enumerable."""
    repo = get_audit_repository()
    return [AuditRecord(**r) for r in repo.all()]


@router.post(
    "/predict/{prediction_id}/report",
    summary="Generate a PDF report for a stored prediction",
    dependencies=[Depends(require_api_key)],
)
async def report(prediction_id: str, request: PredictionRequest) -> Response:
    """
    Streams a PDF for the requested stored prediction. The body remains for
    dashboard backward compatibility but is intentionally ignored. Requires
    ``X-API-Key`` since a report re-exposes the full audit record.
    """
    record = get_audit_repository().get(prediction_id)
    if record is None:
        raise AuditNotFoundError(f"No audit record found for id={prediction_id}")
    prediction = PredictionResponse(**record["response"])
    pdf_bytes = generate_pdf_report(prediction)
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=cograx_report_{prediction_id}.pdf"
        },
    )
