"""Results endpoint routes."""
from fastapi import APIRouter, Depends, HTTPException, status, Response
import asyncpg
import logging

from models import VoteResults
from db_client import get_db
from services.results_service import (
    fetch_vote_results,
    DatabaseUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["results"])


@router.get(
    "/results",
    response_model=VoteResults,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Current vote results"},
        503: {"description": "Database service unavailable"},
        500: {"description": "Internal server error"},
    },
)
async def get_results(
    response: Response, db_pool: asyncpg.Pool = Depends(get_db)
) -> VoteResults:
    """Get current voting results.

    Returns aggregated vote counts and percentages for cats vs dogs.
    Results are cached for 2 seconds to reduce database load.

    Args:
        response: FastAPI Response object for headers
        db_pool: PostgreSQL connection pool (injected dependency)

    Returns:
        Vote results with counts and percentages

    Raises:
        HTTPException: 503 if database is unavailable
        HTTPException: 500 for other errors
    """
    logger.info("Fetching vote results")

    # Set cache control header
    response.headers["Cache-Control"] = "public, max-age=2"

    try:
        results = await fetch_vote_results(db_pool)
        logger.info(
            f"Results returned: cats={results.cats}, "
            f"dogs={results.dogs}, total={results.total}"
        )
        return results

    except DatabaseUnavailableError as e:
        logger.error(f"Database unavailable: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Results service temporarily unavailable",
        )

    except Exception as e:
        logger.error(f"Unexpected error fetching results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch results",
        )
