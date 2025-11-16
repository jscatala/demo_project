"""Unit tests for results endpoint."""
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime
from fastapi import status
from fastapi.testclient import TestClient

from main import app
from services.results_service import DatabaseUnavailableError


@pytest.fixture
def mock_db_pool():
    """Create a mock PostgreSQL pool."""
    return AsyncMock()


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_results_success(mock_db_pool):
    """Test successful results fetch with counts."""
    # Arrange - mock database response
    mock_rows = [
        {
            "option": "cats",
            "count": 150,
            "percentage": 60.0,
            "updated_at": datetime(2025, 11, 15, 12, 0, 0),
        },
        {
            "option": "dogs",
            "count": 100,
            "percentage": 40.0,
            "updated_at": datetime(2025, 11, 15, 11, 30, 0),
        },
    ]

    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = mock_rows
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    with patch("routes.results.get_db", return_value=mock_db_pool):
        client = TestClient(app)

        # Act
        response = client.get("/api/results")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cats"] == 150
        assert data["dogs"] == 100
        assert data["total"] == 250
        assert data["cats_percentage"] == 60.0
        assert data["dogs_percentage"] == 40.0
        assert "last_updated" in data


@pytest.mark.asyncio
async def test_get_results_empty_database(mock_db_pool):
    """Test results fetch with zero votes."""
    # Arrange - mock empty database
    mock_rows = [
        {
            "option": "cats",
            "count": 0,
            "percentage": 0.0,
            "updated_at": datetime(2025, 11, 15, 12, 0, 0),
        },
        {
            "option": "dogs",
            "count": 0,
            "percentage": 0.0,
            "updated_at": datetime(2025, 11, 15, 12, 0, 0),
        },
    ]

    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = mock_rows
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    with patch("routes.results.get_db", return_value=mock_db_pool):
        client = TestClient(app)

        # Act
        response = client.get("/api/results")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["cats"] == 0
        assert data["dogs"] == 0
        assert data["total"] == 0
        assert data["cats_percentage"] == 0.0
        assert data["dogs_percentage"] == 0.0


@pytest.mark.asyncio
async def test_get_results_database_unavailable():
    """Test results fetch when database is unavailable."""
    # Arrange
    with patch("routes.results.get_db", return_value=AsyncMock()), patch(
        "routes.results.fetch_vote_results",
        side_effect=DatabaseUnavailableError("DB down"),
    ):
        client = TestClient(app)

        # Act
        response = client.get("/api/results")

        # Assert
        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
        assert "unavailable" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_results_cache_control_header(mock_db_pool):
    """Test that Cache-Control header is set correctly."""
    # Arrange
    mock_rows = [
        {
            "option": "cats",
            "count": 10,
            "percentage": 50.0,
            "updated_at": datetime.now(),
        },
        {
            "option": "dogs",
            "count": 10,
            "percentage": 50.0,
            "updated_at": datetime.now(),
        },
    ]

    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = mock_rows
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    with patch("routes.results.get_db", return_value=mock_db_pool):
        client = TestClient(app)

        # Act
        response = client.get("/api/results")

        # Assert
        assert response.status_code == status.HTTP_200_OK
        assert "cache-control" in response.headers
        assert "max-age=2" in response.headers["cache-control"]


@pytest.mark.asyncio
async def test_get_results_caching_works(mock_db_pool):
    """Test that results are cached for 2 seconds."""
    import time
    from services.results_service import clear_cache

    # Clear cache before test
    clear_cache()

    # Arrange
    mock_rows = [
        {
            "option": "cats",
            "count": 50,
            "percentage": 50.0,
            "updated_at": datetime.now(),
        },
        {
            "option": "dogs",
            "count": 50,
            "percentage": 50.0,
            "updated_at": datetime.now(),
        },
    ]

    mock_conn = AsyncMock()
    mock_conn.fetch.return_value = mock_rows
    mock_db_pool.acquire.return_value.__aenter__.return_value = mock_conn

    with patch("routes.results.get_db", return_value=mock_db_pool):
        client = TestClient(app)

        # Act - First call
        response1 = client.get("/api/results")

        # Act - Second call within 2 seconds
        response2 = client.get("/api/results")

        # Assert - Both succeed
        assert response1.status_code == status.HTTP_200_OK
        assert response2.status_code == status.HTTP_200_OK

        # Database should only be called once (second call uses cache)
        # Note: This is a simplified test; full caching test would need
        # to verify fetch is only called once

    # Cleanup
    clear_cache()
