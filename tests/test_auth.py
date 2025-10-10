"""
Comprehensive authentication API tests with mocked external dependencies.
"""

import os

# Disable Sentry before any imports
os.environ["SENTRY_DSN"] = ""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from core.dependencies import get_current_user
from main import app
from utils.supabase_client import (get_supabase_admin_client,
                                   get_supabase_client)

# Mock the audit decorator globally
with patch("utils.audit_decorator.audit_action") as mock_audit:
    mock_audit.side_effect = lambda action, resource: lambda func: func

# Mock Sentry SDK to prevent initialization and error reporting during tests
with patch("sentry_sdk.init") as mock_sentry_init, patch(
    "sentry_sdk.capture_exception"
) as mock_capture, patch("sentry_sdk.configure_scope") as mock_scope:
    mock_sentry_init.return_value = None
    mock_capture.return_value = None
    mock_scope.return_value.__enter__.return_value = None


# Create a mock middleware class to replace SentryMiddleware
class MockSentryMiddleware:
    """Mock SentryMiddleware."""

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)


# Mock the SentryMiddleware import
with patch(
    "middlewares.sentry_middleware.SentryMiddleware", MockSentryMiddleware
), patch("main.SentryMiddleware", MockSentryMiddleware):
    pass


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client with realistic response objects."""
    mock_client = Mock()

    # Mock auth methods
    mock_auth = Mock()
    mock_client.auth = mock_auth

    # Mock table methods
    mock_table = Mock()
    mock_client.table.return_value = mock_table

    return mock_client


@pytest.fixture
def mock_supabase_admin_client():
    """Mock Supabase admin client."""
    mock_client = Mock()
    mock_auth = Mock()
    mock_admin = Mock()
    mock_auth.admin = mock_admin
    mock_client.auth = mock_auth

    return mock_client


@pytest.fixture
def mock_current_user():
    """Mock authenticated user data."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "user_metadata": {"username": "testuser", "full_name": "Test User"},
        "app_metadata": {"role": "user"},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def mock_auth_response():
    """Mock Supabase auth response with session and user."""
    mock_user = Mock()
    mock_user.id = "test-user-id"
    mock_user.email = "test@example.com"
    mock_user.user_metadata = {"username": "testuser", "full_name": "Test User"}
    mock_user.created_at = datetime.now()
    mock_user.updated_at = datetime.now()

    mock_session = Mock()
    mock_session.access_token = "mock-access-token"
    mock_session.refresh_token = "mock-refresh-token"
    mock_session.expires_in = 3600

    mock_response = Mock()
    mock_response.user = mock_user
    mock_response.session = mock_session

    return mock_response


@pytest.fixture
def test_client(mock_supabase_client, mock_supabase_admin_client):
    """TestClient with mocked dependencies."""
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_client
    app.dependency_overrides[get_supabase_admin_client] = (
        lambda: mock_supabase_admin_client
    )

    with TestClient(app) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


class TestAuthRegister:
    """Test POST /auth/register endpoint."""

    def test_register_success(
        self, test_client, mock_supabase_client, mock_auth_response
    ):
        """Test successful user registration."""
        # Mock table query for existing user check
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = (
            None
        )

        # Mock successful sign up
        mock_supabase_client.auth.sign_up.return_value = mock_auth_response

        response = test_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User",
                "username": "testuser",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user"]["email"] == "test@example.com"
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["username"] == "testuser"

    def test_register_existing_user(self, test_client, mock_supabase_client):
        """Test registration with existing user."""
        # Mock existing user found
        existing_user_data = {
            "id": "existing-user-id",
            "email": "test@example.com",
            "raw_user_meta_data": {
                "full_name": "Existing User",
                "username": "existinguser",
            },
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": "2023-01-01T00:00:00Z",
        }

        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = (
            existing_user_data
        )

        response = test_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User",
                "username": "testuser",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "exists"
        assert data["message"] == "User is already registered"
        assert data["user"]["email"] == "test@example.com"

    def test_register_validation_error(self, test_client):
        """Test registration with validation errors."""
        response = test_client.post(
            "/auth/register",
            json={"email": "invalid-email", "password": "123"},  # Too short
        )

        assert response.status_code == 422

    def test_register_supabase_failure(self, test_client, mock_supabase_client):
        """Test registration when Supabase sign_up fails."""
        # Mock table query for existing user check
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.maybe_single.return_value.execute.return_value.data = (
            None
        )

        # Mock failed sign up
        mock_supabase_client.auth.sign_up.return_value.user = None

        response = test_client.post(
            "/auth/register",
            json={
                "email": "test@example.com",
                "password": "password123",
                "full_name": "Test User",
                "username": "testuser",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "Registration failed" in data["detail"]["message"]


class TestAuthLogin:
    """Test POST /auth/login endpoint."""

    def test_login_success(self, test_client, mock_supabase_client, mock_auth_response):
        """Test successful user login."""
        mock_supabase_client.auth.sign_in_with_password.return_value = (
            mock_auth_response
        )

        response = test_client.post(
            "/auth/login", json={"email": "test@example.com", "password": "password123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock-access-token"
        assert data["token_type"] == "bearer"
        assert data["refresh_token"] == "mock-refresh-token"
        assert data["user"]["email"] == "test@example.com"

    def test_login_invalid_credentials(self, test_client, mock_supabase_client):
        """Test login with invalid credentials."""
        # Mock failed authentication
        mock_response = Mock()
        mock_response.user = None
        mock_response.session = None
        mock_supabase_client.auth.sign_in_with_password.return_value = mock_response

        response = test_client.post(
            "/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "Invalid credentials" in data["detail"]["message"]

    def test_login_validation_error(self, test_client):
        """Test login with validation errors."""
        response = test_client.post(
            "/auth/login",
            json={"email": "invalid-email", "password": ""},  # Empty password
        )

        assert response.status_code == 422


class TestAuthLogout:
    """Test POST /auth/logout endpoint."""

    def test_logout_success(self, test_client, mock_supabase_client):
        """Test successful logout."""
        mock_supabase_client.auth.sign_out.return_value = None

        response = test_client.post("/auth/logout")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Successfully logged out"


class TestAuthRefresh:
    """Test POST /auth/refresh endpoint."""

    def test_refresh_success(
        self, test_client, mock_supabase_client, mock_auth_response
    ):
        """Test successful token refresh."""
        mock_supabase_client.auth.refresh_session.return_value = mock_auth_response

        response = test_client.post("/auth/refresh", params={"token": "refresh-token"})

        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "mock-access-token"
        assert data["token_type"] == "bearer"
        assert data["refresh_token"] == "mock-refresh-token"

    def test_refresh_invalid_token(self, test_client, mock_supabase_client):
        """Test refresh with invalid token."""
        # Mock failed refresh
        mock_response = Mock()
        mock_response.session = None
        mock_supabase_client.auth.refresh_session.return_value = mock_response

        response = test_client.post("/auth/refresh", params={"token": "invalid-token"})

        assert response.status_code == 401
        data = response.json()
        assert "Invalid refresh token" in data["detail"]["message"]


class TestAuthMe:
    """Test GET /auth/me endpoint."""

    def test_me_success(self, test_client, mock_current_user):
        """Test getting current user info with valid token."""
        app.dependency_overrides[get_current_user] = lambda: mock_current_user

        response = test_client.get("/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-user-id"
        assert data["email"] == "test@example.com"
        assert data["full_name"] == "Test User"
        assert data["username"] == "testuser"

    def test_me_unauthorized(self, test_client):
        """Test getting current user info without token."""
        response = test_client.get("/auth/me")

        assert response.status_code == 403


class TestAuthForgotPassword:
    """Test POST /auth/forgot-password endpoint."""

    @patch("api.auth.send_templated_email")
    def test_forgot_password_success(
        self, mock_send_email, test_client, mock_supabase_admin_client
    ):
        """Test successful password reset request."""
        # Mock admin client response
        mock_response = Mock()
        mock_response.properties.action_link = "https://example.com/reset?token=abc123"
        mock_supabase_admin_client.auth.admin.generate_link.return_value = mock_response

        # Mock email sending
        mock_send_email.return_value = {"id": "email-id"}

        response = test_client.post(
            "/auth/forgot-password", json={"email": "test@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password reset email sent"

        # Verify email was sent
        mock_send_email.assert_called_once()

    def test_forgot_password_validation_error(self, test_client):
        """Test forgot password with validation errors."""
        response = test_client.post(
            "/auth/forgot-password", json={"email": "invalid-email"}
        )

        assert response.status_code == 422

    def test_forgot_password_supabase_failure(
        self, test_client, mock_supabase_admin_client
    ):
        """Test forgot password when Supabase fails."""
        # Mock failed response - return None to simulate complete failure
        mock_supabase_admin_client.auth.admin.generate_link.return_value = None

        response = test_client.post(
            "/auth/forgot-password", json={"email": "test@example.com"}
        )

        assert response.status_code == 422
        data = response.json()
        assert "Failed to send password reset email" in data["detail"]["message"]


class TestAuthResetPassword:
    """Test POST /auth/reset-password endpoint."""

    def test_reset_password_success(
        self, test_client, mock_supabase_client, mock_auth_response
    ):
        """Test successful password reset."""
        # Mock session establishment
        mock_supabase_client.auth.set_session.return_value = mock_auth_response

        response = test_client.post(
            "/auth/reset-password",
            json={
                "token": "reset-token",
                "password": "newpassword123",
                "refresh_token": "refresh-token",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Password successfully reset"

    def test_reset_password_invalid_token(self, test_client, mock_supabase_client):
        """Test password reset with invalid token."""
        # Mock failed session establishment
        mock_response = Mock()
        mock_response.session = None
        mock_supabase_client.auth.set_session.return_value = mock_response

        response = test_client.post(
            "/auth/reset-password",
            json={
                "token": "invalid-token",
                "password": "newpassword123",
                "refresh_token": "refresh-token",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "Failed to establish session" in data["detail"]["message"]

    def test_reset_password_update_failure(
        self, test_client, mock_supabase_client, mock_auth_response
    ):
        """Test password reset when user update fails."""
        # Mock successful session establishment
        mock_supabase_client.auth.set_session.return_value = mock_auth_response

        # Mock failed user update
        mock_update_response = Mock()
        mock_update_response.user = None
        mock_supabase_client.auth.update_user.return_value = mock_update_response

        response = test_client.post(
            "/auth/reset-password",
            json={
                "token": "reset-token",
                "password": "newpassword123",
                "refresh_token": "refresh-token",
            },
        )

        assert response.status_code == 422
        data = response.json()
        assert "Password reset failed" in data["detail"]["message"]
