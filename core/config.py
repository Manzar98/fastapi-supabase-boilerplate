"""
Application configuration settings.
"""

import os
import warnings
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

# Load environment variables from .env
load_dotenv()


class Settings(BaseModel):
    """Application settings."""

    # Application
    app_name: str = "FastAPI Supabase Boilerplate"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Supabase
    supabase_url: Optional[str] = os.getenv("SUPABASE_URL")
    supabase_key: Optional[str] = os.getenv("SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    # Database
    database_url: Optional[str] = os.getenv("DATABASE_URL")

    # ✅ CORS — now loaded from .env
    cors_origins: List[str] = os.getenv("CORS_ORIGINS", "")

    # Resend
    resend_api_key: Optional[str] = os.getenv("RESEND_API_KEY")
    resend_from_email: Optional[str] = os.getenv("RESEND_FROM_EMAIL")

    # App URL
    app_url: Optional[str] = os.getenv("BASE_URL")

    # Sentry
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN")

    # Logging
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Assemble CORS origins from a comma-separated string."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v

    def __init__(self, **data):
        super().__init__(**data)

        # Warnings if env vars are missing
        if not self.supabase_url:
            warnings.warn(
                "SUPABASE_URL is not set. Please configure it in your .env file.",
                UserWarning,
            )

        if not self.supabase_key:
            warnings.warn(
                "SUPABASE_KEY is not set. Please configure it in your .env file.",
                UserWarning,
            )

    model_config = {"env_file": ".env", "case_sensitive": False}


# Global settings instance
settings = Settings()
