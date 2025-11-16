"""
Voting API - Cats vs Dogs
FastAPI application for voting system with Redis Streams
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from redis_client import init_redis, close_redis
from db_client import init_db, close_db
from routes.vote import router as vote_router
from routes.results import router as results_router
from middleware.security import (
    SecurityHeadersMiddleware,
    RequestSizeLimitMiddleware,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager.

    Handles startup and shutdown events for Redis and PostgreSQL connections.
    """
    # Startup
    logger.info("Starting Voting API")
    try:
        await init_redis()
        logger.info("Redis initialized successfully")

        await init_db()
        logger.info("PostgreSQL initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down Voting API")
    await close_redis()
    await close_db()


app = FastAPI(
    title="Voting API",
    version="0.3.2",
    description="API for Cats vs Dogs voting system",
    lifespan=lifespan,
)

# Security middleware (order matters: first added = last executed)
app.add_middleware(RequestSizeLimitMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware (more restrictive configuration)
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
    max_age=600,  # Cache preflight requests for 10 minutes
)

# Include routers
app.include_router(vote_router)
app.include_router(results_router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voting API - Cats vs Dogs",
        "version": "0.3.2",
        "status": "running"
    }


@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    """Health check endpoint for liveness probe"""
    return {"status": "healthy"}


@app.api_route("/ready", methods=["GET", "HEAD"])
async def ready():
    """Readiness check endpoint"""
    return {"status": "ready"}
