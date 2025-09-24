"""
Supabase client utility.
"""
from supabase import create_client, Client
from core.config import settings
from core.exceptions import AuthenticationError
from fastapi import HTTPException
import logging

logger = logging.getLogger(__name__)

# Global Supabase client instance
_supabase_client: Client = None


def get_supabase_client() -> Client:
    """
    Get Supabase client instance.
    
    Returns:
        Client: Supabase client instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        try:
            _supabase_client = create_client(
                settings.supabase_url,
                settings.supabase_key
            )
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {str(e)}")
            raise
    
    return _supabase_client


def get_supabase_admin_client() -> Client:
    """
    Get Supabase admin client instance with service role key.
    
    Returns:
        Client: Supabase admin client instance
    """
    if not settings.supabase_service_role_key:
        raise ValueError("Service role key not configured")
    
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key
    )


def verify_with_supabase(token: str) -> dict:
    """
    Verify JWT token with Supabase (for double-checking user state).
    Use this when you need to verify user state with Supabase, e.g., for admin checks.
    
    Args:
        token: JWT token to verify with Supabase
        
    Returns:
        dict: User information from Supabase
        
    Raises:
        HTTPException: If verification fails
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
            "role": response.user.app_metadata.get("role", "user")
        }
        
    except Exception as e:
        logger.error(f"Supabase verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Supabase verification failed"
        )