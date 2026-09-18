from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized configuration for NiyamTrace-X.
    Uses pydantic-settings to load from environment variables or .env file.
    """

    environment: Literal["development", "production", "test"] = Field(
        default="development", description="Deployment environment."
    )
    debug_mode: bool = Field(
        default=False, description="Enable debug logging and features."
    )
    
    # Auth
    auth_enabled: bool = Field(
        default=True, description="Enable authentication and authorization."
    )
    auth_secret_key: str | None = Field(
        default=None, description="Secret key for JWT verification (required in prod)."
    )

    # LLM Settings
    llm_backend: Literal["openai", "groq", "google", "gemini", "local"] = Field(
        default="openai", description="The LLM provider backend to use."
    )
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    gemini_api_key: str | None = None

    # Database
    erp_db_type: Literal["sqlite", "postgres"] = Field(
        default="sqlite", description="Database backend for ERP."
    )
    erp_db_url: str = Field(
        default="sqlite:///niyamtrace/data/synthetic/erp.db",
        description="Database URL for the ERP connection.",
    )

    # API Security
    cors_allowed_origins: list[str] = Field(
        default=["*"], description="Allowed CORS origins."
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @field_validator("debug_mode", mode="before")
    def restrict_debug_in_prod(cls, v, info):
        # info.data contains previously validated fields like environment
        if info.data.get("environment") == "production" and v is True:
            raise ValueError("Debug mode must not be enabled in production environment.")
        return v

    @field_validator("auth_secret_key", mode="before")
    def require_auth_in_prod(cls, v, info):
        if info.data.get("environment") == "production":
            if not info.data.get("auth_enabled", True):
                raise ValueError("Authentication must be enabled in production.")
            if not v:
                raise ValueError("auth_secret_key is missing, but required for production auth.")
        return v

    @field_validator("erp_db_type", mode="before")
    def restrict_sqlite_in_prod(cls, v, info):
        # We reject production mode with SQLite unless explicitly permitted (not yet implemented override)
        if info.data.get("environment") == "production" and v == "sqlite":
            raise ValueError("SQLite is not allowed in production unless explicitly permitted.")
        return v

    @field_validator("cors_allowed_origins", mode="before")
    def restrict_wildcard_cors_in_prod(cls, v, info):
        if info.data.get("environment") == "production":
            if "*" in v or ["*"] == v:
                raise ValueError("Wildcard CORS (*) is not permitted in production.")
        return v


@lru_cache()
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
