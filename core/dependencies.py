"""
Dependency injection for FastAPI.
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from utils.supabase_client import get_supabase_client
from core.exceptions import AuthenticationError, create_http_exception

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    supabase=Depends(get_supabase_client)
) -> dict:
    """
    Get current authenticated user using Supabase access token.

    Args:
        credentials: HTTP Bearer token credentials
        supabase: Supabase client dependency

    Returns:
        dict: User information from Supabase

    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        
        # Verify token with Supabase (real-time validation)
        response = supabase.auth.get_user(token)

        if not response.user:
            raise AuthenticationError("Invalid Token")

        # Extract user information
        user_data = {
            "id": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata or {},
            "app_metadata": response.user.app_metadata or {},
            "role": (
                response.user.app_metadata.get("role", "user")
                if response.user.app_metadata
                else "user"
            ),
            "created_at": response.user.created_at,
            "updated_at": response.user.updated_at,
        }

        logging.info("User authenticated: %s (%s)", user_data["email"], user_data["id"])
        return user_data
    except Exception as e:
        if isinstance(e, AuthenticationError):
            raise create_http_exception(e) from e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from e


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    supabase=Depends(get_supabase_client)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.

    Args:
        credentials: HTTP Bearer token credentials (optional)
        supabase: Supabase client dependency

    Returns:
        dict or None: User information if authenticated, None otherwise
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials, supabase)
    except HTTPException:
        return None
