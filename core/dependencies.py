"""
Dependency injection for FastAPI.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from supabase import Client
from utils.supabase import get_supabase_client, verify_with_supabase
from middlewares.jwt_middleware import verify_jwt_token_locally
from core.exceptions import AuthenticationError, create_http_exception

# Security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """
    Get current authenticated user from JWT token (local verification).
    
    Args:
        credentials: HTTP Bearer token credentials
        
    Returns:
        dict: User information
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        token = credentials.credentials
        
        # Verify token locally (faster, no network call)
        return verify_jwt_token_locally(token)
        
    except Exception as e:
        if isinstance(e, AuthenticationError):
            raise create_http_exception(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[dict]:
    """
    Get current user if authenticated, otherwise return None.
    
    Args:
        credentials: HTTP Bearer token credentials (optional)
        
    Returns:
        dict or None: User information if authenticated, None otherwise
    """
    if not credentials:
        return None
        
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


