"""
Custom exceptions for the application.
"""

from typing import Any, Dict, Optional

from fastapi import HTTPException


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(AppException):
    """Authentication related errors."""

    def __init__(
        self,
        message: str = "Authentication failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 401, details)


class AuthorizationError(AppException):
    """Authorization related errors."""

    def __init__(
        self, message: str = "Access denied", details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 403, details)


class ValidationError(AppException):
    """Validation related errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 422, details)


class NotFoundError(AppException):
    """Resource not found errors."""

    def __init__(
        self,
        message: str = "Resource not found",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 404, details)


class ConflictError(AppException):
    """Resource conflict errors."""

    def __init__(
        self,
        message: str = "Resource conflict",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 409, details)


class ExternalServiceError(AppException):
    """External service errors."""

    def __init__(
        self,
        message: str = "External service error",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message, 502, details)


def create_http_exception(exc: AppException) -> HTTPException:
    """Convert AppException to HTTPException."""
    return HTTPException(
        status_code=exc.status_code,
        detail={"message": exc.message, "details": exc.details},
    )
