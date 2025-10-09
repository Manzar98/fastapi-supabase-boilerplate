"""
User profile API routes.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from utils.supabase_client import get_supabase_client
from utils.audit_decorator import audit_action
from schemas.auth import (
    UserProfileResponse,
    UserProfileUpdate,
    UserProfileUpdateResponse,
    DeleteUserResponse,
)
from core.dependencies import get_current_user
from core.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    create_http_exception,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user=Depends(get_current_user), supabase=Depends(get_supabase_client)
):
    """
    Get current user profile information

    Returns:
    UserProfileResponse: User profile information

    Raises:
    AuthenticationError: If user is not authenticated
    NotFoundError: If user profile is not found
    ExternalServiceError: If there is an error fetching user profile
    HTTPException: If there is an error in the request

    """
    try:
        response = supabase.auth.get_user()

        if not response.user:
            raise NotFoundError("User profile not found")

        user_metadata = response.user.user_metadata or {}

        return UserProfileResponse(
            username=user_metadata.get("username"),
            full_name=user_metadata.get("full_name"),
            avatar_url=user_metadata.get("avatar_url"),
        )

    except Exception as e:
        logger.error(
            "Get profile error for user %s: %s",
            current_user.get("id", "unknown"),
            str(e),
        )

        if isinstance(
            e,
            (
                AuthenticationError,
                ValidationError,
                NotFoundError,
                ConflictError,
                ExternalServiceError,
            ),
        ):
            raise create_http_exception(e) from e

        # Handle Supabase specific errors
        if hasattr(e, "message"):
            error_message = str(e.message)
            if "Invalid JWT" in error_message or "JWT expired" in error_message:
                raise create_http_exception(
                    AuthenticationError("Session expired. Please login again.")
                ) from e
            elif "User not found" in error_message:
                raise create_http_exception(
                    NotFoundError("User profile not found")
                ) from e
            else:
                raise create_http_exception(
                    ExternalServiceError(f"Failed to fetch profile: {error_message}")
                ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user profile",
        ) from e


@router.put("/profile", response_model=UserProfileUpdateResponse)
@audit_action("UPDATE", "user")
async def update_user_profile(
    profile_update: UserProfileUpdate,
    request: Request,  # noqa: ARG001
    current_user=Depends(get_current_user),
    supabase=Depends(get_supabase_client),
):
    """
    Update current user profile information

        Args:
        profile_update: Profile update data

    Returns:
    UserProfileUpdateResponse: User profile update information

    Raises:
    AuthenticationError: If user is not authenticated
    ValidationError: If there is an error updating user profile
    ExternalServiceError: If there is an error updating user profile
    HTTPException: If there is an error in the request
    """
    try:
        update_data = {}
        if profile_update.username:
            update_data["username"] = profile_update.username
        if profile_update.full_name:
            update_data["full_name"] = profile_update.full_name
        if profile_update.avatar_url:
            update_data["avatar_url"] = profile_update.avatar_url

        if not update_data:
            raise ValidationError("No profile data provided for update")

        response = supabase.auth.update_user(update_data)

        if not response.user:
            raise ExternalServiceError("Failed to update profile")

        # Get updated user data
        updated_user_metadata = response.user.user_metadata or {}

        updated_profile = UserProfileResponse(
            username=updated_user_metadata.get("username"),
            full_name=updated_user_metadata.get("full_name"),
            avatar_url=updated_user_metadata.get("avatar_url"),
        )

        return UserProfileUpdateResponse(status="success", user=updated_profile)

    except Exception as e:
        logger.error(
            "Update profile error for user %s: %s",
            current_user.get("id", "unknown"),
            str(e),
        )

        if isinstance(
            e,
            (
                AuthenticationError,
                ValidationError,
                NotFoundError,
                ConflictError,
                ExternalServiceError,
            ),
        ):
            raise create_http_exception(e) from e

        # Handle Supabase specific errors
        if hasattr(e, "message"):
            error_message = str(e.message)
            if "Invalid JWT" in error_message or "JWT expired" in error_message:
                raise create_http_exception(
                    AuthenticationError("Session expired. Please login again.")
                ) from e
            elif "User not found" in error_message:
                raise create_http_exception(
                    NotFoundError("User profile not found")
                ) from e
            elif (
                "already exists" in error_message.lower()
                or "duplicate" in error_message.lower()
            ):
                raise create_http_exception(
                    ConflictError(
                        "Username already exists. Please choose a different username."
                    )
                ) from e
            elif "validation" in error_message.lower():
                raise create_http_exception(
                    ValidationError(f"Invalid profile data: {error_message}")
                ) from e
            else:
                raise create_http_exception(
                    ExternalServiceError(f"Failed to update profile: {error_message}")
                ) from e

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile",
        ) from e


@router.delete("/", response_model=DeleteUserResponse)
@audit_action("DELETE", "user")
async def delete_user(
    request: Request,  # noqa: ARG001
    current_user=Depends(get_current_user),  # noqa: ARG001
    supabase=Depends(get_supabase_client)
):
    """
    Delete current user account
    """
    try:
        response = supabase.auth.delete_user()

        if not response.user:
            raise ExternalServiceError("Failed to delete user")

        return DeleteUserResponse(status="success", message="User deleted successfully")

    except Exception as e:
        logger.error("Delete user error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        ) from e
