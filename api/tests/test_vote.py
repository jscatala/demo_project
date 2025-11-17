"""Unit tests for vote endpoint."""
import pytest
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from services.vote_service import RedisUnavailableError


# Mock Redis client for dependency injection
@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    return AsyncMock()


@pytest.fixture
def client():
    """Create test client with mocked Redis."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_submit_vote_cats_success(mock_redis):
    """Test successful vote submission for cats."""
    # Arrange
    mock_redis.xadd.return_value = "1234567890-0"

    with patch("routes.vote.get_redis", return_value=mock_redis):
        client = TestClient(app)

        # Act
        response = client.post("/api/vote", json={"option": "cats"})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Vote recorded successfully"
        assert data["option"] == "cats"
        assert "stream_id" in data


@pytest.mark.asyncio
async def test_submit_vote_dogs_success(mock_redis):
    """Test successful vote submission for dogs."""
    # Arrange
    mock_redis.xadd.return_value = "1234567890-1"

    with patch("routes.vote.get_redis", return_value=mock_redis):
        client = TestClient(app)

        # Act
        response = client.post("/api/vote", json={"option": "dogs"})

        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["message"] == "Vote recorded successfully"
        assert data["option"] == "dogs"
        assert "stream_id" in data


@pytest.mark.asyncio
async def test_submit_vote_invalid_option():
    """Test vote submission with invalid option returns 422."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # Act
        response = client.post("/api/vote", json={"option": "birds"})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_submit_vote_missing_option():
    """Test vote submission with missing option returns 422."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # Act
        response = client.post("/api/vote", json={})

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_submit_vote_redis_unavailable():
    """Test vote submission when Redis is unavailable returns 503."""
    # Arrange
    mock_redis = AsyncMock()

    with patch("routes.vote.get_redis", return_value=mock_redis), patch(
        "routes.vote.write_vote_to_stream", side_effect=RedisUnavailableError("Redis down")
    ):
        client = TestClient(app)

        # Act
        response = client.post("/api/vote", json={"option": "cats"})

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_submit_vote_extra_fields_rejected():
    """Test vote submission with extra fields is rejected."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # Act
        response = client.post(
            "/api/vote", json={"option": "cats", "extra_field": "should_fail"}
        )

        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# High-Priority Security/Edge Case Tests (Phase 4.2)
# ============================================================================


@pytest.mark.asyncio
async def test_submit_vote_sql_injection_attempt():
    """Test that SQL injection attempts are rejected by Pydantic validation."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # SQL injection payloads
        sql_injection_payloads = [
            "cats' OR '1'='1",
            "cats; DROP TABLE votes;--",
            "cats' UNION SELECT * FROM users--",
            "'; DELETE FROM votes WHERE '1'='1",
        ]

        for payload in sql_injection_payloads:
            # Act
            response = client.post("/api/vote", json={"option": payload})

            # Assert - Pydantic Literal validation rejects non-literal values
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Input should be 'cats' or 'dogs'" in response.text


@pytest.mark.asyncio
async def test_submit_vote_xss_attempt():
    """Test that XSS attempts are rejected by Pydantic validation."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # XSS payloads
        xss_payloads = [
            "<script>alert('xss')</script>",
            "cats<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert('XSS')",
        ]

        for payload in xss_payloads:
            # Act
            response = client.post("/api/vote", json={"option": payload})

            # Assert - Pydantic Literal validation rejects non-literal values
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
            assert "Input should be 'cats' or 'dogs'" in response.text


@pytest.mark.asyncio
async def test_submit_vote_oversized_payload():
    """Test that oversized payloads are rejected by middleware."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # Create payload larger than 1MB (default MAX_REQUEST_SIZE)
        # Use a large string in the option field
        oversized_payload = {"option": "a" * (2 * 1024 * 1024)}  # 2MB string

        # Act
        response = client.post("/api/vote", json=oversized_payload)

        # Assert - Middleware should reject with 413
        # Note: This test validates middleware behavior
        assert response.status_code in [
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            status.HTTP_422_UNPROCESSABLE_ENTITY,  # May fail Pydantic validation first
        ]


@pytest.mark.asyncio
async def test_submit_vote_malformed_json():
    """Test that malformed JSON is rejected with proper error."""
    with patch("routes.vote.get_redis", return_value=AsyncMock()):
        client = TestClient(app)

        # Malformed JSON payloads (invalid JSON syntax)
        malformed_payloads = [
            '{option: "cats"}',  # Missing quotes on key
            '{"option": "cats",}',  # Trailing comma
            '{"option" "cats"}',  # Missing colon
            'option=cats',  # Not JSON at all
        ]

        for payload in malformed_payloads:
            # Act - Send raw string instead of JSON dict
            response = client.post(
                "/api/vote",
                content=payload,
                headers={"Content-Type": "application/json"},
            )

            # Assert - FastAPI returns 422 for JSON decode errors
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
