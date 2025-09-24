"""
Authentication API tests.
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app_name" in data
    assert "version" in data


def test_root_endpoint():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data


def test_login_missing_credentials():
    """Test login with missing credentials."""
    response = client.post("/auth/login", json={})
    assert response.status_code == 422  # Validation error


def test_register_missing_credentials():
    """Test register with missing credentials."""
    response = client.post("/auth/register", json={})
    assert response.status_code == 422  # Validation error


def test_protected_route_without_token():
    """Test accessing protected route without token."""
    response = client.get("/auth/me")
    assert response.status_code == 401  # Unauthorized


def test_logout():
    """Test logout endpoint."""
    response = client.post("/auth/logout")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Successfully logged out"
