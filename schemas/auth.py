"""
Authentication schemas for request/response models.
"""
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    username: Optional[str] = None


class LoginUserResponse(BaseModel):
    """Login user response schema."""
    username: Optional[str] = None
    email: str
    full_name: Optional[str] = None


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str  # Add refresh token
    user: Optional[LoginUserResponse] = None


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    full_name: Optional[str] = None
    username: Optional[str] = None
    created_at: str
    updated_at: str


class RegisterUserResponse(BaseModel):
    """Register user response schema."""
    status: str
    user: UserResponse
    message: Optional[str] = None


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    password: str
    refresh_token: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """User profile update request schema."""
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileResponse(BaseModel):
    """User profile response schema."""
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileUpdateResponse(BaseModel):
    """User profile update response schema."""
    status: str
    user: UserProfileResponse


class DeleteUserResponse(BaseModel):
    """Delete user response schema."""
    status: str
    message: Optional[str] = None
    user: Optional[UserResponse] = None