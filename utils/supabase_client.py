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

