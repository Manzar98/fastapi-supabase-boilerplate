"""
Authentication API routes.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from utils.supabase_client import get_supabase_client
from schemas.auth import (
    LoginUserResponse,
    RegisterUserResponse,
    UserLogin,
    UserRegister,
    TokenResponse,
    UserResponse,
    PasswordReset,
    PasswordResetConfirm,
)
from core.dependencies import get_current_user
from core.exceptions import AuthenticationError, ValidationError, create_http_exception

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, supabase=Depends(get_supabase_client)):
    """
    Authenticate user and return Supabase access token.
    """
    try:
        # Authenticate with Supabase
        response = supabase.auth.sign_in_with_password(
            {"email": user.email, "password": user.password}
        )

        if response.user is None or not response.session:
            raise AuthenticationError("Invalid credentials")

        # Return Supabase's tokens directly
        return TokenResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            expires_in=response.session.expires_in,
            refresh_token=response.session.refresh_token,
            user=LoginUserResponse(
                username=response.user.user_metadata.get("username")
                or user.email.split("@")[0],
                email=response.user.email,
                full_name=response.user.user_metadata.get("full_name"),
            ),
        )

    except Exception as e:
        logger.error("Login error: %s", str(e))
        if isinstance(e, (AuthenticationError, ValidationError)):
            raise create_http_exception(e) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(getattr(e, "detail", None)) or "Invalid credentials",
        ) from e


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_token: str, supabase=Depends(get_supabase_client)):
    """
    Refresh access token using refresh token.
    """
    try:
        response = supabase.auth.refresh_session(refresh_token)

        if not response.session:
            raise AuthenticationError("Invalid refresh token")

        return TokenResponse(
            access_token=response.session.access_token,
            token_type="bearer",
            expires_in=response.session.expires_in,
            refresh_token=response.session.refresh_token,
            user=LoginUserResponse(
                username=response.user.user_metadata.get("username")
                or response.user.email.split("@")[0],
                email=response.user.email,
                full_name=response.user.user_metadata.get("full_name"),
            ),
        )

    except Exception as e:
        logger.error("Token refresh error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token refresh failed"
        ) from e


@router.post("/register", response_model=RegisterUserResponse)
async def register(user: UserRegister, supabase=Depends(get_supabase_client)):
    """
    Register a new user.
    """
    try:
        existing_user = (
            supabase.table("users")
            .select("*")
            .eq("email", user.email)
            .maybe_single()  # ✅ handles 0 rows without error
            .execute()
        )

        if existing_user and existing_user.data:
            # User already exists
            u = existing_user.data
            return RegisterUserResponse(
                status="exists",
                message="User is already registered",
                user=UserResponse(
                    id=u["id"],
                    email=u["email"],
                    full_name=u.get("raw_user_meta_data", {}).get("full_name", ""),
                    username=u.get("raw_user_meta_data", {}).get("username", ""),
                    created_at=u["created_at"],
                    updated_at=u["updated_at"],
                ),
            )

        response = supabase.auth.sign_up(
            {
                "email": user.email,
                "password": user.password,
                "options": {
                    "data": {"full_name": user.full_name, "username": user.username}
                },
            }
        )

        if response.user is None:
            raise ValidationError("Registration failed")

        return RegisterUserResponse(
            status="success",
            user=UserResponse(
                id=response.user.id,
                email=response.user.email,
                full_name=user.full_name,
                username=user.username,
                created_at=(
                    response.user.created_at.isoformat()
                    if response.user.created_at
                    else ""
                ),
                updated_at=(
                    response.user.updated_at.isoformat()
                    if response.user.updated_at
                    else ""
                ),
            ),
        )

    except Exception as e:
        logger.error("Registration error: %s", str(e))
        if isinstance(e, (AuthenticationError, ValidationError)):
            raise create_http_exception(e) from e
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Registration failed"
        ) from e


@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user), supabase=Depends(get_supabase_client)
):
    """
    Logout current user and revoke session.
    """
    try:
        # Revoke the current session
        supabase.auth.sign_out()
        return {"message": "Successfully logged out"}
    except Exception as e:
        logger.error("Logout error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed",
        ) from e


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user=Depends(get_current_user)):
    """
    Get current user information.
    """
    return UserResponse(
        id=current_user["id"],
        email=current_user["email"],
        full_name=current_user.get("user_metadata", {}).get("full_name"),
        username=current_user.get("user_metadata", {}).get("username"),
        created_at=(
            current_user["created_at"].isoformat() if current_user["created_at"] else ""
        ),
        updated_at=(
            current_user["updated_at"].isoformat() if current_user["updated_at"] else ""
        ),
    )


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordReset, supabase=Depends(get_supabase_client)
):
    """
    Send password reset email.
    """
    try:
        supabase.auth.reset_password_email(password_reset.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        logger.error("Password reset error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send password reset email",
        ) from e


@router.post("/reset-password")
async def reset_password(
    password_reset_confirm: PasswordResetConfirm, supabase=Depends(get_supabase_client)
):
    """
    Reset password with token.
    """
    try:
        # Set the session using the access_token and refresh_token
        session_response = supabase.auth.set_session(
            password_reset_confirm.token, password_reset_confirm.refresh_token
        )

        if not session_response.session:
            raise ValidationError("Failed to establish session")

        # Now update the password
        update_response = supabase.auth.update_user(
            {"password": password_reset_confirm.password}
        )

        if update_response.user is None:
            raise ValidationError("Password reset failed")

        return {"message": "Password successfully reset"}

    except Exception as e:
        logger.error("Password reset confirm error: %s", str(e))
        if isinstance(e, ValidationError):
            raise create_http_exception(e) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed",
        ) from e
