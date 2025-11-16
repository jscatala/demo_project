"""Vote endpoint routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from redis.asyncio import Redis
import logging

from models import VoteRequest, VoteResponse
from redis_client import get_redis
from services.vote_service import write_vote_to_stream, RedisUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["voting"])


@router.post(
    "/vote",
    response_model=VoteResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Vote recorded successfully"},
        400: {"description": "Invalid vote option"},
        503: {"description": "Redis service unavailable"},
    },
)
async def submit_vote(
    vote: VoteRequest, redis_client: Redis = Depends(get_redis)
) -> VoteResponse:
    """Submit a vote for cats or dogs.

    Args:
        vote: Vote request containing option (cats or dogs)
        redis_client: Redis client (injected dependency)

    Returns:
        Vote response with confirmation

    Raises:
        HTTPException: 503 if Redis is unavailable
    """
    logger.info(f"Received vote: option={vote.option}")

    try:
        # Write vote to Redis Stream
        stream_id = await write_vote_to_stream(redis_client, vote.option)

        logger.info(f"Vote recorded: option={vote.option}, stream_id={stream_id}")

        return VoteResponse(
            message="Vote recorded successfully",
            option=vote.option,
            stream_id=stream_id,
        )

    except RedisUnavailableError as e:
        logger.error(f"Redis unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Voting service temporarily unavailable",
        )
