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
        # Debug: Print the values being used
        print(f"DEBUG: SUPABASE_URL = {settings.supabase_url}")
        print(f"DEBUG: SUPABASE_KEY = {settings.supabase_key[:10] if settings.supabase_key else None}...")
        
        if not settings.supabase_url:
            raise ValueError("SUPABASE_URL is not configured")
        if not settings.supabase_key:
            raise ValueError("SUPABASE_KEY is not configured")
            
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

    # Debug: Print the values being used
    print(f"DEBUG: SUPABASE_URL = {settings.supabase_url}")
    print(f"DEBUG: SUPABASE_SERVICE_ROLE_KEY = {settings.supabase_service_role_key[:10] if settings.supabase_service_role_key else None}...")

    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
    )

