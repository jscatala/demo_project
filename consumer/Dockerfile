# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies (empty for now, but prepared for future)
COPY requirements.txt .
# RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy dependencies from builder (if any)
# COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code
COPY --chown=appuser:appuser main.py .

# Update PATH to use appuser's local bin
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER 1000

# Run application
CMD ["python", "main.py"]
