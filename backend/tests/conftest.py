"""Shared pytest fixtures for the Lux test suite."""

from collections.abc import AsyncGenerator, Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.init_db import init_db
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


@pytest.fixture
def tmp_db_engine(tmp_path: Path) -> Generator[Engine]:
    """Provide a clean SQLite database engine with WAL mode in a temporary directory."""
    db_file = tmp_path / "test_lux.db"
    db_url = f"sqlite:///{db_file.resolve()}"
    test_engine = create_engine(
        db_url,
        connect_args={"check_same_thread": False},
        pool_pre_ping=True,
    )
    init_db(test_engine)
    yield test_engine
    test_engine.dispose()


@pytest.fixture
def db_session(tmp_db_engine: Engine) -> Generator[Session]:
    """Provide an isolated database session for testing."""
    session_factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=tmp_db_engine,
        class_=Session,
    )
    session = session_factory()
    try:
        yield session
    finally:
        session.close()
