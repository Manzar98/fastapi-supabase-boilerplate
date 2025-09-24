from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from typing import Optional
from utils.supabase import get_supabase_client
from schemas.auth import (
    UserLogin, 
    UserRegister, 
    TokenResponse, 
    UserResponse, 
    PasswordReset, 
    PasswordResetConfirm
)
from core.dependencies import get_current_user
from core.exceptions import AuthenticationError, ValidationError, create_http_exception
from core.config import settings
from jose import jwt
from datetime import datetime, timedelta, timezone
import logging

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token.
    
    Args:
        data: Data to encode in the token
        expires_delta: Token expiration time
        
    Returns:
        str: JWT token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "iss": settings.app_name
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, supabase=Depends(get_supabase_client)):
    """
    Authenticate user and return JWT token.
    """
    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password({
            "email": user.email,
            "password": user.password
        })
        
        if response.user is None:
            raise AuthenticationError("Invalid credentials")
        
        # Create local JWT token with user data
        token_data = {
            "sub": response.user.id,
            "email": response.user.email,
            "user_metadata": response.user.user_metadata,
            "app_metadata": response.user.app_metadata,
            "role": response.user.app_metadata.get("role", "user")
        }
        
        access_token = create_access_token(token_data)
        expires_in = settings.jwt_access_token_expire_minutes * 60
        
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=expires_in
        )
        
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        if isinstance(e, AuthenticationError):
            raise create_http_exception(e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )


@router.post("/register", response_model=UserResponse)
async def register(user: UserRegister, supabase=Depends(get_supabase_client)):
    """
    Register a new user.
    """
    try:
        response = supabase.auth.sign_up({
            "email": user.email,
            "password": user.password,
            "options": {
                "data": {
                    "full_name": user.full_name
                }
            }
        })
        
        if response.user is None:
            raise ValidationError("Registration failed")
            
        return UserResponse(
            id=response.user.id,
            email=response.user.email,
            full_name=user.full_name,
            created_at=response.user.created_at,
            updated_at=response.user.updated_at
        )
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        if isinstance(e, (AuthenticationError, ValidationError)):
            raise create_http_exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed"
        )


@router.post("/logout")
async def logout(supabase=Depends(get_supabase_client)):
    """
    Logout current user.
    """
    try:
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error(f"Logout error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("user_metadata", {}).get("full_name"),
        created_at=current_user["created_at"],
        updated_at=current_user["updated_at"]
    )


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset, 
    supabase=Depends(get_supabase_client)
):
    """
    Send password reset email.
    """
    try:
        supabase.auth.reset_password_email(password_reset.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email"
        )


@router.post("/reset-password")
async def reset_password(
    password_reset_confirm: PasswordResetConfirm,
    supabase=Depends(get_supabase_client)
):
    """
    Reset password with token.
    """
    try:
        response = supabase.auth.update_user({
            "password": password_reset_confirm.password
        })
        
        if response.user is None:
            raise ValidationError("Password reset failed")
            
        return {"message": "Password successfully reset"}
        
    except Exception as e:
        logger.error(f"Password reset confirm error: {str(e)}")
        if isinstance(e, ValidationError):
            raise create_http_exception(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset failed"
        )