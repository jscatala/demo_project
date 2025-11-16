"""
Redis Streams client for voting consumer.

Manages Redis connection and consumer group operations.
"""
import redis.asyncio as redis
import structlog

from config import Config

logger = structlog.get_logger()

# Global Redis client
_client: redis.Redis | None = None


async def get_client() -> redis.Redis:
    """
    Get or create Redis client.

    Returns:
        Redis client instance.

    Raises:
        Exception: If connection fails.
    """
    global _client

    if _client is None:
        logger.info("creating_redis_client", url=Config.REDIS_URL)
        _client = redis.from_url(
            Config.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        # Test connection
        await _client.ping()
        logger.info("redis_client_created")

    return _client


async def close_client() -> None:
    """Close Redis client gracefully."""
    global _client

    if _client is not None:
        logger.info("closing_redis_client")
        await _client.aclose()
        _client = None
        logger.info("redis_client_closed")


async def ensure_consumer_group() -> None:
    """
    Create consumer group if it doesn't exist.

    Uses XGROUP CREATE with MKSTREAM to create stream and group.
    Ignores error if group already exists.
    """
    client = await get_client()

    try:
        await client.xgroup_create(
            name=Config.STREAM_NAME,
            groupname=Config.CONSUMER_GROUP,
            id="0",
            mkstream=True,
        )
        logger.info(
            "consumer_group_created",
            stream=Config.STREAM_NAME,
            group=Config.CONSUMER_GROUP
        )
    except redis.ResponseError as e:
        if "BUSYGROUP" in str(e):
            logger.info(
                "consumer_group_exists",
                stream=Config.STREAM_NAME,
                group=Config.CONSUMER_GROUP
            )
        else:
            raise


async def read_messages() -> list[tuple[str, dict]]:
    """
    Read messages from Redis Stream using consumer group.

    Uses XREADGROUP to read pending messages for this consumer.
    Blocks for Config.BLOCK_MS milliseconds if no messages available.

    Returns:
        List of (message_id, message_data) tuples.
        Empty list if no messages available.

    Raises:
        Exception: If Redis operation fails.
    """
    client = await get_client()

    # XREADGROUP GROUP group consumer [BLOCK ms] [COUNT count] STREAMS key [key ...] id [id ...]
    response = await client.xreadgroup(
        groupname=Config.CONSUMER_GROUP,
        consumername=Config.CONSUMER_NAME,
        streams={Config.STREAM_NAME: ">"},
        count=Config.BATCH_SIZE,
        block=Config.BLOCK_MS,
    )

    if not response:
        return []

    # response format: [(stream_name, [(message_id, message_data), ...])]
    stream_name, messages = response[0]

    logger.debug(
        "messages_read",
        stream=stream_name,
        count=len(messages)
    )

    return messages


async def ack_message(message_id: str) -> None:
    """
    Acknowledge message processing with XACK.

    Args:
        message_id: Redis Stream message ID to acknowledge.

    Raises:
        Exception: If XACK fails.
    """
    client = await get_client()

    await client.xack(
        Config.STREAM_NAME,
        Config.CONSUMER_GROUP,
        message_id
    )

    logger.debug("message_acked", message_id=message_id)
