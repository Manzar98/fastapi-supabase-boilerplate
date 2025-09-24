"""
Authentication schemas for request/response models.
"""
from pydantic import BaseModel, EmailStr


class UserLogin(BaseModel):
    """User login request schema."""
    email: EmailStr
    password: str


class UserRegister(BaseModel):
    """User registration request schema."""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Token response schema."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginUserResponse(BaseModel):
    """Login user response schema."""
    username: str
    email: str


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    created_at: str
    updated_at: str


class PasswordReset(BaseModel):
    """Password reset request schema."""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema."""
    token: str
    password: str
