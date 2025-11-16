"""Vote service for handling vote business logic."""
import time
import uuid
from typing import Literal
from redis.asyncio import Redis
import logging

logger = logging.getLogger(__name__)


class VoteServiceError(Exception):
    """Base exception for vote service errors."""

    pass


class RedisUnavailableError(VoteServiceError):
    """Raised when Redis is unavailable."""

    pass


async def write_vote_to_stream(
    redis_client: Redis, option: Literal["cats", "dogs"]
) -> str:
    """Write vote event to Redis Stream.

    Args:
        redis_client: Redis client instance
        option: Vote option (cats or dogs)

    Returns:
        Redis Stream message ID

    Raises:
        RedisUnavailableError: If Redis operation fails
    """
    try:
        # Generate unique request ID for tracking
        request_id = str(uuid.uuid4())
        timestamp = int(time.time() * 1000)  # Milliseconds

        # Write to Redis Stream using XADD
        message_id = await redis_client.xadd(
            "votes",
            {"option": option, "timestamp": str(timestamp), "request_id": request_id},
        )

        logger.info(
            f"Vote written to stream: option={option}, "
            f"request_id={request_id}, stream_id={message_id}"
        )

        return message_id

    except Exception as e:
        logger.error(f"Failed to write vote to Redis Stream: {e}")
        raise RedisUnavailableError(f"Redis operation failed: {e}")
