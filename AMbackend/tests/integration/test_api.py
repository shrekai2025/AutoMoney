"""Integration tests for API endpoints"""

import pytest
from fastapi.testclient import TestClient


def test_health_check(test_client: TestClient):
    """Test health check endpoint"""
    response = test_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "app" in data
    assert "version" in data
    assert "environment" in data


def test_root_endpoint(test_client: TestClient):
    """Test root endpoint"""
    response = test_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "docs" in data


def test_firebase_config(test_client: TestClient):
    """Test Firebase configuration endpoint"""
    response = test_client.get("/api/v1/auth/config")

    assert response.status_code == 200
    data = response.json()
    assert "apiKey" in data
    assert "authDomain" in data
    assert "projectId" in data
    assert data["projectId"] == "lingocontext"


def test_get_me_without_auth(test_client: TestClient):
    """Test /me endpoint without authentication"""
    response = test_client.get("/api/v1/auth/me")

    # Should return 403 (Forbidden) or 401 (Unauthorized)
    assert response.status_code in [401, 403]


def test_logout(test_client: TestClient):
    """Test logout endpoint"""
    response = test_client.post("/api/v1/auth/logout")

    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_api_docs_accessible(test_client: TestClient):
    """Test that API documentation is accessible"""
    response = test_client.get("/docs")

    assert response.status_code == 200


def test_openapi_schema(test_client: TestClient):
    """Test OpenAPI schema endpoint"""
    response = test_client.get("/api/v1/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data
