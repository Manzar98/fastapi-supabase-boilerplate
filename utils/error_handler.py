"""
Error handling utilities for API endpoints.
"""

import logging
from typing import Any, Dict, Optional, Union
from fastapi import HTTPException, status
from core.exceptions import (
    AuthenticationError,
    ValidationError,
    NotFoundError,
    ConflictError,
    ExternalServiceError,
    AppException,
)

logger = logging.getLogger(__name__)


class ErrorResponse:
    """Standard error response structure."""
    
    def __init__(self, status_code: str = "error", error: str = "", data: Optional[Any] = None):
        self.status = status_code
        self.error = error
        self.data = data
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {"status": self.status}
        if self.error:
            result["error"] = self.error
        if self.data is not None:
            result["data"] = self.data
        return result


class SuccessResponse:
    """Standard success response structure."""
    
    def __init__(self, data: Any = None, message: str = "success"):
        self.status = "success"
        self.data = data
        self.message = message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = {"status": self.status}
        if self.data is not None:
            result["data"] = self.data
        if self.message != "success":
            result["message"] = self.message
        return result


def handle_api_error(
    error: Exception,
    user_id: Optional[str] = None,
    operation: str = "operation",
    return_error_response: bool = True,
) -> Union[ErrorResponse, HTTPException]:
    """
    Handle API errors with consistent logging and response formatting.
    
    Args:
        error: The exception that occurred
        user_id: ID of the user making the request (for logging)
        operation: Description of the operation being performed
        return_error_response: If True, return ErrorResponse; if False, raise HTTPException
    
    Returns:
        ErrorResponse if return_error_response is True, otherwise raises HTTPException
    """
    error_msg = str(error)
    user_info = user_id or "unknown"
    
    # Log the error
    logger.error(
        "%s error for user %s: %s",
        operation,
        user_info,
        error_msg,
    )
    
    # Handle custom application exceptions
    if isinstance(error, AppException):
        if return_error_response:
            return ErrorResponse(error=error_msg)
        else:
            return HTTPException(
                status_code=error.status_code,
                detail={"message": error.message, "details": error.details},
            )
    
    # Handle Supabase specific errors
    if hasattr(error, "message"):
        error_message = str(error.message)
        
        # Authentication errors
        if any(phrase in error_message for phrase in ["Invalid JWT", "JWT expired", "Unauthorized"]):
            auth_error = AuthenticationError("Session expired. Please login again.")
            if return_error_response:
                return ErrorResponse(error=str(auth_error))
            else:
                return HTTPException(
                    status_code=auth_error.status_code,
                    detail={"message": auth_error.message, "details": auth_error.details},
                )
        
        # User not found errors
        elif "User not found" in error_message:
            not_found_error = NotFoundError("User not found")
            if return_error_response:
                return ErrorResponse(error=str(not_found_error))
            else:
                return HTTPException(
                    status_code=not_found_error.status_code,
                    detail={"message": not_found_error.message, "details": not_found_error.details},
                )
        
        # Conflict errors (duplicate data)
        elif any(phrase in error_message.lower() for phrase in ["already exists", "duplicate", "conflict"]):
            conflict_error = ConflictError("Resource already exists")
            if return_error_response:
                return ErrorResponse(error=str(conflict_error))
            else:
                return HTTPException(
                    status_code=conflict_error.status_code,
                    detail={"message": conflict_error.message, "details": conflict_error.details},
                )
        
        # Validation errors
        elif "validation" in error_message.lower():
            validation_error = ValidationError(f"Invalid data: {error_message}")
            if return_error_response:
                return ErrorResponse(error=str(validation_error))
            else:
                return HTTPException(
                    status_code=validation_error.status_code,
                    detail={"message": validation_error.message, "details": validation_error.details},
                )
        
        # Other external service errors
        else:
            external_error = ExternalServiceError(f"Service error: {error_message}")
            if return_error_response:
                return ErrorResponse(error=str(external_error))
            else:
                return HTTPException(
                    status_code=external_error.status_code,
                    detail={"message": external_error.message, "details": external_error.details},
                )
    
    # Generic error handling
    if return_error_response:
        return ErrorResponse(error=error_msg)
    else:
        return HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def handle_supabase_response(
    response: Any,
    operation: str = "database operation",
    user_id: Optional[str] = None,
    return_error_response: bool = True,
) -> Union[ErrorResponse, None]:
    """
    Handle Supabase response and return error if needed.
    
    Args:
        response: Supabase response object
        operation: Description of the operation
        user_id: ID of the user making the request
        return_error_response: If True, return ErrorResponse; if False, raise HTTPException
    
    Returns:
        ErrorResponse if there's an error, None if successful
    """
    if hasattr(response, 'status_code') and response.status_code not in [200, 201]:
        error_msg = f"Failed to {operation}. Status: {response.status_code}"
        if hasattr(response, 'data') and response.data:
            error_msg += f", Details: {response.data}"
        
        logger.error(
            "%s error for user %s: %s",
            operation,
            user_id or "unknown",
            error_msg,
        )
        
        if return_error_response:
            return ErrorResponse(error=error_msg)
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=error_msg,
            )
    
    return None


def create_success_response(data: Any = None, message: str = "success") -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: The data to return
        message: Success message
    
    Returns:
        Dictionary with success response structure
    """
    return SuccessResponse(data=data, message=message).to_dict()


def create_error_response(error: str) -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error: Error message
    
    Returns:
        Dictionary with error response structure
    """
    return ErrorResponse(error=error).to_dict()
