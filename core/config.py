"""
Application configuration settings.
"""

import os
import warnings
from typing import List, Optional
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings(BaseModel):
    """Application settings."""

    # Application
    app_name: str = "FastAPI Supabase Boilerplate"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # Supabase
    supabase_url: str = os.getenv("SUPABASE_URL")
    supabase_key: str = os.getenv("SUPABASE_KEY")
    supabase_service_role_key: Optional[str] = None

    # Database
    database_url: Optional[str] = None

    # JWT
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30

    # CORS
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "https://your-frontend-domain.com",
    ]

    # Logging
    log_level: str = "INFO"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        """Assemble CORS origins."""
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """
        Validate environment.
        """
        allowed_envs = ["development", "staging", "production"]
        if v not in allowed_envs:
            raise ValueError(f"Environment must be one of {allowed_envs}")
        return v

    def __init__(self, **data):
        super().__init__(**data)

        # Warn if using default values
        if self.supabase_url == os.getenv("SUPABASE_URL"):
            warnings.warn(
                "Using default Supabase URL. Please set SUPABASE_URL in your .env file.",
                UserWarning,
            )

        if self.supabase_key == os.getenv("SUPABASE_KEY"):
            warnings.warn(
                "Using default Supabase key. Please set SUPABASE_KEY in your .env file.",
                UserWarning,
            )

        if self.jwt_secret_key == os.getenv("JWT_SECRET_KEY"):
            warnings.warn(
                (
                    "Using default JWT secret key. "
                    "Please set JWT_SECRET_KEY in your .env file for security."
                ),
                UserWarning,
            )

    model_config = {"env_file": ".env", "case_sensitive": False}


# Global settings instance
settings = Settings()
