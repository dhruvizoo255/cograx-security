"""Custom exception hierarchy and FastAPI exception handlers."""

from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from backend.core.logging_config import get_logger

logger = get_logger(__name__)


class CograxError(Exception):
    """Base class for all application-specific errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    default_message: str = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        self.message = message or self.default_message
        super().__init__(self.message)


class FeatureValidationError(CograxError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    default_message = "One or more input features are invalid."


class ModelNotLoadedError(CograxError):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_message = "The prediction model is not currently loaded."


class BlockchainError(CograxError):
    status_code = status.HTTP_502_BAD_GATEWAY
    default_message = "Blockchain interaction failed."


class AuditNotFoundError(CograxError):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = "Requested audit record was not found."


def register_exception_handlers(app: FastAPI) -> None:
    """Attach handlers so every CograxError (and unhandled Exception) returns
    a consistent JSON envelope instead of leaking stack traces."""

    @app.exception_handler(CograxError)
    async def handle_cograx_error(request: Request, exc: CograxError) -> JSONResponse:
        logger.warning("Handled error on %s: %s", request.url.path, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "detail": exc.message},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "InternalServerError", "detail": "Something went wrong."},
        )
