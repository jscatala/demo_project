"""PostgreSQL client singleton for connection pooling."""
import os
from typing import Optional
import asyncpg
import logging

logger = logging.getLogger(__name__)

# Global database pool instance
_db_pool: Optional[asyncpg.Pool] = None


async def init_db() -> None:
    """Initialize PostgreSQL connection pool.

    Creates a singleton connection pool with asyncpg.
    Uses DATABASE_URL environment variable for configuration.

    Raises:
        ConnectionError: If unable to connect to PostgreSQL
    """
    global _db_pool

    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/votes",
    )
    logger.info(f"Initializing PostgreSQL connection to {database_url}")

    try:
        _db_pool = await asyncpg.create_pool(
            database_url, min_size=2, max_size=10, command_timeout=60
        )

        # Test connection
        async with _db_pool.acquire() as conn:
            await conn.fetchval("SELECT 1")

        logger.info("PostgreSQL connection pool established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        raise ConnectionError(f"PostgreSQL connection failed: {e}")


async def close_db() -> None:
    """Close PostgreSQL connection pool.

    Cleanup function to be called on application shutdown.
    """
    global _db_pool

    if _db_pool:
        await _db_pool.close()
        logger.info("PostgreSQL connection pool closed")
        _db_pool = None


async def get_db() -> asyncpg.Pool:
    """Get PostgreSQL pool instance for dependency injection.

    Returns:
        asyncpg Pool instance

    Raises:
        RuntimeError: If database pool not initialized
    """
    if _db_pool is None:
        raise RuntimeError("Database pool not initialized")
    return _db_pool


async def check_db_health() -> bool:
    """Check PostgreSQL connection health.

    Returns:
        True if PostgreSQL is reachable, False otherwise
    """
    try:
        pool = await get_db()
        async with pool.acquire() as conn:
            await conn.fetchval("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"PostgreSQL health check failed: {e}")
        return False
