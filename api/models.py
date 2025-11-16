"""Pydantic models for API requests and responses."""
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
