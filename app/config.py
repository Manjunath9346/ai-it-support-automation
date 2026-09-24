"""
Application configuration.
Loads values from backend/.env
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


# ============================================================
# PATHS
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parent.parent

ENV_FILE = BACKEND_DIR / ".env"


# ============================================================
# SETTINGS
# ============================================================

class Settings(BaseSettings):

    # Application
    app_name: str = Field(
        default="AI IT Support Automation",
        alias="APP_NAME"
    )

    app_env: str = Field(
        default="development",
        alias="APP_ENV"
    )

    debug: bool = Field(
        default=True,
        alias="DEBUG"
    )

    log_level: str = Field(
        default="INFO",
        alias="LOG_LEVEL"
    )

    host: str = Field(
        default="127.0.0.1",
        alias="HOST"
    )

    port: int = Field(
        default=8000,
        alias="PORT"
    )


    # ========================================================
    # DATABASE
    # ========================================================

    database_url: str | None = Field(
        default=None,
        alias="DATABASE_URL"
    )

    aiven_ca_cert: str | None = Field(
        default=None,
        alias="AIVEN_CA_CERT"
    )


    # ========================================================
    # N8N
    # ========================================================

    n8n_api_url: str | None = Field(
        default=None,
        alias="N8N_API_URL"
    )


    # ========================================================
    # LLM
    # ========================================================

    llm_enabled: bool = Field(
        default=False,
        alias="LLM_ENABLED"
    )

    llm_api_url: str | None = Field(
        default=None,
        alias="LLM_API_URL"
    )

    llm_api_key: str | None = Field(
        default=None,
        alias="LLM_API_KEY"
    )

    llm_model: str | None = Field(
        default=None,
        alias="LLM_MODEL"
    )


    # ========================================================
    # SMTP
    # ========================================================

    smtp_enabled: bool = Field(
        default=False,
        alias="SMTP_ENABLED"
    )

    smtp_host: str | None = Field(
        default=None,
        alias="SMTP_HOST"
    )

    smtp_port: int = Field(
        default=587,
        alias="SMTP_PORT"
    )

    smtp_username: str | None = Field(
        default=None,
        alias="SMTP_USERNAME"
    )

    smtp_password: str | None = Field(
        default=None,
        alias="SMTP_PASSWORD"
    )

    support_email: str | None = Field(
        default=None,
        alias="SUPPORT_EMAIL"
    )


    # ========================================================
    # JWT
    # ========================================================

    jwt_secret: str = Field(
        default="change-this-secret",
        alias="JWT_SECRET"
    )


    # ========================================================
    # PYDANTIC SETTINGS
    # ========================================================

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


# ============================================================
# SETTINGS INSTANCE
# ============================================================

@lru_cache
def get_settings() -> Settings:
    return Settings()


# Your main.py expects:
#
# from app.config import settings
#
# Therefore expose the settings object directly.

settings = get_settings()