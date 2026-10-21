"""Custom exceptions and centralized error envelope handlers."""

import logging
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("lux.errors")


class LuxException(Exception):
    """Base application exception for Lux with structured code and details."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFoundError(LuxException):
    """Resource not found exception."""

    def __init__(
        self,
        code: str = "RESOURCE_NOT_FOUND",
        message: str = "The requested resource was not found.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


HTTP_413_STATUS = getattr(status, "HTTP_413_CONTENT_TOO_LARGE", 413)


class PayloadTooLargeError(LuxException):
    """Payload exceeds allowed limit."""

    def __init__(
        self,
        code: str = "PAYLOAD_TOO_LARGE",
        message: str = "Uploaded file exceeds maximum allowed limit (20MB).",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=HTTP_413_STATUS,
            details=details,
        )


class CyclicDependencyError(LuxException):
    """Raised when a lineage dependency cycle is detected in the DAG."""

    def __init__(
        self,
        message: str = "Lineage graph contains cyclic dependencies.",
        cycle_path: list[str] | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        details_dict = details.copy() if details else {}
        if cycle_path is not None:
            details_dict["cycle_path"] = cycle_path
        super().__init__(
            code="CYCLIC_DEPENDENCY",
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details_dict,
        )
        self.cycle_path: list[str] = cycle_path or []


class LineageIntegrityError(LuxException):
    """Raised when graph integrity constraints (e.g. dangling edges, missing nodes) are violated."""

    def __init__(
        self,
        message: str = "Lineage graph integrity validation failed.",
        code: str = "LINEAGE_INTEGRITY_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details or {},
        )


def format_error_payload(
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Format payload conforming to Lux standard error envelope."""
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now(UTC).isoformat(),
        }
    }


async def lux_exception_handler(_: Request, exc: LuxException) -> JSONResponse:
    """Handle custom Lux exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_payload(code=exc.code, message=exc.message, details=exc.details),
    )


async def http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard Starlette / FastAPI HTTP exceptions."""
    detail: object = exc.detail
    code = "HTTP_ERROR"
    details: dict[str, Any] = {}
    message: str

    if isinstance(detail, dict):
        code = str(detail.get("code", code))
        message = str(detail.get("message", str(detail)))
        raw_details = detail.get("details")
        if isinstance(raw_details, dict):
            details = raw_details
    elif isinstance(detail, str):
        message = detail
        if exc.status_code == status.HTTP_404_NOT_FOUND:
            code = "NOT_FOUND"
        elif exc.status_code == status.HTTP_403_FORBIDDEN:
            code = "FORBIDDEN"
        elif exc.status_code == status.HTTP_401_UNAUTHORIZED:
            code = "UNAUTHORIZED"
        elif exc.status_code == status.HTTP_400_BAD_REQUEST:
            code = "BAD_REQUEST"
        elif exc.status_code == 413:
            code = "PAYLOAD_TOO_LARGE"
    else:
        message = str(detail)

    return JSONResponse(
        status_code=exc.status_code,
        content=format_error_payload(code=code, message=message, details=details),
    )


async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle FastAPI / Pydantic request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=format_error_payload(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            details={"errors": exc.errors()},
        ),
    )


async def generic_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unhandled internal server errors."""
    logger.exception("Unhandled exception occurred: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=format_error_payload(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected server error occurred.",
            details={},
        ),
    )


def register_error_handlers(app: FastAPI) -> None:
    """Register all centralized error handlers on the FastAPI application."""
    app.add_exception_handler(LuxException, lux_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, validation_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, generic_exception_handler)
