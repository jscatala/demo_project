"""
Voting API - Hello World
FastAPI application for voting system
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Voting API",
    version="0.1.0",
    description="API for Cats vs Dogs voting system"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Will be restricted in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Voting API - Hello World",
        "version": "0.1.0",
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
