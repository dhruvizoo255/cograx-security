"""Response schemas for the prediction and audit APIs."""

from __future__ import annotations

from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FeatureContribution(BaseModel):
    feature: str
    value: float
    shap_value: float = Field(..., description="SHAP contribution to the risk score.")
    direction: str = Field(..., description="'increases_risk' or 'decreases_risk'.")


class SecurityCheck(BaseModel):
    name: str
    passed: bool
    severity: str = Field(..., description="info | low | medium | high | critical")
    detail: str


class BlockchainStatus(BaseModel):
    stored: bool
    tx_hash: Optional[str] = None
    block_number: Optional[int] = None
    contract_address: Optional[str] = None
    error: Optional[str] = None


class PredictionResponse(BaseModel):
    prediction_id: str
    token_address: str
    risk_score: float = Field(..., description="0-100 scale rug-pull risk score.")
    confidence: float = Field(..., description="Model confidence, 0-1.")
    risk_level: RiskLevel
    top_positive_factors: List[FeatureContribution] = Field(
        default_factory=list, description="Factors pushing risk UP."
    )
    top_negative_factors: List[FeatureContribution] = Field(
        default_factory=list, description="Factors pushing risk DOWN."
    )
    natural_language_explanation: str
    security_checklist: List[SecurityCheck]
    recommendations: List[str]
    model_version: str
    timestamp: str
    prediction_hash: str
    blockchain_status: BlockchainStatus


class AuditRecord(BaseModel):
    prediction_id: str
    token_address: str
    prediction_hash: str
    feature_hash: str
    risk_score: float
    confidence: float
    model_version: str
    timestamp: str
    wallet_address: Optional[str] = None
    blockchain_status: BlockchainStatus


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    scaler_loaded: bool
    blockchain_connected: bool
    version: str


class MetricsResponse(BaseModel):
    total_predictions: int
    high_risk_predictions: int
    critical_risk_predictions: int
    average_risk_score: float
    blockchain_stored_count: int
