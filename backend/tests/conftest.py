"""Shared pytest fixtures for the Lux test suite."""

from collections.abc import AsyncGenerator, Generator

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
def client() -> Generator[TestClient]:
    """Synchronous test client fixture."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient]:
    """Asynchronous HTTP test client fixture."""
    async with AsyncClient(
        transport=ASGITransport(app=app),  # type: ignore[arg-type]
        base_url="http://testserver",
    ) as ac:
        yield ac
