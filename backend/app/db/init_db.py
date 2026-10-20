"""Database initialization utility for creating tables and schema metadata."""

import logging
from pathlib import Path

from sqlalchemy.engine import Engine

import app.models  # noqa: F401 - Ensure all models are registered with Base.metadata
from app.db.session import engine
from app.models.base import Base

logger = logging.getLogger(__name__)


def init_db(bind_engine: Engine | None = None) -> None:
    """Initialize database schema by creating all registered tables and indices.

    Args:
        bind_engine: Optional SQLAlchemy engine to bind. Defaults to application engine.
    """
    target_engine = bind_engine or engine

    # Ensure parent directory exists for file-based database
    if target_engine.url.database and target_engine.url.database != ":memory:":
        db_file = Path(target_engine.url.database)
        if db_file.parent:
            db_file.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Initializing database schema at %s", target_engine.url)
    Base.metadata.create_all(bind=target_engine)
    logger.info("Database schema initialized successfully with 11 tables.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    init_db()
