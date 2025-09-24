"""
JWT middleware for FastAPI with local verification.
"""

import logging
from datetime import datetime, timezone
from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from core.config import settings
from core.exceptions import AuthenticationError, create_http_exception


logger = logging.getLogger(__name__)
security = HTTPBearer()


def get_jwt_token_from_header(request: Request) -> str:
    """
    Extract JWT token from Authorization header.

    Args:
        request: FastAPI request object

    Returns:
        str: JWT token

    Raises:
        HTTPException: If token is missing or invalid format
    """
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
        )

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
            )
        return token
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
        ) from e


def verify_jwt_token_locally(token: str) -> dict:
    """
    Verify JWT token locally using jose library.

    Args:
        token: JWT token to verify

    Returns:
        dict: User information from token payload

    Raises:
        HTTPException: If token is invalid
    """
    try:
        # Decode JWT token locally
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )

        # Check token expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(
            timezone.utc
        ):
            raise AuthenticationError("Token has expired")

        # Extract user information from payload
        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        return {
            "id": user_id,
            "email": payload.get("email"),
            "user_metadata": payload.get("user_metadata", {}),
            "app_metadata": payload.get("app_metadata", {}),
            "created_at": payload.get("iat"),
            "updated_at": payload.get("iat"),
            "role": payload.get("role", "user"),  # Extract role for authorization
            "exp": exp,
        }

    except JWTError as e:
        logger.error("JWT verification error: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid JWT token"
        ) from e
    except Exception as e:
        logger.error("Token verification error: %s", str(e))
        if isinstance(e, AuthenticationError):
            raise create_http_exception(e) from e
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token verification failed"
        ) from e


def verify_jwt_token(token: str) -> dict:
    """
    Verify JWT token (defaults to local verification).

    Args:
        token: JWT token to verify

    Returns:
        dict: User information

    Raises:
        HTTPException: If token is invalid
    """
    return verify_jwt_token_locally(token)


class JWTMiddleware:
    """
    JWT middleware for protecting routes.
    """

    def __init__(self, app, exclude_paths: list = None):
        self.app = app
        self.exclude_paths = exclude_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/auth/login",
            "/auth/register",
            "/auth/forgot-password",
            "/auth/reset-password",
            "/health",
        ]

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path

        # Skip JWT verification for excluded paths
        if any(path.startswith(excluded) for excluded in self.exclude_paths):
            await self.app(scope, receive, send)
            return

        # Extract and verify token
        try:
            token = get_jwt_token_from_header(request)
            user = verify_jwt_token(token)

            # Add user info to request state
            scope["user"] = user

        except HTTPException as e:
            # Return error response

            response = JSONResponse(
                status_code=e.status_code, content={"detail": e.detail}
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
