"""Common Pydantic schemas across API endpoints."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = "ok"
    app: str = "lux"


class ErrorDetail(BaseModel):
    """Standard error detail object conforming to API specification."""

    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class ErrorResponse(BaseModel):
    """Standard error envelope for all 4xx/5xx responses."""

    error: ErrorDetail
