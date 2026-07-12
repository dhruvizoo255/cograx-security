"""API-key authentication and dependency-free fixed-window rate limiting.

Two dependencies are exposed:

- ``require_api_key`` -- authentication only. Applied to every endpoint that
  reads audit/report/metrics data, since that data must not be publicly
  enumerable once an API key is configured.
- ``protect_prediction_endpoint`` -- authentication *and* per-client rate
  limiting. Applied to the inference endpoint, which is the most
  expensive/abusable call in the API.

Both no-op (allow the request) when ``COGRAX_API_KEY`` is unset, which is the
local-development default. Production config validation (see
``backend.core.config``) refuses to start without an API key set, so in a
production deployment both dependencies are always enforced.
"""

from __future__ import annotations

import hmac
import time
from collections import defaultdict, deque

from fastapi import Header, HTTPException, Request, status

from backend.core.config import get_settings

_requests: dict[str, deque[float]] = defaultdict(deque)


def _check_api_key(x_api_key: str | None) -> None:
    settings = get_settings()
    if settings.api_key and not hmac.compare_digest(x_api_key or "", settings.api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key."
        )


async def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    """Authenticate a request. No rate limiting -- used for read endpoints
    (audit lookups, listings, reports, metrics) that must not be publicly
    enumerable once an API key is configured."""
    _check_api_key(x_api_key)


async def protect_prediction_endpoint(
    request: Request, x_api_key: str | None = Header(default=None)
) -> None:
    """Authenticate and rate-limit a request. Used for the inference
    endpoint, which is the most expensive call in the API."""
    settings = get_settings()
    _check_api_key(x_api_key)
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = _requests[client]
    while window and window[0] <= now - 60:
        window.popleft()
    if len(window) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded."
        )
    window.append(now)
