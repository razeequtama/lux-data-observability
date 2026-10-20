"""Database connection, engine configuration, and session factory."""

import sqlite3
from collections.abc import Generator
from typing import Any

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


@event.listens_for(Engine, "connect")
def configure_sqlite_connection(dbapi_connection: Any, connection_record: Any) -> None:
    """Configure SQLite pragmas for performance and data integrity.

    - PRAGMA journal_mode=WAL: Write-Ahead Logging for non-blocking concurrent readers.
    - PRAGMA foreign_keys=ON: Enforce foreign key constraints and cascading operations.
    - PRAGMA busy_timeout=5000: Wait up to 5000ms if database is locked by concurrent writer.
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.close()


connect_args: dict[str, Any] = {}
if settings.db_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.db_url,
    connect_args=connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=Session,
)


def get_db() -> Generator[Session]:
    """Dependency for FastAPI endpoints yielding a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
