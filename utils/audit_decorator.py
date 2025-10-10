"""
Audit action decorator for FastAPI routes.
"""

import asyncio
import inspect
import logging
from functools import wraps
from typing import Any, Callable, Dict, Optional

from fastapi import Request, Response

from utils.audit_logger import create_audit_metadata, log_audit_action

logger = logging.getLogger(__name__)


def audit_action(action: str, resource: str):
    """
    Decorator to automatically log audit actions for FastAPI routes.

    This decorator wraps route handlers and automatically logs audit entries
    after the handler completes successfully. It extracts user information,
    request details, and response metadata.

    Args:
        action: The action being performed (e.g., "LOGIN", "LOGOUT", "CREATE", "DELETE")
        resource: The resource type being affected (e.g., "user", "auth", "profile")

    Usage:
        @router.post("/login")
        @audit_action("LOGIN", "auth")
        async def login(user: UserLogin, request: Request):
            # Route implementation
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract information from the request and dependencies
            request = None
            current_user = None

            # Find Request object in kwargs
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

            # Find user information in kwargs (could be current_user, user, etc.)
            user_keys = ["current_user", "user", "authenticated_user"]
            for key in user_keys:
                if key in kwargs and kwargs[key] is not None:
                    current_user = kwargs[key]
                    break

            # Extract user_id
            user_id = None
            if current_user and isinstance(current_user, dict):
                user_id = current_user.get("id")

            # Extract IP address and user agent
            ip_address = None
            user_agent = None
            if request:
                ip_address = get_client_ip(request)
                user_agent = request.headers.get("user-agent")

            # Extract resource_id from path parameters
            resource_id = extract_resource_id(kwargs)

            # Extract request body for POST/PUT operations
            request_body = None
            if request and request.method in ["POST", "PUT", "PATCH"]:
                request_body = await extract_request_body(request)

            # Execute the original function
            try:
                result = await func(*args, **kwargs)

                # Extract response status code
                status_code = None
                if isinstance(result, Response):
                    status_code = result.status_code
                elif hasattr(result, "status_code"):
                    status_code = result.status_code
                else:
                    # Default to 200 for successful execution
                    status_code = 200

                # Create metadata
                metadata = create_audit_metadata(
                    request_body=request_body,
                    status_code=status_code,
                )

                # Log the audit action asynchronously (non-blocking)
                asyncio.create_task(
                    log_audit_action(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata=metadata,
                    )
                )

                return result

            except Exception as e:
                # Log failed audit action
                metadata = create_audit_metadata(
                    request_body=request_body,
                    status_code=500,  # Internal server error
                    additional_data={"error": str(e)},
                )

                # Log the audit action asynchronously (non-blocking)
                asyncio.create_task(
                    log_audit_action(
                        user_id=user_id,
                        action=f"{action}_FAILED",
                        resource=resource,
                        resource_id=resource_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata=metadata,
                    )
                )

                # Re-raise the original exception
                raise

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # Handle synchronous functions
            request = None
            current_user = None

            # Find Request object in kwargs
            for key, value in kwargs.items():
                if isinstance(value, Request):
                    request = value
                    break

            # Find user information in kwargs
            user_keys = ["current_user", "user", "authenticated_user"]
            for key in user_keys:
                if key in kwargs and kwargs[key] is not None:
                    current_user = kwargs[key]
                    break

            # Extract user_id
            user_id = None
            if current_user and isinstance(current_user, dict):
                user_id = current_user.get("id")

            # Extract IP address and user agent
            ip_address = None
            user_agent = None
            if request:
                ip_address = get_client_ip(request)
                user_agent = request.headers.get("user-agent")

            # Extract resource_id from path parameters
            resource_id = extract_resource_id(kwargs)

            # Execute the original function
            try:
                result = func(*args, **kwargs)

                # Extract response status code
                status_code = None
                if isinstance(result, Response):
                    status_code = result.status_code
                elif hasattr(result, "status_code"):
                    status_code = result.status_code
                else:
                    status_code = 200

                # Create metadata
                metadata = create_audit_metadata(
                    status_code=status_code,
                )

                # Log the audit action asynchronously (non-blocking)
                asyncio.create_task(
                    log_audit_action(
                        user_id=user_id,
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata=metadata,
                    )
                )

                return result

            except Exception as e:
                # Log failed audit action
                metadata = create_audit_metadata(
                    status_code=500,
                    additional_data={"error": str(e)},
                )

                # Log the audit action asynchronously (non-blocking)
                asyncio.create_task(
                    log_audit_action(
                        user_id=user_id,
                        action=f"{action}_FAILED",
                        resource=resource,
                        resource_id=resource_id,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        metadata=metadata,
                    )
                )

                # Re-raise the original exception
                raise

        # Determine if the function is async
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def get_client_ip(request: Request) -> Optional[str]:
    """
    Extract the client IP address from the request.

    Args:
        request: FastAPI Request object

    Returns:
        Client IP address or None if not available
    """
    # Check for forwarded headers first (for reverse proxies)
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip

    # Fall back to direct client IP
    if request.client:
        return request.client.host

    return None


def extract_resource_id(kwargs: Dict[str, Any]) -> Optional[str]:
    """
    Extract resource ID from path parameters.

    Args:
        kwargs: Function keyword arguments

    Returns:
        Resource ID or None if not found
    """
    # Common resource ID parameter names
    resource_id_keys = [
        "id",
        "resource_id",
        "user_id",
        "profile_id",
        "item_id",
        "object_id",
    ]

    for key in resource_id_keys:
        if key in kwargs and kwargs[key] is not None:
            return str(kwargs[key])

    return None


async def extract_request_body(request: Request) -> Optional[Dict[str, Any]]:
    """
    Extract and parse request body.

    Args:
        request: FastAPI Request object

    Returns:
        Parsed request body or None if not available
    """
    try:
        # Get request body
        body = await request.body()

        if not body:
            return None

        # Try to parse as JSON
        import json

        try:
            return json.loads(body.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            # If not JSON, return as string
            return {"raw_body": body.decode("utf-8", errors="ignore")}

    except (ValueError, ConnectionError) as e:
        logger.warning("Failed to extract request body: %s", str(e))
        return None
