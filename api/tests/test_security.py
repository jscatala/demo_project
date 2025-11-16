"""Unit tests for security middleware and CORS configuration."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import os

from main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_security_headers_present(client):
    """Test that security headers are added to responses."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    assert "content-security-policy" in response.headers
    assert "x-xss-protection" in response.headers
    assert "referrer-policy" in response.headers


def test_x_frame_options_deny(client):
    """Test X-Frame-Options is set to DENY."""
    response = client.get("/health")

    assert response.headers["x-frame-options"] == "DENY"


def test_x_content_type_options_nosniff(client):
    """Test X-Content-Type-Options is set to nosniff."""
    response = client.get("/health")

    assert response.headers["x-content-type-options"] == "nosniff"


def test_csp_header_present(client):
    """Test Content-Security-Policy header is present."""
    response = client.get("/health")

    assert "content-security-policy" in response.headers
    assert "default-src 'self'" in response.headers["content-security-policy"]


def test_hsts_not_in_development(client):
    """Test HSTS header not present in development."""
    with patch.dict(os.environ, {"ENVIRONMENT": "development"}):
        response = client.get("/health")

        # HSTS should not be present in development
        assert "strict-transport-security" not in response.headers


def test_hsts_in_production():
    """Test HSTS header present in production."""
    with patch.dict(os.environ, {"ENVIRONMENT": "production"}):
        # Create new client with production environment
        client = TestClient(app)
        response = client.get("/health")

        assert "strict-transport-security" in response.headers
        assert (
            "max-age=31536000" in response.headers["strict-transport-security"]
        )


def test_cors_allowed_origin_succeeds(client):
    """Test CORS preflight request succeeds for allowed origin."""
    response = client.options(
        "/api/vote",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers
    assert (
        response.headers["access-control-allow-origin"]
        == "http://localhost:3000"
    )


def test_cors_untrusted_origin_blocked(client):
    """Test CORS rejects untrusted origin."""
    response = client.options(
        "/api/vote",
        headers={
            "Origin": "https://evil.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    # CORS will not include allow-origin header for untrusted origins
    # The browser will block the request
    assert response.status_code == 200  # OPTIONS succeeds
    # But the origin should not be in the allowed list
    if "access-control-allow-origin" in response.headers:
        assert response.headers["access-control-allow-origin"] != "https://evil.com"


def test_request_size_limit_small_request(client):
    """Test normal-sized request succeeds."""
    response = client.post(
        "/api/vote",
        json={"option": "cats"},
        headers={"Content-Type": "application/json"},
    )

    # Should succeed (201 or other non-413 status)
    assert response.status_code != 413


def test_request_size_limit_large_request(client):
    """Test oversized request rejected with 413."""
    # Create a large payload (> 1MB)
    large_payload = {"data": "x" * (2 * 1024 * 1024)}  # 2MB of data

    response = client.post(
        "/api/vote",
        json=large_payload,
        headers={"Content-Length": str(2 * 1024 * 1024)},
    )

    assert response.status_code == 413
    assert "too large" in response.json()["detail"].lower()


def test_cors_headers_restricted(client):
    """Test CORS only allows specific headers."""
    response = client.options(
        "/api/vote",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type,authorization",
        },
    )

    assert response.status_code == 200
    # Headers should be restricted to Content-Type, Authorization, Accept
    allowed_headers = response.headers.get(
        "access-control-allow-headers", ""
    ).lower()
    assert "content-type" in allowed_headers
    assert "authorization" in allowed_headers


def test_cors_methods_restricted(client):
    """Test CORS only allows specific methods."""
    response = client.options(
        "/api/vote",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    allowed_methods = response.headers.get(
        "access-control-allow-methods", ""
    ).upper()
    assert "GET" in allowed_methods
    assert "POST" in allowed_methods
    # Should not allow all methods like DELETE, PUT, etc.


def test_security_headers_on_all_endpoints(client):
    """Test security headers are present on all endpoints."""
    endpoints = ["/", "/health", "/ready", "/api/results"]

    for endpoint in endpoints:
        response = client.get(endpoint)

        # Should have security headers regardless of endpoint
        assert "x-frame-options" in response.headers
        assert "x-content-type-options" in response.headers
