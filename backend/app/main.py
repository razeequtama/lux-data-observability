"""Main FastAPI application entrypoint for Lux Data Observability Platform."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_v1_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.db.init_db import init_db
from app.schemas.common import HealthResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Application lifespan context manager for startup and shutdown hooks."""
    # Ensure runtime data directories exist
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.scenarios_dir.mkdir(parents=True, exist_ok=True)
    settings.uploads_dir.mkdir(parents=True, exist_ok=True)
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    # Initialize database tables
    init_db()
    yield


def create_app() -> FastAPI:
    """Application factory for the Lux FastAPI backend."""
    app = FastAPI(
        title=settings.project_name,
        openapi_url=f"{settings.api_v1_str}/openapi.json",
        docs_url=f"{settings.api_v1_str}/docs",
        redoc_url=f"{settings.api_v1_str}/redoc",
        lifespan=lifespan,
    )

    # CORS configuration
    cors_regex = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$" if not settings.is_production else None
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=cors_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Centralized error handling
    register_error_handlers(app)

    # API v1 endpoints
    app.include_router(api_v1_router, prefix=settings.api_v1_str)

    # Root health check endpoint
    @app.get(
        "/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        tags=["System"],
        summary="Service Health Check",
    )
    async def health_check() -> HealthResponse:
        """Return application health status."""
        return HealthResponse(status="ok", app="lux")

    # Versioned health check endpoint for consistency
    @app.get(
        f"{settings.api_v1_str}/health",
        response_model=HealthResponse,
        status_code=status.HTTP_200_OK,
        tags=["System"],
        summary="API v1 Health Check",
    )
    async def api_v1_health_check() -> HealthResponse:
        """Return API v1 health status."""
        return HealthResponse(status="ok", app="lux")

    return app


app = create_app()
