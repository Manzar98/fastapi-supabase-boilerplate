"""
Supabase client utility.
"""
import logging
from functools import lru_cache
from supabase import create_client, Client
from fastapi import HTTPException, status
from core.config import settings
from core.exceptions import AuthenticationError

logger = logging.getLogger(__name__)


@lru_cache
def get_supabase_client() -> Client:
    """
    Get Supabase client instance (singleton).
    """
    try:
        client = create_client(
            settings.supabase_url,
            settings.supabase_key,
        )
        logger.info("Supabase client initialized successfully")
        return client
    except Exception as e:
        logger.error("Failed to initialize Supabase client: %s", str(e))
        raise


@lru_cache
def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client instance with service role key.
    """
    if not settings.supabase_service_role_key:
        raise ValueError("Service role key not configured")

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )


def verify_with_supabase(token: str) -> dict:
    """
    Verify JWT token with Supabase (for double-checking user state).
    """
    try:
        supabase = get_supabase_client()
        response = supabase.auth.get_user(token)

        if not response.user:
            raise AuthenticationError("Invalid token")

        return {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
            "app_metadata": response.user.app_metadata,
            "created_at": response.user.created_at,
            "updated_at": response.user.updated_at,
            "username": response.user.user_metadata.get("username", "user"),
        }

    except Exception as e:
        logger.error("Supabase verification error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase verification failed",
        ) from e
