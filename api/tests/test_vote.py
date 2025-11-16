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
