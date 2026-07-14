"""Application configuration loaded from the environment via Pydantic Settings."""

from functools import lru_cache

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings.

    Values are read from environment variables (or a local ``.env`` file).
    No other module should read environment variables directly.
    """

    app_name: str = "AI-Assisted Counseling Simulator"
    app_env: str = "development"
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/counseling_simulator"
    )

    gemini_api_key: str = "replace_me"
    ai_provider: str = "gemini_developer_api"
    google_cloud_project: str | None = None
    google_cloud_location: str = "global"
    gemini_client_model: str = "gemini-2.0-flash"
    gemini_evaluator_model: str = "gemini-2.0-flash"

    # Comma-separated string in the environment; parsed via ``cors_origins``.
    cors_origins_raw: str = Field(
        default="http://localhost:5173",
        validation_alias=AliasChoices("CORS_ORIGINS", "cors_origins_raw"),
    )

    max_session_messages: int = 20
    min_student_messages: int = 4

    # Text limits (see Backend.md security requirements).
    student_message_min_length: int = 1
    student_message_max_length: int = 2000
    ai_response_max_length: int = 1500

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Parsed list of allowed CORS origins."""
        return [
            origin.strip()
            for origin in self.cors_origins_raw.split(",")
            if origin.strip()
        ]

    @property
    def gemini_configured(self) -> bool:
        """True when the selected Gemini provider has its required configuration."""
        if self.ai_provider == "vertex_ai":
            return bool(self.google_cloud_project and self.google_cloud_location)
        return bool(self.gemini_api_key) and self.gemini_api_key != "replace_me"


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
