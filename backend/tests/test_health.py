"""Tests for service health check, error handling envelope, and base configuration."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient


def test_health_check_returns_200(client: TestClient) -> None:
    """Verify that GET /health returns HTTP 200 with expected payload."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "app": "lux"}


def test_api_v1_health_check_returns_200(client: TestClient) -> None:
    """Verify that GET /api/v1/health also returns HTTP 200 with expected payload."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "ok", "app": "lux"}


def test_error_envelope_on_404(client: TestClient) -> None:
    """Verify that non-existent routes return the standardized error envelope."""
    response = client.get("/api/v1/nonexistent-route-for-testing")
    assert response.status_code == 404
    data = response.json()

    assert "error" in data
    error = data["error"]
    assert "code" in error
    assert "message" in error
    assert "details" in error
    assert "timestamp" in error
    assert error["code"] == "NOT_FOUND"


def test_cors_headers_on_preflight(client: TestClient) -> None:
    """Verify that CORS preflight requests succeed with appropriate headers."""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


@pytest.mark.asyncio
async def test_async_health_check(async_client: AsyncClient) -> None:
    """Verify that asynchronous client test harness operates properly."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "app": "lux"}
