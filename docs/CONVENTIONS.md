# Project Conventions

Standards and best practices for code, security, and infrastructure.

## Git Workflow

### Commits
- **Format:** [Conventional Commits](../CONTRIBUTING.md#conventional-commits)
- **Examples:** `feat(api): add vote endpoint`, `fix(consumer): handle empty stream`

### Branches
- `feature/description` - New features
- `bugfix/description` - Bug fixes
- `hotfix/description` - Critical fixes
- `docs/description` - Documentation

### Versioning
- **Semantic Versioning:** MAJOR.MINOR.PATCH
- **Tags:** `v1.0.0`, `v1.2.3-beta`
- **Changelog:** Keep a Changelog format

## Test-Driven Development (TDD)

**Mandatory for all new features:** Write tests BEFORE implementation.

### TDD Cycle

1. **🔴 Red:** Write a failing test
2. **🟢 Green:** Write minimal code to pass
3. **🔵 Refactor:** Improve code while keeping tests passing

### Testing Tiers

**Tier 1: Unit Tests (Docker)**
- **Scope:** Single component in isolation
- **Environment:** Docker container
- **Speed:** Fast (<5s)
- **Examples:**
  - Frontend components (vitest)
  - API endpoints (pytest)
  - Utility functions

**Tier 2: Integration Tests (Minikube + Helm)**
- **Scope:** Multi-component interactions
- **Environment:** Minikube cluster with Helm
- **Speed:** Medium (30s-2min)
- **Examples:**
  - Frontend → API flow
  - API → Redis → Consumer → PostgreSQL
  - End-to-end vote submission

**Tier 3: System Tests (Minikube + Helm)**
- **Scope:** Full system behavior
- **Environment:** Complete Helm deployment
- **Speed:** Slow (2-5min)
- **Examples:**
  - Load testing
  - Failure recovery
  - Security validation

### Testing Commands

**Unit Tests (Docker):**
```bash
# Frontend component tests
docker run --rm frontend-test:latest npm test -- --run

# API unit tests
docker run --rm api-test:latest pytest tests/unit/

# Consumer unit tests
docker run --rm consumer-test:latest pytest tests/unit/
```

**Integration Tests (Minikube):**
```bash
# Deploy full stack
helm install voting-test ./helm -f helm/values-test.yaml

# Run integration tests
kubectl run integration-tests --image=voting-integration-tests:latest \
  --restart=Never --rm -it

# Cleanup
helm uninstall voting-test
```

### Validation Phase Requirements

**Before marking a phase complete:**
1. ✅ All unit tests passing (Docker)
2. ✅ All integration tests passing (Minikube) - if multi-component
3. ✅ Coverage thresholds met
4. ✅ Validation protocol executed
5. ✅ Session log documented

### TDD Example Workflow

**Example: Adding POST /vote endpoint**

```python
# Step 1: RED - Write failing test
def test_vote_endpoint_accepts_cats():
    response = client.post("/api/vote", json={"option": "cats"})
    assert response.status_code == 201
    # Test fails - endpoint doesn't exist yet

# Step 2: GREEN - Minimal implementation
@app.post("/api/vote", status_code=201)
async def vote(request: VoteRequest):
    return {"status": "ok"}
    # Test passes - minimal code

# Step 3: REFACTOR - Improve while tests pass
@app.post("/api/vote", status_code=201)
async def vote(request: VoteRequest):
    await redis_client.xadd("votes", {"vote": request.option})
    return {"status": "accepted", "vote": request.option}
    # Tests still pass - better implementation
```

### TDD Anti-Patterns

**❌ DON'T:**
- Write implementation first, tests later
- Skip tests for "simple" code
- Test only happy paths
- Mock everything (integration tests need real dependencies)
- Run tests manually (automate in Docker/CI)

**✅ DO:**
- Write test first, see it fail
- Test edge cases and errors
- Use real dependencies for integration tests
- Run full test suite before commit
- Keep tests fast and focused

## Atomic Principles

### Atomic Functions

**Every function must be atomic:**
- Single responsibility (one clear purpose)
- Self-contained and understandable in isolation
- Clear inputs and outputs
- Maximum 50 lines (ideally 20 or less)
- Descriptive name that explains what it does

**✅ GOOD - Atomic function:**
```python
async def validate_vote_option(option: str) -> Literal["cats", "dogs"]:
    """Validate and normalize vote option.

    Args:
        option: Raw vote option from user

    Returns:
        Validated option

    Raises:
        ValueError: If option is invalid
    """
    normalized = option.lower().strip()
    if normalized not in ["cats", "dogs"]:
        raise ValueError(f"Invalid option: {option}")
    return normalized
```

**❌ BAD - Non-atomic function:**
```python
async def process_vote(option: str, db, redis, user_ip):
    # Validates, writes to Redis, updates DB, logs, sends metrics...
    # Too many responsibilities, hard to test, hard to understand
    pass
```

**Refactor into atomic functions:**
```python
async def validate_vote(option: str) -> str:
    """Validate vote option."""
    # Single responsibility: validation

async def write_vote_event(option: str, redis_client) -> str:
    """Write vote to Redis Stream."""
    # Single responsibility: event writing

async def record_vote_metric(option: str, user_ip: str):
    """Record voting metrics."""
    # Single responsibility: metrics
```

### Atomic Commits

**Each commit must be atomic:**
- One logical change per commit
- Code is functional before and after the commit
- Can be reverted independently without breaking the system
- Follows Conventional Commits format

**Atomic commit rules:**
1. **Functional state:** Every commit leaves code in working state
2. **Single purpose:** One feature/fix/refactor per commit
3. **Complete change:** All related files updated together
4. **Testable:** Can run tests after this commit
5. **Revertable:** Can safely revert without dependencies

**✅ GOOD - Atomic commits:**
```bash
# Commit 1: Complete feature
feat(api): add vote validation endpoint

- Add validate_vote_option function
- Add POST /vote/validate endpoint
- Add tests for validation logic
- Update API documentation

# Commit 2: Separate feature
feat(api): add rate limiting middleware

- Add rate limiting to vote endpoint
- Configure limits in environment
- Add rate limit tests
```

**❌ BAD - Non-atomic commits:**
```bash
# Too broad, multiple features
feat(api): add vote validation, rate limiting, and metrics

# Leaves code broken
feat(api): add vote endpoint (missing tests, incomplete)

# Mixed purposes
feat(api): add validation and fix bug in consumer
```

### Code Always Functional

**Never commit broken code:**
- All tests must pass
- No syntax errors
- No missing imports
- No undefined variables
- API endpoints return valid responses
- Services start without errors

**Before committing:**
```bash
# Run linters
ruff check .
mypy .

# Run tests
pytest

# Test locally
helm install test-release ./helm
kubectl port-forward svc/api 8000:8000
curl http://localhost:8000/health  # Should return 200
```

**Work-in-progress:**
- Use feature branches for incomplete work
- Don't merge to main until fully functional
- Use git stash for temporary state

**Example workflow:**
```bash
# 1. Implement atomic function
def validate_vote_option(option: str) -> str:
    # Complete implementation

# 2. Add tests
def test_validate_vote_option_with_cats():
    assert validate_vote_option("cats") == "cats"

# 3. Ensure functional
pytest  # All pass

# 4. Atomic commit
git add validation.py tests/test_validation.py
git commit -m "feat(api): add vote option validation

- Validate cats/dogs input
- Normalize to lowercase
- Raise ValueError for invalid options
- 100% test coverage"
```

## Code Standards

### Python (API, Consumer)

**Style:**
- PEP 8 compliance
- Line length: 88 characters (Black formatter)
- Type hints for all functions

```python
from typing import Literal

async def record_vote(option: Literal["cats", "dogs"]) -> int:
    """Record a vote in PostgreSQL.

    Args:
        option: The vote option (cats or dogs)

    Returns:
        Updated vote count
    """
    pass
```

**Tools:**
- Linter: `ruff` or `flake8`
- Formatter: `black`
- Type checker: `mypy`

**FastAPI Conventions:**
- Use dependency injection for database connections
- Pydantic models for request/response validation
- Async handlers for I/O operations

**Security:**
- Use parameterized queries (SQLAlchemy/asyncpg)
- Validate all inputs with Pydantic
- No secrets in code (use K8s Secrets)

### TypeScript (Frontend)

**Style:**
- ESLint with recommended rules
- Prettier for formatting
- Strict TypeScript mode

```typescript
interface VoteOption {
  name: "cats" | "dogs";
  count: number;
  percentage: number;
}

async function submitVote(option: "cats" | "dogs"): Promise<void> {
  // Implementation
}
```

**Tools:**
- Linter: `eslint`
- Formatter: `prettier`
- Build: `vite` or `webpack`

**React/UI Conventions:**
- Functional components only
- Hooks for state management
- TypeScript for all components

## Docker

### Multistage Builds

All Dockerfiles must use multistage builds for minimal images:

```dockerfile
# Build stage
FROM python:3.11-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
USER 1000
CMD ["python", "app.py"]
```

### Security Requirements

- **Non-root user:** All containers run as UID 1000+
- **Minimal base:** Use `slim`, `alpine`, or `distroless` images
- **No secrets:** Environment variables from K8s Secrets
- **Scanning:** Run `trivy` or `snyk` on all images
- **Latest patches:** Rebuild images regularly for security updates

### Image Naming

```
<registry>/<project>/<service>:<version>
example: ghcr.io/myorg/voting-api:v1.2.3
```

## Kubernetes

### Resource Naming

- **Lowercase kebab-case:** `voting-api`, `redis-stream`
- **Include app label:** `app: voting-frontend`
- **Namespace:** `voting-app` (production), `voting-app-dev` (local)

### Required Manifests

All Deployments/Jobs must include:

```yaml
spec:
  template:
    spec:
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
      containers:
      - name: app
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
```

### Helm Conventions

- **Values file:** Parameterize all environment-specific configs
- **Naming:** `{{ include "voting.fullname" . }}`
- **Labels:** Use standard labels (app.kubernetes.io/*)
- **Secrets:** Never in values.yaml (use sealed-secrets or external-secrets)

## Security Practices

### Input Validation

**API endpoints:**
```python
from pydantic import BaseModel, Field
from typing import Literal

class VoteRequest(BaseModel):
    option: Literal["cats", "dogs"] = Field(..., description="Vote option")

    class Config:
        extra = "forbid"  # Reject unknown fields
```

### SQL Injection Prevention

**Always use parameterized queries:**

```python
# ✅ GOOD
await conn.execute(
    "UPDATE votes SET count = count + 1 WHERE option = $1",
    option
)

# ❌ BAD
await conn.execute(
    f"UPDATE votes SET count = count + 1 WHERE option = '{option}'"
)
```

### Rate Limiting

**Ingress annotations:**
```yaml
annotations:
  nginx.ingress.kubernetes.io/limit-rps: "10"
  nginx.ingress.kubernetes.io/limit-connections: "5"
```

### CORS Configuration

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://voting.example.com"],  # Specific origins only
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
```

### Security Headers

```python
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["voting.example.com"])
```

## Testing

### Unit Tests
- **Python:** `pytest` with `pytest-asyncio`
- **TypeScript:** `vitest` or `jest`
- **Coverage:** Minimum 80%

### Integration Tests
- Test event flow: API → Redis → Consumer → PostgreSQL
- Use test fixtures for databases (pytest fixtures, testcontainers)

### Naming
- `test_<function>_<scenario>_<expected>`
- Example: `test_record_vote_with_invalid_option_raises_error`

## Documentation

### Code Comments
- Docstrings for all public functions (Google style)
- Inline comments for complex logic only
- No commented-out code (use git history)

### README Updates
- Update README.md when adding major features
- Keep Quick Start section current
- Link to ADRs for architectural changes

## Environment Variables

### Naming Convention
- `UPPERCASE_SNAKE_CASE`
- Prefix with service name: `API_DATABASE_URL`, `CONSUMER_REDIS_URL`

### Required Variables
```bash
# API
API_DATABASE_URL=postgresql://...
API_REDIS_URL=redis://...
API_CORS_ORIGINS=https://voting.example.com

# Consumer
CONSUMER_REDIS_URL=redis://...
CONSUMER_DATABASE_URL=postgresql://...
CONSUMER_GROUP_NAME=vote-processors
```

### Secrets Management
- **Local:** `.env` file (gitignored)
- **K8s:** Kubernetes Secrets
- **Never commit:** API keys, passwords, tokens

## Performance

### Database
- Use connection pooling (asyncpg pool)
- Index frequently queried columns
- Use prepared statements

### Redis
- Configure maxmemory policy: `allkeys-lru`
- Set stream trimming: `MAXLEN ~ 10000`
- Monitor memory usage

### API
- Use async handlers for I/O
- Enable gzip compression
- Set appropriate timeout values

## Monitoring (Future)

When implementing observability:
- **Logs:** Structured JSON (use `structlog`)
- **Metrics:** Prometheus format (`/metrics` endpoint)
- **Tracing:** OpenTelemetry (future enhancement)

## Questions?

See [CONTRIBUTING.md](../CONTRIBUTING.md) or open a discussion.
