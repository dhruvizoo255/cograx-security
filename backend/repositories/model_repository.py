"""
Repository for the frozen ML artifacts.

This is the ONLY module that touches `models/rugguard_xgb.pkl` and
`models/scaler.pkl` on disk. It loads them read-only via joblib and never
fits, retrains, or mutates them, per the frozen-artifact rule.
"""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import List

import joblib

from backend.core.config import Settings, get_settings
from backend.core.exceptions import ModelNotLoadedError
from backend.core.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)
class FrozenArtifacts:
    model: object
    scaler: object
    feature_order: List[str]


class ModelRepository:
    """Thread-safe, lazily-initialized singleton loader for frozen artifacts."""

    _instance: "ModelRepository | None" = None
    _lock = threading.Lock()

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or get_settings()
        self._artifacts: FrozenArtifacts | None = None

    @classmethod
    def instance(cls) -> "ModelRepository":
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def load(self) -> FrozenArtifacts:
        """Load (or return cached) frozen model + scaler."""
        if self._artifacts is not None:
            return self._artifacts

        with self._lock:
            if self._artifacts is not None:
                return self._artifacts
            try:
                self._verify_integrity(
                    self._settings.model_path, self._settings.model_sha256
                )
                self._verify_integrity(
                    self._settings.scaler_path, self._settings.scaler_sha256
                )
                model = joblib.load(self._settings.model_path)
                scaler = joblib.load(self._settings.scaler_path)
            except FileNotFoundError as exc:
                logger.error("Frozen artifact missing: %s", exc)
                raise ModelNotLoadedError(str(exc)) from exc

            feature_order = list(getattr(scaler, "feature_names_in_", []))
            if not feature_order:
                raise ModelNotLoadedError(
                    "Scaler is missing feature_names_in_; cannot determine "
                    "the frozen feature order safely."
                )

            self._artifacts = FrozenArtifacts(
                model=model, scaler=scaler, feature_order=feature_order
            )
            logger.info(
                "Loaded frozen artifacts. model=%s scaler=%s features=%d",
                type(model).__name__,
                type(scaler).__name__,
                len(feature_order),
            )
            return self._artifacts

    def _verify_integrity(self, path: Path, expected_hash: str) -> None:
        """Verify a configured SHA-256 without modifying frozen artifacts."""
        if not self._settings.verify_model_integrity or not expected_hash:
            return
        if (
            hashlib.sha256(path.read_bytes()).hexdigest().lower()
            != expected_hash.lower()
        ):
            raise ModelNotLoadedError(f"Integrity check failed for {path.name}.")

    @property
    def is_loaded(self) -> bool:
        return self._artifacts is not None
