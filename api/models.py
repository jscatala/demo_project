"""Pydantic models for API requests and responses."""
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


class VoteRequest(BaseModel):
    """Request model for voting endpoint.

    Attributes:
        option: The vote option, must be either "cats" or "dogs"
    """

    option: Literal["cats", "dogs"] = Field(
        ..., description="Vote option: cats or dogs"
    )

    class Config:
        extra = "forbid"  # Reject unknown fields for security


class VoteResponse(BaseModel):
    """Response model for successful vote submission.

    Attributes:
        message: Success message
        option: The vote option that was recorded
        stream_id: Redis Stream message ID
    """

    message: str
    option: str
    stream_id: str


class VoteOption(BaseModel):
    """Individual vote option result.

    Attributes:
        option: The vote option (cats or dogs)
        count: Number of votes for this option
        percentage: Percentage of total votes (0-100)
    """

    option: Literal["cats", "dogs"]
    count: int
    percentage: float = Field(..., ge=0, le=100)


class VoteResults(BaseModel):
    """Response model for vote results endpoint.

    Attributes:
        cats: Vote count for cats
        dogs: Vote count for dogs
        total: Total number of votes
        cats_percentage: Percentage for cats (0-100)
        dogs_percentage: Percentage for dogs (0-100)
        last_updated: Timestamp of last vote update
    """

    cats: int = Field(..., ge=0)
    dogs: int = Field(..., ge=0)
    total: int = Field(..., ge=0)
    cats_percentage: float = Field(..., ge=0, le=100)
    dogs_percentage: float = Field(..., ge=0, le=100)
    last_updated: datetime
