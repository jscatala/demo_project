# Build stage
FROM python:3.11-slim AS builder

WORKDIR /build

# Install uv - fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install with uv
COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

# Production stage - Google Distroless Python 3.12
FROM gcr.io/distroless/python3-debian12:nonroot

WORKDIR /app

# Copy Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /home/nonroot/.local/lib/python3.11/site-packages

# Copy application code
COPY main.py models.py redis_client.py ./
COPY routes/ routes/
COPY services/ services/

# Expose port
EXPOSE 8000

# Distroless runs as non-root user 65532 by default
# Distroless Python ENTRYPOINT is already python, just pass module args
CMD ["-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
