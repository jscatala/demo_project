"""
Voting Consumer - Production Implementation

Event consumer for processing votes from Redis Streams to PostgreSQL.
Implements consumer group pattern with graceful shutdown.
"""
import asyncio
import signal
import sys
from typing import NoReturn

import structlog

from config import Config
from logger import setup_logging
import redis_client
import db_client

# Setup logging
logger = setup_logging()

# Shutdown flag
shutdown_flag = False


def signal_handler(signum: int, frame) -> None:
    """
    Handle shutdown signals (SIGTERM, SIGINT).

    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    global shutdown_flag

    sig_name = signal.Signals(signum).name
    logger.info("shutdown_signal_received", signal=sig_name)
    shutdown_flag = True


async def process_message(message_id: str, message_data: dict) -> bool:
    """
    Process a single vote message.

    Args:
        message_id: Redis Stream message ID.
        message_data: Message payload containing vote data.

    Returns:
        True if processing succeeded, False otherwise.
    """
    try:
        # Extract vote from message
        vote = message_data.get("option")

        if not vote:
            logger.warning(
                "malformed_message_missing_option",
                message_id=message_id,
                data=message_data
            )
            return False

        # Validate vote option
        if vote not in ("cats", "dogs"):
            logger.warning(
                "invalid_vote_option",
                message_id=message_id,
                vote=vote
            )
            return False

        logger.info(
            "processing_vote",
            message_id=message_id,
            vote=vote
        )

        # Increment vote in database with retries
        retries = 0
        while retries < Config.MAX_RETRIES:
            try:
                option, new_count = await db_client.increment_vote(vote)
                logger.info(
                    "vote_processed",
                    message_id=message_id,
                    option=option,
                    new_count=new_count
                )
                return True

            except Exception as db_error:
                retries += 1
                logger.error(
                    "database_error",
                    message_id=message_id,
                    vote=vote,
                    attempt=retries,
                    max_retries=Config.MAX_RETRIES,
                    error=str(db_error)
                )

                if retries < Config.MAX_RETRIES:
                    await asyncio.sleep(1 * retries)  # Exponential backoff
                else:
                    logger.error(
                        "vote_processing_failed",
                        message_id=message_id,
                        vote=vote
                    )
                    return False

        return False

    except Exception as e:
        logger.error(
            "message_processing_error",
            message_id=message_id,
            error=str(e),
            exc_info=True
        )
        return False


async def process_loop() -> None:
    """
    Main processing loop.

    Continuously reads messages from Redis Stream and processes them.
    Handles errors and respects shutdown flag.
    """
    logger.info("starting_consumer_loop")

    while not shutdown_flag:
        try:
            # Read messages from Redis Stream
            messages = await redis_client.read_messages()

            if not messages:
                # No messages available (timeout)
                continue

            logger.info("messages_received", count=len(messages))

            # Process each message
            for message_id, message_data in messages:
                if shutdown_flag:
                    logger.info("shutdown_during_processing")
                    break

                success = await process_message(message_id, message_data)

                # Acknowledge message if processed successfully or malformed
                # (we don't want to retry malformed messages forever)
                if success or not message_data.get("vote"):
                    await redis_client.ack_message(message_id)

        except Exception as e:
            logger.error(
                "loop_error",
                error=str(e),
                exc_info=True
            )
            # Brief pause before retrying
            await asyncio.sleep(1)

    logger.info("consumer_loop_stopped")


async def startup() -> None:
    """Initialize consumer resources."""
    logger.info(
        "consumer_starting",
        version="0.2.0",
        stream=Config.STREAM_NAME,
        group=Config.CONSUMER_GROUP,
        consumer=Config.CONSUMER_NAME
    )

    # Ensure consumer group exists
    await redis_client.ensure_consumer_group()

    # Initialize database pool
    await db_client.get_pool()

    logger.info("consumer_initialized")


async def shutdown() -> None:
    """Clean up consumer resources."""
    logger.info("consumer_shutting_down")

    # Close connections
    await redis_client.close_client()
    await db_client.close_pool()

    logger.info("consumer_shutdown_complete")


async def main_async() -> NoReturn:
    """
    Main async entry point.

    Sets up signal handlers, runs processing loop, and handles shutdown.
    """
    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # Startup
        await startup()

        # Run processing loop
        await process_loop()

    except Exception as e:
        logger.error("fatal_error", error=str(e), exc_info=True)
        sys.exit(1)

    finally:
        # Shutdown
        await shutdown()

    logger.info("consumer_exiting")
    sys.exit(0)


def main() -> NoReturn:
    """Synchronous entry point."""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
