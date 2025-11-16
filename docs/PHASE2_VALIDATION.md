# Phase 2 Validation Protocol - Manual Checklist

**Purpose:** Verify backend services (FastAPI + Consumer) are correctly implemented and containerized before integration testing.

**Date:** 2025-11-16
**Phase:** 2 (Backend Core)
**Validator:** ___________

---

## Validation Checklist

### 1. Pre-Flight Checks

**1.1 Verify Docker Images Built**

```bash
# List consumer and API images
docker images | grep -E '(api|consumer)' | grep -E '(0.3|0.2)'

# Expected output:
# consumer   0.3.0   [IMAGE_ID]   [TIME]   223MB
# api        0.3.2   [IMAGE_ID]   [TIME]   166MB
```

- [X] api:0.3.2 image exists
- [X] consumer:0.3.0 image exists
- [X] Image sizes within expected range (API ~166MB, Consumer ~223MB)

**1.2 Verify Source Files**

```bash
# Check API structure
ls -l api/*.py api/middleware/ api/routes/ api/services/

# Check consumer structure
ls -l consumer/*.py

# Expected files:
# API: main.py, models.py, redis_client.py, db_client.py
# API middleware: security.py
# API routes: vote.py, results.py
# API services: vote_service.py, results_service.py
# Consumer: main.py, config.py, logger.py, redis_client.py, db_client.py
```

- [ ] API files present (modular structure)
- [ ] Consumer files present (modular structure)
- [ ] All Python files have .py extension

---

### 2. API Container Validation

**Important:** API requires Redis and PostgreSQL to start successfully. Most tests in this section (2.2 onwards) require these services running. Section 2.1 can be tested without dependencies to verify basic container functionality.

**2.1 Test API Container Startup**

**Note:** API will attempt to connect to Redis/PostgreSQL on startup. Without these services running, connection errors are expected but can be ignored for basic validation. The important checks are: no import errors and Uvicorn starts.

```bash
# Run API container (will show connection errors without Redis/PostgreSQL)
docker run --rm -d --name api-test -p 8000:8000 api:0.3.2

# Wait for startup
sleep 3

# Check logs
docker logs api-test

# Expected output includes:
# INFO:     Started server process [PID]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000
#
# Connection errors are EXPECTED without Redis/PostgreSQL:
# ERROR: Redis connection failed: Connection refused
# (This is OK for basic container validation)

# Stop container
docker stop api-test
```

- [X] API container starts without errors
- [X] Uvicorn starts on port 8000
- [X] No import errors
- [X] Application startup complete
- [X] Connection errors to Redis/DB expected (can be ignored)

**2.2 Test API Health Endpoints**

**Note:** API requires Redis and PostgreSQL to start. Run these services first:

```bash
# Start Redis and PostgreSQL (if not already running)
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
docker run -d --name postgres-test -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=votes \
  postgres:15-alpine

# Wait for services
sleep 3

# Start API with connections
docker run --rm -d --name api-test -p 8000:8000 \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/votes" \
  api:0.3.2

# Wait for API startup
sleep 3

# Test health endpoint
curl -I http://localhost:8000/health

# Expected: HTTP/1.1 200 OK

# Test ready endpoint
curl -I http://localhost:8000/ready

# Expected: HTTP/1.1 200 OK

# Stop containers
docker stop api-test redis-test postgres-test
docker rm redis-test postgres-test
```

- [X] /health endpoint returns 200 OK
- [X] /ready endpoint returns 200 OK
- [X] HEAD method supported on both endpoints

**2.3 Test API Security Headers**

**Note:** Assumes Redis/PostgreSQL still running from section 2.2. If not, start them first.

```bash
# Start API with CORS configuration
docker run --rm -d --name api-test -p 8000:8000 \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/votes" \
  -e CORS_ORIGINS="http://localhost:3000" \
  api:0.3.2

# Wait for startup
sleep 3

# Check security headers
curl -I http://localhost:8000/health

# Expected headers:
# x-frame-options: DENY
# x-content-type-options: nosniff
# content-security-policy: default-src 'self'
# x-xss-protection: 1; mode=block
# referrer-policy: strict-origin-when-cross-origin

# Stop API
docker stop api-test
```

- [X] X-Frame-Options header present
- [X] X-Content-Type-Options header present
- [X] Content-Security-Policy header present
- [X] X-XSS-Protection header present
- [X] Referrer-Policy header present

**2.4 Verify API Non-Root User**

**Note:** API uses distroless image (no shell). Use `docker inspect` to verify user.

```bash
# Check API configured user (distroless has no shell/id command)
docker inspect api:0.3.2 --format='User: {{.Config.User}}'

# Expected output:
# User: 65532

# Verify it's the distroless nonroot user (UID 65532)
```

- [X] API runs as UID 65532 (distroless nonroot)
- [X] Not running as root (root is UID 0)

**2.5 Test API Image Size**

```bash
# Check API image size
docker images api:0.3.2 --format "{{.Size}}"

# Expected: ~166MB (distroless base)
```

- [X] API image size ≤ 200MB
- [X] Using distroless base (verified in Dockerfile)

---

### 3. Consumer Container Validation

**3.1 Test Consumer Container Startup**

**Note:** Consumer will attempt to connect to Redis/PostgreSQL and fail. This is expected. The important validation points are: structured logging, no import errors, and graceful shutdown sequence.

```bash
# Run consumer (will fail to connect to Redis/DB, that's expected)
docker run --rm --name consumer-test consumer:0.3.0

# Expected output (JSON structured logs):
# {"event": "consumer_starting", "version": "0.2.0", ...}
# {"event": "creating_redis_client", ...}
# {"error": "...", "event": "fatal_error", ...}  <- Expected without Redis
# {"event": "consumer_shutting_down", ...}
# {"event": "closing_redis_client", ...}
# {"event": "consumer_shutdown_complete", ...}
#
# Connection errors are EXPECTED without Redis/PostgreSQL.
# Graceful shutdown sequence proves error handling works correctly.
```

- [X] Consumer container starts
- [X] Structured logging (JSON format with ISO timestamps)
- [X] Version 0.2.0 in startup log
- [X] No Python import errors
- [X] Graceful shutdown sequence on connection failure (expected behavior)

**3.2 Test Consumer Imports**

```bash
# Test all imports load
docker run --rm consumer:0.3.0 python -c "
import main
import config
import logger
import redis_client
import db_client
print('✓ All imports successful')
"

# Expected output:
# ✓ All imports successful
```

- [X] All Python modules import successfully
- [X] No ModuleNotFoundError
- [X] No syntax errors

**3.3 Verify Consumer Non-Root User**

```bash
# Check consumer runs as non-root
docker run --rm consumer:0.3.0 id

# Expected output:
# uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
```

- [X] Consumer runs as UID 1000 (appuser)
- [X] Not running as root

**3.4 Test Consumer Configuration**

```bash
# Test environment variable loading
docker run --rm \
  -e REDIS_URL="redis://test:6379" \
  -e DATABASE_URL="postgresql://test:5432/votes" \
  -e LOG_LEVEL="DEBUG" \
  consumer:0.3.0 python -c "
from config import Config
assert Config.REDIS_URL == 'redis://test:6379'
assert Config.DATABASE_URL == 'postgresql://test:5432/votes'
assert Config.LOG_LEVEL == 'DEBUG'
print('✓ Configuration loaded correctly')
"

# Expected output:
# ✓ Configuration loaded correctly
```

- [X] Environment variables loaded
- [X] Config validation works
- [X] Default values applied when env vars missing

**3.5 Test Consumer Image Size**

```bash
# Check consumer image size
docker images consumer:0.3.0 --format "{{.Size}}"

# Expected: ~223MB (Python 3.13-slim + dependencies)
```

- [X] Consumer image size ≤ 250MB
- [X] Size reasonable for Python 3.13 + asyncpg/redis/structlog

---

### 4. Helm Chart Validation

**4.1 Updated Values Validation**

```bash
# Check updated image tags
grep -A 2 "api:" helm/values.yaml
grep -A 2 "consumer:" helm/values.yaml

# Should show:
# api: tag: "0.3.2"
# consumer: tag: "0.3.0"

# Check consumer configuration
grep -A 10 "^consumer:" helm/values.yaml

# Should show:
# replicas, streamName, consumerGroup, batchSize, blockMs, maxRetries, logLevel
```

- [X] API image tag: 0.3.2
- [X] Consumer image tag: 0.3.0
- [X] Consumer replicas: 1
- [X] Consumer streamName: "votes"
- [X] Consumer consumerGroup: "vote-processors"
- [X] Consumer configuration present

**4.2 Consumer Deployment Validation**

```bash
# Render consumer deployment
helm template voting-test helm/ --show-only templates/consumer/deployment.yaml > /tmp/consumer-deploy.yaml

# Validate with kubectl
kubectl apply --dry-run=client -f /tmp/consumer-deploy.yaml

# Expected: deployment.apps/consumer created (dry run)

# Check environment variables
grep "name: REDIS_URL" -A 1 /tmp/consumer-deploy.yaml
grep "name: DATABASE_URL" -A 4 /tmp/consumer-deploy.yaml

# Should show 9 environment variables total
```

- [X] Consumer deployment renders successfully
- [X] Kubectl dry-run validation passes
- [X] 9 environment variables configured
- [X] DATABASE_URL from secret reference
- [X] REDIS_URL from values
- [X] CONSUMER_NAME from fieldRef (pod name)

**4.3 Security Context Validation**

```bash
# Check API deployment security
helm template voting-test helm/ --show-only templates/api/deployment.yaml | grep -A 10 "securityContext:"

# Should show:
# runAsNonRoot: true
# runAsUser: 1000 (or distroless default)
# allowPrivilegeEscalation: false

# Check consumer deployment security
helm template voting-test helm/ --show-only templates/consumer/deployment.yaml | grep -A 10 "securityContext:"

# Should show:
# runAsNonRoot: true
# runAsUser: 1000
# fsGroup: 1000
# allowPrivilegeEscalation: false
```

- [X] API runAsNonRoot: true
- [X] Consumer runAsNonRoot: true
- [X] Both drop all capabilities
- [X] allowPrivilegeEscalation: false

**4.4 Probes Validation**

```bash
# Check API probes
helm template voting-test helm/ --show-only templates/api/deployment.yaml | grep -A 5 "Probe:"

# Should show:
# livenessProbe: httpGet /health
# readinessProbe: httpGet /ready

# Check consumer probes
helm template voting-test helm/ --show-only templates/consumer/deployment.yaml | grep -A 8 "livenessProbe:"

# Should show:
# exec command: ps aux | grep python
```

- [X] API has liveness probe (HTTP /health)
- [X] API has readiness probe (HTTP /ready)
- [X] Consumer has liveness probe (exec ps check)
- [X] Probe timings configured

**4.5 Full Helm Lint**

```bash
# Lint entire chart
helm lint helm/

# Expected output:
# 1 chart(s) linted, 0 chart(s) failed
```

- [X] Helm lint passes with 0 failures
- [X] No errors or warnings (INFO messages OK)

---

### 5. API Functionality Validation (Requires Redis/PostgreSQL)

**Note:** These tests require Redis and PostgreSQL running. Can be done in Phase 5 integration testing.

**Setup: Start Required Services**

```bash
# Option 1: Using Docker (quick test)
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
docker run -d --name postgres-test -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=votes \
  postgres:15-alpine

# Wait for services to be ready
sleep 5

# Initialize PostgreSQL schema
docker exec -i postgres-test psql -U postgres -d votes <<'EOF'
CREATE TABLE IF NOT EXISTS votes (
    id SERIAL PRIMARY KEY,
    option VARCHAR(10) NOT NULL CHECK (option IN ('cats', 'dogs')),
    count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_votes_option ON votes(option);
INSERT INTO votes (option, count) VALUES ('cats', 0), ('dogs', 0) ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION increment_vote(vote_option VARCHAR(10))
RETURNS TABLE(option VARCHAR(10), new_count INTEGER) AS $$
BEGIN
    UPDATE votes SET count = count + 1, updated_at = NOW()
    WHERE votes.option = vote_option
    RETURNING votes.option, votes.count INTO option, new_count;
    RETURN NEXT;
END;
$$ LANGUAGE plpgsql;
EOF

# Start API with connections to test services
docker run -d --name api-test -p 8000:8000 \
  -e REDIS_URL="redis://host.docker.internal:6379" \
  -e DATABASE_URL="postgresql://postgres:postgres@host.docker.internal:5432/votes" \
  -e CORS_ORIGINS="http://localhost:3000" \
  api:0.3.2

# Wait for API startup
sleep 3

# Services are now running and ready for testing (sections 5.1-5.4)
```

**5.1 POST /api/vote Endpoint**

**Note:** Assumes services running from setup section above.

```bash
# Test vote endpoint
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "cats"}'

# Expected: HTTP 201 Created
# Response: {"status": "success", "option": "cats"}
```

- [ ] POST /api/vote accepts valid vote (cats)
- [ ] POST /api/vote accepts valid vote (dogs)
- [ ] POST /api/vote rejects invalid option (422)
- [ ] POST /api/vote writes to Redis Stream
- [ ] Structured logging for votes

**5.2 GET /api/results Endpoint**

```bash
# Test results endpoint
curl http://localhost:8000/api/results

# Expected: HTTP 200 OK
# Response: {
#   "cats": {"count": N, "percentage": X.XX},
#   "dogs": {"count": M, "percentage": Y.YY},
#   "total_votes": N+M,
#   "updated_at": "ISO timestamp"
# }
```

- [ ] GET /api/results returns vote counts
- [ ] Response includes percentages
- [ ] Response includes timestamps
- [ ] Cache-Control header present (max-age=2)
- [ ] Caching reduces database load

**5.3 CORS Validation**

```bash
# Test CORS preflight
curl -X OPTIONS http://localhost:8000/api/vote \
  -H "Origin: http://localhost:3000" \
  -H "Access-Control-Request-Method: POST" \
  -v

# Expected headers in response:
# access-control-allow-origin: http://localhost:3000
# access-control-allow-methods: GET, POST, OPTIONS
# access-control-allow-headers: Content-Type, Authorization, Accept
# access-control-max-age: 600
```

- [ ] CORS preflight succeeds for allowed origin
- [ ] CORS rejects untrusted origins
- [ ] Allowed methods: GET, POST, OPTIONS
- [ ] Allowed headers restricted (not *)
- [ ] Preflight cache: 600 seconds

**5.4 Request Size Limit**

```bash
# Test request size limit (>1MB should fail)
dd if=/dev/zero bs=1M count=2 | curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  --data-binary @- \
  -w "%{http_code}\n"

# Expected: 413 Payload Too Large
```

- [ ] Requests >1MB rejected with 413
- [ ] Request size limit configurable via MAX_REQUEST_SIZE

**Cleanup after Section 5 tests:**
```bash
# Stop and remove test containers
docker stop api-test redis-test postgres-test
docker rm api-test redis-test postgres-test
```

---

### 6. Consumer Functionality Validation (Requires Redis/PostgreSQL)

**Note:** These tests require Redis and PostgreSQL running. Can be done in Phase 5 integration testing.

**6.1 Consumer Group Creation**

```bash
# Check consumer creates consumer group
kubectl logs -n voting-consumer consumer-XXXXX | grep "consumer_group"

# Expected logs:
# {"event": "consumer_group_created", "stream": "votes", "group": "vote-processors"}
# OR
# {"event": "consumer_group_exists", "stream": "votes", "group": "vote-processors"}
```

- [ ] Consumer creates consumer group on startup
- [ ] Handles existing consumer group gracefully
- [ ] Uses XGROUP CREATE with MKSTREAM

**6.2 Message Processing**

```bash
# Post a vote via API
curl -X POST http://localhost:8000/api/vote -H "Content-Type: application/json" -d '{"option": "cats"}'

# Check consumer logs
kubectl logs -n voting-consumer consumer-XXXXX | grep "vote_processed"

# Expected:
# {"event": "processing_vote", "vote": "cats", "message_id": "..."}
# {"event": "vote_processed", "option": "cats", "new_count": N}
```

- [ ] Consumer reads messages from Redis Stream
- [ ] Parses vote field correctly
- [ ] Calls increment_vote() PostgreSQL function
- [ ] Logs processing events
- [ ] Acknowledges (XACK) messages after processing

**6.3 Error Handling**

```bash
# Test malformed message handling
# (Manual: inject malformed message into Redis Stream)

kubectl exec -n voting-data redis-0 -- redis-cli XADD votes '*' invalid_field 'bad_data'

# Check consumer logs
kubectl logs -n voting-consumer consumer-XXXXX | grep "malformed"

# Expected:
# {"event": "malformed_message_missing_vote", "message_id": "...", "level": "warning"}
```

- [ ] Malformed messages logged and skipped
- [ ] Invalid vote options rejected (not cats/dogs)
- [ ] Database errors retried 3 times
- [ ] Exponential backoff on retries

**6.4 Graceful Shutdown**

```bash
# Send SIGTERM to consumer
kubectl delete pod -n voting-consumer consumer-XXXXX

# Check logs before termination
kubectl logs -n voting-consumer consumer-XXXXX | tail -20

# Expected:
# {"event": "shutdown_signal_received", "signal": "SIGTERM"}
# {"event": "consumer_shutting_down"}
# {"event": "closing_redis_client"}
# {"event": "closing_postgres_pool"}
# {"event": "consumer_shutdown_complete"}
```

- [ ] SIGTERM signal handled gracefully
- [ ] Redis client closed cleanly
- [ ] PostgreSQL pool closed cleanly
- [ ] Shutdown logging present

---

### 7. Integration Test (End-to-End Flow)

**Note:** Requires full deployment (Phase 5)

**7.1 Complete Vote Flow**

```bash
# 1. Post vote via API
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "cats"}'

# 2. Check Redis Stream
kubectl exec -n voting-data redis-0 -- redis-cli XLEN votes
# Expected: 1 (or more)

# 3. Wait for consumer processing (2-5 seconds)
sleep 5

# 4. Check database
kubectl exec -n voting-data postgres-0 -- psql -U postgres -d votes -c \
  "SELECT * FROM votes WHERE option='cats';"
# Expected: count incremented

# 5. Check results endpoint
curl http://localhost:8000/api/results
# Expected: cats count matches database
```

- [ ] Vote posted via API (201 Created)
- [ ] Vote written to Redis Stream
- [ ] Consumer reads and processes vote
- [ ] Database vote count incremented
- [ ] Results endpoint reflects new count
- [ ] End-to-end latency <10 seconds

---

### 8. Documentation Validation

**8.1 Session Logs**

```bash
# Check Phase 2 session files
ls -l docs/sessions/ | grep "2025-11-16"

# Expected files (Phase 2 work):
# 2025-11-16-session-09-consumer-implementation.md
# (or similar session logs for consumer work)
```

- [ ] Session logs created for Phase 2 work
- [ ] Logs include what was implemented
- [ ] Logs include decisions made
- [ ] Next steps documented

**8.2 README Updates**

```bash
# Check README for Phase 2 status
grep "Phase 2" README.md

# Should mention:
# - FastAPI implementation complete
# - Consumer implementation complete
# - Current versions (api:0.3.2, consumer:0.3.0)
```

- [ ] README reflects Phase 2 completion
- [ ] Current versions documented
- [ ] Architecture updated if needed

**8.3 Todos Tracking**

```bash
# Check Phase 2 completion in todos.md
grep "## Phase 2:" -A 50 todos.md | grep "\[x\]" | wc -l

# Should show all Phase 2 tasks marked complete
```

- [ ] All Phase 2 tasks marked complete
- [ ] Consumer Dockerfile task complete
- [ ] Consumer implementation task complete
- [ ] Consumer deployment task complete

**8.4 Validation Document**

```bash
# Check this validation document exists
ls -l docs/PHASE2_VALIDATION.md

# Expected: This file
```

- [ ] PHASE2_VALIDATION.md created
- [ ] Follows PHASE1_VALIDATION.md format
- [ ] Comprehensive checklist

---

## Validation Summary

### Overall Results

**Pre-Flight:** ___ / 3 checks passed
**API Container:** ___ / 5 checks passed
**Consumer Container:** ___ / 5 checks passed
**Helm Chart:** ___ / 5 checks passed
**API Functionality:** ___ / 5 checks passed (requires integration)
**Consumer Functionality:** ___ / 4 checks passed (requires integration)
**Integration Test:** ___ / 1 check passed (Phase 5)
**Documentation:** ___ / 4 checks passed

**TOTAL:** ___ / 32 sections passed

### Issues Found

| # | Section | Issue Description | Severity | Action Required |
|---|---------|-------------------|----------|-----------------|
| - | - | - | - | - |

### Recommendations

- [ ] All checks passed - Ready for Phase 3 or Phase 5
- [ ] Minor issues - Can proceed (note issues)
- [ ] Major issues - Fix before proceeding

**Assessment:** ___________

### Sign-off

**Validated by:** ___________
**Date:** 2025-11-16
**Status:** [ ] PASS [ ] PASS WITH NOTES [ ] FAIL

**Notes:**
-
-
-

---

## Reference

**Project Directory:** `/Users/juan.catalan/Documents/Procastination/Demo_project`

**Key Components:**
- FastAPI: `api/` (version 0.3.2)
- Consumer: `consumer/` (version 0.3.0)
- Helm chart: `helm/`
- Documentation: `docs/`

**Next Steps:**
- If validation passes, can proceed to:
  - **Phase 3:** Frontend implementation
  - **Phase 5:** Integration testing (recommended)
