"""Results service for fetching vote results."""
import time
from datetime import datetime
from typing import Optional
import asyncpg
import logging

from models import VoteResults

logger = logging.getLogger(__name__)

# Simple in-memory cache
_cache: Optional[dict] = None
_cache_timestamp: float = 0
CACHE_TTL_SECONDS = 2


class ResultsServiceError(Exception):
    """Base exception for results service errors."""

    pass


class DatabaseUnavailableError(ResultsServiceError):
    """Raised when database is unavailable."""

    pass


async def fetch_vote_results(db_pool: asyncpg.Pool) -> VoteResults:
    """Fetch current vote results from PostgreSQL.

    Uses get_vote_results() database function to retrieve aggregated counts.
    Implements 2-second cache to reduce database load.

    Args:
        db_pool: PostgreSQL connection pool

    Returns:
        VoteResults with current counts and percentages

    Raises:
        DatabaseUnavailableError: If database operation fails
    """
    global _cache, _cache_timestamp

    # Check cache
    current_time = time.time()
    if _cache and (current_time - _cache_timestamp) < CACHE_TTL_SECONDS:
        logger.debug("Returning cached results")
        return _cache

    try:
        # Call database function
        async with db_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM get_vote_results()")

        # Transform rows to dict for easy access
        results_dict = {row["option"]: row for row in rows}

        # Extract data (handle missing options gracefully)
        cats_data = results_dict.get("cats", {})
        dogs_data = results_dict.get("dogs", {})

        cats_count = cats_data.get("count", 0)
        dogs_count = dogs_data.get("count", 0)
        total = cats_count + dogs_count

        # Get latest updated_at timestamp
        last_updated = max(
            cats_data.get("updated_at", datetime.now()),
            dogs_data.get("updated_at", datetime.now()),
        )

        # Build response
        vote_results = VoteResults(
            cats=cats_count,
            dogs=dogs_count,
            total=total,
            cats_percentage=float(cats_data.get("percentage", 0.0)),
            dogs_percentage=float(dogs_data.get("percentage", 0.0)),
            last_updated=last_updated,
        )

        # Update cache
        _cache = vote_results
        _cache_timestamp = current_time

        logger.info(
            f"Fetched vote results: cats={cats_count}, "
            f"dogs={dogs_count}, total={total}"
        )

        return vote_results

    except Exception as e:
        logger.error(f"Failed to fetch vote results: {e}")
        raise DatabaseUnavailableError(f"Database operation failed: {e}")


def clear_cache() -> None:
    """Clear the results cache.

    Useful for testing or manual cache invalidation.
    """
    global _cache, _cache_timestamp
    _cache = None
    _cache_timestamp = 0
    logger.debug("Results cache cleared")
