"""
PostgreSQL database client for voting consumer.

Manages connection pool and provides vote increment functionality.
"""
import asyncpg
import structlog

from config import Config

logger = structlog.get_logger()

# Global connection pool
_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """
    Get or create PostgreSQL connection pool.

    Returns:
        Connection pool instance.

    Raises:
        Exception: If pool creation fails.
    """
    global _pool

    if _pool is None:
        logger.info("creating_postgres_pool", url=Config.DATABASE_URL.split("@")[0])
        _pool = await asyncpg.create_pool(
            Config.DATABASE_URL,
            min_size=2,
            max_size=10,
            command_timeout=10,
        )
        logger.info("postgres_pool_created")

    return _pool


async def close_pool() -> None:
    """Close PostgreSQL connection pool gracefully."""
    global _pool

    if _pool is not None:
        logger.info("closing_postgres_pool")
        await _pool.close()
        _pool = None
        logger.info("postgres_pool_closed")


async def increment_vote(option: str) -> tuple[str, int]:
    """
    Increment vote count for given option.

    Calls PostgreSQL increment_vote() function which atomically
    increments the vote count.

    Args:
        option: Vote option ('cats' or 'dogs').

    Returns:
        Tuple of (option, new_count).

    Raises:
        ValueError: If option is invalid.
        Exception: If database operation fails.
    """
    if option not in ("cats", "dogs"):
        raise ValueError(f"Invalid vote option: {option}")

    pool = await get_pool()

    async with pool.acquire() as conn:
        # Call increment_vote PostgreSQL function
        result = await conn.fetchrow(
            "SELECT * FROM increment_vote($1)",
            option
        )

        if result is None:
            raise Exception(f"increment_vote returned no result for {option}")

        new_option = result["option"]
        new_count = result["new_count"]

        logger.info(
            "vote_incremented",
            option=new_option,
            new_count=new_count
        )

        return new_option, new_count
