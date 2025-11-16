# Voting API

FastAPI application for Cats vs Dogs voting system with Redis Streams and PostgreSQL.

## Features

- **POST /api/vote** - Submit vote (cats or dogs)
- **GET /api/results** - Get current vote results
- **Health endpoints** - `/health` and `/ready` for Kubernetes probes
- **Security** - CORS, security headers, request size limits
- **Caching** - 2-second result caching
- **Event streaming** - Redis Streams for vote processing

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export REDIS_URL=redis://localhost:6379
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/votes
export CORS_ORIGINS=http://localhost:3000

# Run application
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Docker

```bash
# Build image
docker build -t api:0.3.2 .

# Run container
docker run -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/votes \
  api:0.3.2
```

## Environment Variables

### Required

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/votes` |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Comma-separated allowed origins | `http://localhost:3000` |
| `MAX_REQUEST_SIZE` | Max request body size in bytes | `1048576` (1MB) |
| `ENVIRONMENT` | Environment name (enables HSTS if "production") | `development` |

## Security Configuration

### CORS (Cross-Origin Resource Sharing)

The API implements restrictive CORS policies:

```python
# Allowed origins (comma-separated in env var)
CORS_ORIGINS=http://localhost:3000,https://voting.example.com

# Allowed methods
GET, POST, OPTIONS

# Allowed headers
Content-Type, Authorization, Accept
```

**Important:** Never use wildcard (`*`) origins in production.

### Security Headers

All responses include security headers:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing |
| `Content-Security-Policy` | `default-src 'self'` | XSS protection |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS protection |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer control |
| `Strict-Transport-Security` | `max-age=31536000` | HTTPS enforcement (production only) |

### Request Size Limits

Requests larger than `MAX_REQUEST_SIZE` are rejected with `413 Payload Too Large`.

```bash
# Set custom limit (in bytes)
export MAX_REQUEST_SIZE=2097152  # 2MB
```

### Input Validation

All inputs are validated using Pydantic models:

```python
class VoteRequest(BaseModel):
    option: Literal["cats", "dogs"]

    class Config:
        extra = "forbid"  # Reject unknown fields
```

## API Endpoints

### POST /api/vote

Submit a vote for cats or dogs.

**Request:**
```json
{
  "option": "cats"
}
```

**Response (201):**
```json
{
  "message": "Vote recorded successfully",
  "option": "cats",
  "stream_id": "1763260175197-0"
}
```

**Errors:**
- `422` - Invalid option (not cats or dogs)
- `503` - Redis unavailable

### GET /api/results

Get current vote results.

**Response (200):**
```json
{
  "cats": 150,
  "dogs": 100,
  "total": 250,
  "cats_percentage": 60.0,
  "dogs_percentage": 40.0,
  "last_updated": "2025-11-15T12:00:00Z"
}
```

**Cache:** Results cached for 2 seconds (`Cache-Control: max-age=2`)

**Errors:**
- `503` - Database unavailable

### GET /health

Liveness probe for Kubernetes.

**Response (200):**
```json
{
  "status": "healthy"
}
```

### GET /ready

Readiness probe for Kubernetes.

**Response (200):**
```json
{
  "status": "ready"
}
```

## Architecture

```
POST /vote → Redis Stream "votes" → Consumer → PostgreSQL
GET /results ← PostgreSQL (cached 2s) ←
```

### Dependencies

- **FastAPI** 0.115.0 - Web framework
- **Redis** 5.2.0 - Event streaming
- **asyncpg** 0.30.0 - PostgreSQL client
- **Pydantic** 2.9.2 - Validation

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_security.py
```

## Database Schema

Uses PostgreSQL function for results:

```sql
SELECT * FROM get_vote_results();
-- Returns: option, count, percentage, updated_at
```

See `helm/templates/configs/postgres-configmap.yaml` for full schema.

## Production Deployment

### Kubernetes

Deployed via Helm chart:

```bash
helm install voting-api ./helm \
  --set images.api.tag=0.3.2 \
  --set api.replicas=3
```

### Security Checklist

- [ ] Set `ENVIRONMENT=production` for HSTS
- [ ] Configure specific `CORS_ORIGINS` (no wildcards)
- [ ] Use secrets for `DATABASE_URL` and `REDIS_URL`
- [ ] Enable TLS/HTTPS at ingress level
- [ ] Set appropriate `MAX_REQUEST_SIZE`
- [ ] Configure rate limiting at ingress/Gateway API
- [ ] Enable resource limits in Kubernetes

## Development

### Code Standards

- Follow `docs/CONVENTIONS.md`
- Line length: 88 characters (Black formatter)
- Type hints required
- Google-style docstrings

### Commit Format

```
feat(api): add new feature
fix(api): fix bug
docs(api): update documentation
```

## Version

Current version: **0.3.2**

### Changelog

- **0.3.2** - Security enhancements (headers, CORS restrictions, size limits)
- **0.3.1** - GET /results endpoint with PostgreSQL
- **0.3.0** - POST /vote endpoint with Redis Streams
- **0.2.1** - Production Dockerfile with distroless
- **0.1.0** - Initial setup

## License

See project root LICENSE file.
