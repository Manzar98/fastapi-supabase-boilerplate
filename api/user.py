"""
User profile API routes.
"""

import logging

from fastapi import APIRouter, Depends, Request

from core.dependencies import get_current_user
from core.exceptions import (ExternalServiceError, NotFoundError,
                             ValidationError)
from schemas.auth import (DeleteUserResponse, UserProfileResponse,
                          UserProfileUpdate, UserProfileUpdateResponse)
from utils.audit_decorator import audit_action
from utils.supabase_client import get_supabase_client

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
    response = supabase.auth.get_user()

    if not response.user:
        raise NotFoundError("User profile not found")

    user_metadata = response.user.user_metadata or {}

    return UserProfileResponse(
        username=user_metadata.get("username"),
        full_name=user_metadata.get("full_name"),
        avatar_url=user_metadata.get("avatar_url"),
    )


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
    update_data = {}
    if profile_update.username:
        update_data["username"] = profile_update.username
    if profile_update.full_name:
        update_data["full_name"] = profile_update.full_name
    if profile_update.avatar_url:
        update_data["avatar_url"] = profile_update.avatar_url

    if not update_data:
        raise ValidationError("No profile data provided for update")

    # Update user metadata in Supabase Auth
    response = supabase.auth.update_user({"data": update_data})

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


@router.delete("/", response_model=DeleteUserResponse)
@audit_action("DELETE", "user")
async def delete_user(
    request: Request,  # noqa: ARG001
    current_user=Depends(get_current_user),  # noqa: ARG001
    supabase=Depends(get_supabase_client),
):
    """
    Delete current user account
    """
    response = supabase.auth.delete_user()

    if not response.user:
        raise ExternalServiceError("Failed to delete user")

    return DeleteUserResponse(status="success", message="User deleted successfully")
