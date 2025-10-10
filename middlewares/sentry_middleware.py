"""
Sentry middleware for FastAPI error monitoring and request context capture.
"""

import logging
import time
import uuid
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration
from core.config import settings

logger = logging.getLogger(__name__)


class SentryMiddleware(BaseHTTPMiddleware):
    """
    Professional Sentry middleware that:
    - Captures unhandled exceptions and sends them to Sentry
    - Returns proper JSON error responses to clients
    - Logs useful request context (URL, method, user info if available)
    - Maintains clean error handling structure
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self._initialize_sentry()

    def _initialize_sentry(self):
        """Initialize Sentry SDK with proper configuration."""
        if not settings.sentry_dsn:
            logger.warning("SENTRY_DSN not configured. Sentry monitoring disabled.")
            return

        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            release=f"{settings.app_name}@{settings.app_version}",
            send_default_pii=True,  # Include user data
            traces_sample_rate=0.1 if settings.environment == "production" else 1.0,
            profiles_sample_rate=0.1 if settings.environment == "production" else 1.0,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
            before_send=self._before_send,
        )

    def _before_send(self, event: Dict[str, Any], hint: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Filter and enhance events before sending to Sentry.
        """
        # Skip certain exceptions in development
        if settings.environment == "development":
            # Skip common development exceptions
            if "exc_info" in hint:
                exc_type, exc_value, exc_tb = hint["exc_info"]
                if exc_type.__name__ in ["KeyboardInterrupt", "SystemExit"]:
                    return None
                # Suppress unused variable warnings
                _ = exc_value
                _ = exc_tb

        # Add custom tags
        event.setdefault("tags", {}).update({
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "environment": settings.environment,
        })

        return event

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and capture context for Sentry.
        """
        # Generate unique request ID for tracing
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Set up Sentry context for this request
        with sentry_sdk.configure_scope() as scope:
            # Add request context
            scope.set_context("request", {
                "url": str(request.url),
                "method": request.method,
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
                "path_params": getattr(request, "path_params", {}),
                "request_id": request_id,
            })

            # Add user context if available
            user_info = await self._extract_user_context(request)
            if user_info:
                scope.set_user(user_info)

            # Add tags
            scope.set_tag("request_id", request_id)
            scope.set_tag("method", request.method)
            scope.set_tag("path", request.url.path)

            try:
                # Process the request
                response = await call_next(request)
                
                # Calculate processing time
                process_time = time.time() - start_time
                
                # Add performance context
                scope.set_context("performance", {
                    "process_time": process_time,
                    "status_code": response.status_code,
                })

                # Add response headers for debugging
                response.headers["X-Request-ID"] = request_id
                response.headers["X-Process-Time"] = str(round(process_time, 4))

                return response

            except Exception as exc:
                # Capture the exception with full context
                sentry_sdk.capture_exception(exc)
                
                # Log the error locally
                logger.error(
                    "Unhandled exception in request %s %s: %s",
                    request.method,
                    request.url.path,
                    str(exc),
                    exc_info=True,
                    extra={
                        "request_id": request_id,
                        "method": request.method,
                        "path": request.url.path,
                        "user_agent": request.headers.get("user-agent"),
                        "client_ip": self._get_client_ip(request),
                    }
                )

                # Return a proper JSON error response
                return JSONResponse(
                    status_code=500,
                    content={
                        "message": "Internal server error",
                        "details": "An unexpected error occurred",
                        "request_id": request_id,
                    },
                    headers={"X-Request-ID": request_id}
                )

    async def _extract_user_context(self, request: Request) -> Optional[Dict[str, Any]]:
        """
        Extract user context from request for Sentry.
        This can be customized based on your authentication system.
        """
        try:
            # Try to get user info from request state (if set by auth middleware)
            if hasattr(request.state, "user") and request.state.user:
                user = request.state.user
                return {
                    "id": getattr(user, "id", None),
                    "email": getattr(user, "email", None),
                    "username": getattr(user, "username", None),
                }

            # Try to get user info from Authorization header
            auth_header = request.headers.get("authorization")
            if auth_header and auth_header.startswith("Bearer "):
                # You could decode the JWT token here to extract user info
                # For now, we'll just indicate that a token is present
                return {"authenticated": True}

        except (AttributeError, KeyError, ValueError) as e:
            logger.debug("Failed to extract user context: %s", str(e))

        return None

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.
        """
        # Check for forwarded headers first
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fall back to direct connection
        if hasattr(request, "client") and request.client:
            return request.client.host

        return "unknown"


class SentryErrorHandler:
    """
    Centralized error handler that integrates with Sentry.
    """

    @staticmethod
    def capture_exception(exc: Exception, request: Optional[Request] = None, **context) -> None:
        """
        Capture an exception with additional context.
        """
        with sentry_sdk.configure_scope() as scope:
            # Add any additional context
            if context:
                scope.set_context("additional", context)

            # Add request context if available
            if request:
                scope.set_context("request", {
                    "url": str(request.url),
                    "method": request.method,
                    "headers": dict(request.headers),
                })

        sentry_sdk.capture_exception(exc)

    @staticmethod
    def capture_message(message: str, level: str = "info", **context) -> None:
        """
        Capture a message with additional context.
        """
        with sentry_sdk.configure_scope() as scope:
            if context:
                scope.set_context("additional", context)

        sentry_sdk.capture_message(message, level=level)

    @staticmethod
    def add_breadcrumb(message: str, category: str = "custom", level: str = "info", **data) -> None:
        """
        Add a breadcrumb for debugging.
        """
        sentry_sdk.add_breadcrumb(
            message=message,
            category=category,
            level=level,
            data=data
        )
