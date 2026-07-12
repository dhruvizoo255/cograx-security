"""
Cograx Security API — FastAPI application entrypoint.

Run locally with:
    uvicorn backend.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from backend.api.routes import prediction_routes, system_routes
from backend.core.config import get_settings
from backend.core.exceptions import register_exception_handlers
from backend.core.logging_config import configure_logging, get_logger

settings = get_settings()
configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Explainable AI-powered smart contract security risk assessment "
        "platform with immutable blockchain audit trails."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.trusted_hosts)

register_exception_handlers(app)

app.include_router(system_routes.router)
app.include_router(prediction_routes.router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info(
        "Starting %s v%s (%s)",
        settings.app_name,
        settings.app_version,
        settings.environment,
    )


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
    }
