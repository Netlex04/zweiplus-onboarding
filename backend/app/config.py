"""Application configuration (Architektur §9).

Settings are loaded from environment variables (and an optional ``.env`` file).
Defaults are chosen so the app runs locally and in tests without any secrets:
SQLite database and the deterministic ``fake`` AI provider.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/ directory (this file lives in backend/app/config.py)
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Typed application settings, populated from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Database — Postgres at runtime, SQLite default for local/test (Annahme A13).
    database_url: str = Field(default="sqlite:///./zweiplus.db")

    # AI provider seam (Annahme A7) — default deterministic fake, no secret required.
    ai_provider: str = Field(default="fake")  # "fake" | "anthropic"
    anthropic_api_key: str | None = Field(default=None)
    anthropic_model: str = Field(default="claude-opus-4-8")

    # File storage (Annahme A12) + upload limit (Annahme A6).
    storage_dir: str = Field(default=str(BACKEND_DIR / "storage"))
    max_upload_mb: int = Field(default=10)

    # Auth (used from Phase 2). Demo default only — override in production.
    jwt_secret: str = Field(default="dev-insecure-change-me")

    # CORS — comma-separated origins or a list.
    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value: object) -> object:
        """Allow a comma-separated string in addition to a JSON list."""
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            if stripped.startswith("["):  # let pydantic parse JSON lists
                return value
            return [origin.strip() for origin in stripped.split(",") if origin.strip()]
        return value

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()
