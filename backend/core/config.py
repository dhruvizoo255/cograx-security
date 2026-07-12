"""
Centralized application configuration.

All tunable values (thresholds, paths, blockchain RPC, API keys) live here and
are overridable via environment variables / .env, per the "everything
configurable" requirement.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application-wide settings, loaded from environment / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", env_prefix="COGRAX_", extra="ignore"
    )

    # --- App metadata ---
    app_name: str = "Cograx Security API"
    app_version: str = "1.0.0"
    environment: str = Field(default="development")
    api_v1_prefix: str = "/api/v1"

    # --- CORS ---
    # Explicit local default; configure production origins through the env.
    cors_origins: List[str] = ["http://localhost:8501"]
    api_key: str = Field(default="", repr=False)
    rate_limit_per_minute: int = Field(default=30, ge=1, le=10_000)
    trusted_hosts: List[str] = ["localhost", "127.0.0.1", "testserver", "api"]

    # --- Frozen ML artifacts (never modified, only read) ---
    model_path: Path = BASE_DIR / "models" / "rugguard_xgb.pkl"
    scaler_path: Path = BASE_DIR / "models" / "scaler.pkl"
    dataset_path: Path = BASE_DIR / "data" / "rugguard_dataset.csv"
    model_version: str = "rugguard-xgb-v1-frozen"
    verify_model_integrity: bool = True
    model_sha256: str = ""
    scaler_sha256: str = ""
    audit_db_path: Path = BASE_DIR / "data" / "cograx_audit.db"

    # --- Risk thresholds (business logic layer, NOT part of the frozen model) ---
    risk_threshold_low: float = 0.25
    risk_threshold_medium: float = 0.50
    risk_threshold_high: float = 0.75

    # --- Blockchain ---
    web3_rpc_url: str = Field(default="http://127.0.0.1:8545")
    chain_id: int = 31337
    contract_address: str = Field(default="")
    deployer_private_key: str = Field(default="")
    blockchain_enabled: bool = Field(default=False)

    # --- Logging ---
    log_level: str = "INFO"
    log_json: bool = False

    # --- Reports ---
    reports_dir: Path = BASE_DIR / "reports"

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        """Fail closed for settings that are unsafe in a public deployment."""
        if self.environment.lower() == "production":
            if not self.api_key:
                raise ValueError("COGRAX_API_KEY is required in production.")
            if "*" in self.cors_origins:
                raise ValueError("Wildcard CORS is not permitted in production.")
            if not self.model_sha256 or not self.scaler_sha256:
                raise ValueError("Artifact SHA-256 values are required in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
