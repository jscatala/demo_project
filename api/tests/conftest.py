"""Pytest configuration and fixtures for API tests.

This module provides global fixtures and patches to enable testing
without actual Redis/PostgreSQL connections.
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock


# Global patches for lifespan and dependency injection
# These prevent actual Redis/DB connections during test runs
@pytest.fixture(scope="session", autouse=True)
def mock_redis_lifecycle():
    """Mock Redis init/close functions and global client for all tests."""
    mock_client = AsyncMock()

    with patch("redis_client.init_redis", new_callable=AsyncMock), \
         patch("redis_client.close_redis", new_callable=AsyncMock), \
         patch("redis_client._redis_client", mock_client):
        yield mock_client


@pytest.fixture(scope="session", autouse=True)
def mock_db_lifecycle():
    """Mock PostgreSQL init/close functions and global pool for all tests."""
    mock_pool = AsyncMock()

    with patch("db_client.init_db", new_callable=AsyncMock), \
         patch("db_client.close_db", new_callable=AsyncMock), \
         patch("db_client._db_pool", mock_pool):
        yield mock_pool


@pytest.fixture(scope="function")
def mock_redis_client():
    """Mock Redis client for dependency injection (function-scoped)."""
    return AsyncMock()


@pytest.fixture(scope="function")
def mock_db_pool():
    """Mock PostgreSQL connection pool (function-scoped)."""
    return AsyncMock()
