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


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginUserResponse(BaseModel):
    """Login user response schema."""
    username: str
    email: str
    full_name: str


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    full_name: Optional[str] = None
    created_at: str
    updated_at: str


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    password: str
