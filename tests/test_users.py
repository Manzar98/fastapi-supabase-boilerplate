"""
Comprehensive user profile API tests with mocked external dependencies.
"""

import os

# Disable Sentry before any imports
os.environ["SENTRY_DSN"] = ""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime

from main import app
from utils.supabase_client import get_supabase_client
from core.dependencies import get_current_user

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

    return mock_client


@pytest.fixture
def mock_current_user():
    """Mock authenticated user data."""
    return {
        "id": "test-user-id",
        "email": "test@example.com",
        "user_metadata": {
            "username": "testuser",
            "full_name": "Test User",
            "avatar_url": "https://example.com/avatar.jpg",
        },
        "app_metadata": {"role": "user"},
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
    }


@pytest.fixture
def mock_user_response():
    """Mock Supabase user response."""
    mock_user = Mock()
    mock_user.user_metadata = {
        "username": "testuser",
        "full_name": "Test User",
        "avatar_url": "https://example.com/avatar.jpg",
    }

    mock_response = Mock()
    mock_response.user = mock_user

    return mock_response


@pytest.fixture
def test_client(mock_supabase_client):
    """TestClient with mocked dependencies."""
    app.dependency_overrides[get_supabase_client] = lambda: mock_supabase_client

    with TestClient(app) as client:
        yield client

    # Clean up
    app.dependency_overrides.clear()


class TestUserProfile:
    """Test GET /user/profile endpoint."""

    def test_get_profile_success(
        self, test_client, mock_supabase_client, mock_user_response
    ):
        """Test successful profile retrieval."""
        # Mock get_user response
        mock_supabase_client.auth.get_user.return_value = mock_user_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.get("/user/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"
        assert data["full_name"] == "Test User"
        assert data["avatar_url"] == "https://example.com/avatar.jpg"

    def test_get_profile_user_not_found(self, test_client, mock_supabase_client):
        """Test profile retrieval when user is not found."""
        # Mock get_user response with no user
        mock_response = Mock()
        mock_response.user = None
        mock_supabase_client.auth.get_user.return_value = mock_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.get("/user/profile")

        assert response.status_code == 404
        data = response.json()
        assert "User profile not found" in data["detail"]["message"]

    def test_get_profile_unauthorized(self, test_client):
        """Test profile retrieval without authentication."""
        response = test_client.get("/user/profile")

        assert response.status_code == 403


class TestUserProfileUpdate:
    """Test PUT /user/profile endpoint."""

    def test_update_profile_success(
        self, test_client, mock_supabase_client, mock_user_response
    ):
        """Test successful profile update."""
        # Mock update_user response
        mock_supabase_client.auth.update_user.return_value = mock_user_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.put(
            "/user/profile",
            json={
                "username": "newusername",
                "full_name": "New Full Name",
                "avatar_url": "https://example.com/new-avatar.jpg",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user"]["username"] == "testuser"
        assert data["user"]["full_name"] == "Test User"
        assert data["user"]["avatar_url"] == "https://example.com/avatar.jpg"

    def test_update_profile_partial_update(
        self, test_client, mock_supabase_client, mock_user_response
    ):
        """Test partial profile update."""
        # Mock update_user response
        mock_supabase_client.auth.update_user.return_value = mock_user_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.put("/user/profile", json={"username": "newusername"})

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["user"]["username"] == "testuser"

    def test_update_profile_no_data(self, test_client):
        """Test profile update with no data provided."""
        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.put("/user/profile", json={})

        assert response.status_code == 422
        data = response.json()
        assert "No profile data provided for update" in data["detail"]["message"]

    def test_update_profile_validation_error(
        self, test_client, mock_supabase_client, mock_user_response
    ):
        """Test profile update with validation errors."""
        # Mock update_user response
        mock_supabase_client.auth.update_user.return_value = mock_user_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        # Test with malformed JSON
        response = test_client.put(
            "/user/profile",
            data="invalid json",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 422

    def test_update_profile_supabase_failure(self, test_client, mock_supabase_client):
        """Test profile update when Supabase fails."""
        # Mock failed update_user response
        mock_response = Mock()
        mock_response.user = None
        mock_supabase_client.auth.update_user.return_value = mock_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.put("/user/profile", json={"username": "newusername"})

        assert response.status_code == 502
        data = response.json()
        assert "Failed to update profile" in data["detail"]["message"]

    def test_update_profile_unauthorized(self, test_client):
        """Test profile update without authentication."""
        response = test_client.put("/user/profile", json={"username": "newusername"})

        assert response.status_code == 403


class TestUserDelete:
    """Test DELETE /user/ endpoint."""

    def test_delete_user_success(self, test_client, mock_supabase_client):
        """Test successful user deletion."""
        # Mock successful delete_user response
        mock_user = Mock()
        mock_user.id = "test-user-id"
        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase_client.auth.delete_user.return_value = mock_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.delete("/user/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["message"] == "User deleted successfully"

    def test_delete_user_supabase_failure(self, test_client, mock_supabase_client):
        """Test user deletion when Supabase fails."""
        # Mock failed delete_user response
        mock_response = Mock()
        mock_response.user = None
        mock_supabase_client.auth.delete_user.return_value = mock_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.delete("/user/")

        assert response.status_code == 502
        data = response.json()
        assert "Failed to delete user" in data["detail"]["message"]

    def test_delete_user_unauthorized(self, test_client):
        """Test user deletion without authentication."""
        response = test_client.delete("/user/")

        assert response.status_code == 403


class TestUserProfileEdgeCases:
    """Test edge cases for user profile endpoints."""

    def test_get_profile_empty_metadata(self, test_client, mock_supabase_client):
        """Test profile retrieval with empty user metadata."""
        # Mock get_user response with empty metadata
        mock_user = Mock()
        mock_user.user_metadata = None
        mock_response = Mock()
        mock_response.user = mock_user
        mock_supabase_client.auth.get_user.return_value = mock_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.get("/user/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["username"] is None
        assert data["full_name"] is None
        assert data["avatar_url"] is None

    def test_update_profile_with_none_values(
        self, test_client, mock_supabase_client, mock_user_response
    ):
        """Test profile update with None values."""
        # Mock update_user response
        mock_supabase_client.auth.update_user.return_value = mock_user_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.put(
            "/user/profile",
            json={"username": None, "full_name": None, "avatar_url": None},
        )

        assert response.status_code == 422
        data = response.json()
        assert "No profile data provided for update" in data["detail"]["message"]

    def test_update_profile_with_empty_strings(
        self, test_client, mock_supabase_client, mock_user_response
    ):
        """Test profile update with empty strings."""
        # Mock update_user response
        mock_supabase_client.auth.update_user.return_value = mock_user_response

        # Mock current user dependency
        app.dependency_overrides[get_current_user] = lambda: {
            "id": "test-user-id",
            "email": "test@example.com",
            "user_metadata": {},
            "app_metadata": {},
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
        }

        response = test_client.put(
            "/user/profile", json={"username": "", "full_name": "", "avatar_url": ""}
        )

        assert response.status_code == 422
        data = response.json()
        assert "No profile data provided for update" in data["detail"]["message"]
