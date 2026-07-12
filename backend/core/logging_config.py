"""Structured logging configuration shared across API, prediction, and blockchain logs."""

from __future__ import annotations

import logging
import sys
from typing import Any

from backend.core.config import get_settings


class _JsonFormatter(logging.Formatter):
    """Minimal structured (JSON-ish) formatter — no external deps required."""

    def format(self, record: logging.LogRecord) -> str:
        import json

        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> None:
    """Configure root logging handlers once, based on settings."""
    settings = get_settings()
    root = logging.getLogger()
    if root.handlers:
        return  # already configured (avoid duplicate handlers on reload)

    handler = logging.StreamHandler(sys.stdout)
    if settings.log_json:
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(
            logging.Formatter("%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
        )
    root.addHandler(handler)
    root.setLevel(settings.log_level)


def get_logger(name: str) -> logging.Logger:
    """Return a module-scoped logger, configuring logging on first use."""
    configure_logging()
    return logging.getLogger(name)
