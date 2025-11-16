"""
Configuration management for voting consumer.

Loads configuration from environment variables with sensible defaults.
"""
import os


class Config:
    """Consumer configuration from environment variables."""

    # Redis configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    STREAM_NAME: str = os.getenv("STREAM_NAME", "votes")
    CONSUMER_GROUP: str = os.getenv("CONSUMER_GROUP", "vote-processors")
    CONSUMER_NAME: str = os.getenv("CONSUMER_NAME", "consumer-1")

    # PostgreSQL configuration
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/votes"
    )

    # Consumer behavior
    BATCH_SIZE: int = int(os.getenv("BATCH_SIZE", "10"))
    BLOCK_MS: int = int(os.getenv("BLOCK_MS", "5000"))
    MAX_RETRIES: int = int(os.getenv("MAX_RETRIES", "3"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate configuration values."""
        if cls.BATCH_SIZE < 1:
            raise ValueError("BATCH_SIZE must be >= 1")
        if cls.BLOCK_MS < 0:
            raise ValueError("BLOCK_MS must be >= 0")
        if cls.MAX_RETRIES < 1:
            raise ValueError("MAX_RETRIES must be >= 1")


# Validate configuration on import
Config.validate()
