"""
Prediction service — orchestrates the full pipeline described in the
architecture: validation -> scaling -> inference -> thresholding ->
classification -> SHAP -> hashing -> blockchain audit -> response.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from backend.api.schemas.request_schemas import PredictionRequest
from backend.api.schemas.response_schemas import PredictionResponse
from backend.core.logging_config import get_logger
from backend.repositories.audit_repository import AuditRepository, get_audit_repository
from backend.repositories.model_repository import ModelRepository
from backend.services.blockchain_service import BlockchainService
from backend.services.explainability_service import ExplainabilityService
from backend.services.feature_service import FeatureService
from backend.services.hash_service import hash_features, hash_prediction
from backend.services.predictor_service import PredictorService
from backend.services.risk_engine import classify_risk, score_from_probability
from backend.services.security_rules_service import (
    build_recommendations,
    run_security_checks,
)

logger = get_logger(__name__)


class PredictionService:
    """Top-level use-case service consumed directly by the API routes."""

    def __init__(
        self,
        predictor: PredictorService | None = None,
        explainer: ExplainabilityService | None = None,
        blockchain: BlockchainService | None = None,
        audit_repo: AuditRepository | None = None,
    ) -> None:
        self._model_repo = ModelRepository.instance()
        self._predictor = predictor or PredictorService(self._model_repo)
        self._explainer = explainer or ExplainabilityService(self._model_repo)
        self._blockchain = blockchain or BlockchainService()
        self._audit_repo = audit_repo or get_audit_repository()
        self._feature_service: FeatureService | None = None

    def _get_feature_service(self) -> FeatureService:
        if self._feature_service is None:
            artifacts = self._model_repo.load()
            self._feature_service = FeatureService(artifacts.feature_order)
        return self._feature_service

    def predict(self, request: PredictionRequest) -> PredictionResponse:
        feature_service = self._get_feature_service()
        features = request.features

        # 1. Validation -> vector construction
        vector = feature_service.to_vector(features)
        named = feature_service.to_named_dict(features)
        feature_hash = hash_features(named, features.token_address)

        # The prediction hash intentionally contains a timestamp, so it cannot
        # be used as a replay key. Use a stable feature fingerprint instead.
        cached = self._audit_repo.find_by_feature_hash(
            feature_hash, self._predictor.model_version_tag
        )
        if cached and (
            not request.store_on_chain or cached["blockchain_status"].get("stored")
        ):
            logger.info("Reusing cached prediction for feature hash=%s", feature_hash)
            return PredictionResponse(**cached["response"])

        # 2 & 3. Scaling + inference (inside predictor service)
        result = self._predictor.predict(vector)

        # 4. Threshold optimization / 5. classification
        risk_score = score_from_probability(result.rug_pull_probability)
        risk_level = classify_risk(result.rug_pull_probability)

        # 6. SHAP explanation
        positive, negative = self._explainer.explain(
            result.scaled_features, feature_service.feature_order, list(named.values())
        )
        explanation = ExplainabilityService.to_natural_language(
            positive, negative, risk_level.value
        )

        # Security checklist (independent, deterministic layer)
        checklist = run_security_checks(features)
        recommendations = build_recommendations(checklist)

        # 7. Prediction hash
        timestamp = datetime.now(timezone.utc).isoformat()
        prediction_hash = hash_prediction(
            feature_hash,
            risk_score,
            result.confidence,
            self._predictor.model_version_tag,
            timestamp,
        )

        prediction_id = str(uuid.uuid4())

        # 8. Blockchain audit
        blockchain_status = None
        if request.store_on_chain:
            blockchain_status = self._blockchain.store_prediction(
                prediction_id=prediction_id,
                token_address=features.token_address,
                wallet_address=request.wallet_address,
                prediction_hash=prediction_hash,
                risk_score=risk_score,
                confidence=result.confidence,
                model_version=self._predictor.model_version_tag,
                timestamp=int(time.time()),
            )
        else:
            from backend.api.schemas.response_schemas import BlockchainStatus

            blockchain_status = BlockchainStatus(stored=False, error=None)

        response = PredictionResponse(
            prediction_id=prediction_id,
            token_address=features.token_address,
            risk_score=risk_score,
            confidence=round(result.confidence, 4),
            risk_level=risk_level,
            top_positive_factors=positive,
            top_negative_factors=negative,
            natural_language_explanation=explanation,
            security_checklist=checklist,
            recommendations=recommendations,
            model_version=self._predictor.model_version_tag,
            timestamp=timestamp,
            prediction_hash=prediction_hash,
            blockchain_status=blockchain_status,
        )

        self._audit_repo.save(
            {
                "prediction_id": prediction_id,
                "token_address": features.token_address,
                "prediction_hash": prediction_hash,
                "feature_hash": feature_hash,
                "risk_score": risk_score,
                "confidence": result.confidence,
                "model_version": self._predictor.model_version_tag,
                "timestamp": timestamp,
                "wallet_address": request.wallet_address,
                "blockchain_status": blockchain_status.model_dump(),
                "response": response.model_dump(mode="json"),
            }
        )
        return response
