# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install dependencies (empty for now, but prepared for future)
COPY requirements.txt .
# RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Copy dependencies from builder (if any)
# COPY --from=builder /root/.local /root/.local

# Copy application code
COPY main.py .

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Update PATH
ENV PATH=/root/.local/bin:$PATH

# Switch to non-root user
USER 1000

# Run application
CMD ["python", "main.py"]
