"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
DEFAULT_DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    """Lux platform settings loaded from environment or defaults."""

    model_config = SettingsConfigDict(
        env_prefix="LUX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_name: str = Field(default="Lux Data Observability", description="Application name")
    api_v1_str: str = Field(default="/api/v1", description="API v1 prefix")
    env: str = Field(
        default="development",
        description="Runtime environment: development, test, production",
    )
    log_level: str = Field(default="INFO", description="Logging level")
    data_dir: Path = Field(
        default=DEFAULT_DATA_DIR,
        description="Root path for data files, scenarios, and artifacts",
    )
    database_url: str | None = Field(
        default=None,
        description="Database connection URL. If None, derived from sqlite_db_path",
    )
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        description="Allowed CORS origins",
    )
    max_upload_size_bytes: int = Field(
        default=20 * 1024 * 1024,
        description="Maximum file upload size in bytes (20 MB default)",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | list[str]) -> list[str]:
        """Parse comma-separated origins if provided as a single string."""
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        if isinstance(v, list):
            return v
        return []

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.env.lower() == "production"

    @property
    def scenarios_dir(self) -> Path:
        """Path to bundled scenarios directory."""
        return self.data_dir / "scenarios"

    @property
    def uploads_dir(self) -> Path:
        """Path to ephemeral uploads directory."""
        return self.data_dir / "uploads"

    @property
    def artifacts_dir(self) -> Path:
        """Path to generated report artifacts directory."""
        return self.data_dir / "artifacts"

    @property
    def sqlite_db_path(self) -> Path:
        """Path to SQLite database file."""
        return self.data_dir / "lux.db"

    @property
    def db_url(self) -> str:
        """SQLAlchemy database connection URL."""
        if self.database_url:
            return self.database_url
        return f"sqlite:///{self.sqlite_db_path.resolve()}"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton instance."""
    return Settings()


settings = get_settings()
