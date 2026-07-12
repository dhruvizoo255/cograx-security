"""Thin HTTP client wrapping the Cograx Security backend API."""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests


class ApiClient:
    """Talks to the FastAPI backend. Sends ``X-API-Key`` whenever an API key
    is configured, so the dashboard keeps working once the backend requires
    one in production (``COGRAX_API_KEY`` set on both sides)."""

    def __init__(
        self, base_url: str, api_key: Optional[str] = None, timeout: float = 30.0
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key or None
        self._timeout = timeout

    def _headers(self) -> Dict[str, str]:
        return {"X-API-Key": self._api_key} if self._api_key else {}

    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(
            f"{self._base_url}/api/v1/predict",
            json=payload,
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()

    def report(self, prediction_id: str, payload: Dict[str, Any]) -> bytes:
        resp = requests.post(
            f"{self._base_url}/api/v1/predict/{prediction_id}/report",
            json=payload,
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.content

    def health(self) -> Dict[str, Any]:
        resp = requests.get(f"{self._base_url}/health", timeout=self._timeout)
        resp.raise_for_status()
        return resp.json()

    def metrics(self) -> Dict[str, Any]:
        resp = requests.get(
            f"{self._base_url}/metrics",
            headers=self._headers(),
            timeout=self._timeout,
        )
        resp.raise_for_status()
        return resp.json()
