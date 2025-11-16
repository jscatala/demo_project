"""Redis client singleton for connection pooling."""
import os
from typing import Optional
from redis.asyncio import Redis, ConnectionPool
import logging

logger = logging.getLogger(__name__)

# Global Redis client instance
_redis_client: Optional[Redis] = None


async def init_redis() -> None:
    """Initialize Redis connection pool.

    Creates a singleton Redis client with connection pooling.
    Uses REDIS_URL environment variable for configuration.

    Raises:
        ConnectionError: If unable to connect to Redis
    """
    global _redis_client

    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    logger.info(f"Initializing Redis connection to {redis_url}")

    try:
        pool = ConnectionPool.from_url(
            redis_url, decode_responses=True, max_connections=10
        )
        _redis_client = Redis(connection_pool=pool)

        # Test connection
        await _redis_client.ping()
        logger.info("Redis connection established successfully")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise ConnectionError(f"Redis connection failed: {e}")


async def close_redis() -> None:
    """Close Redis connection pool.

    Cleanup function to be called on application shutdown.
    """
    global _redis_client

    if _redis_client:
        await _redis_client.close()
        logger.info("Redis connection closed")
        _redis_client = None


async def get_redis() -> Redis:
    """Get Redis client instance for dependency injection.

    Returns:
        Redis client instance

    Raises:
        RuntimeError: If Redis client not initialized
    """
    if _redis_client is None:
        raise RuntimeError("Redis client not initialized")
    return _redis_client


async def check_redis_health() -> bool:
    """Check Redis connection health.

    Returns:
        True if Redis is reachable, False otherwise
    """
    try:
        client = await get_redis()
        await client.ping()
        return True
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        return False
