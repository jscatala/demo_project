# Voting Website - Project Tasks (Cats vs Dogs)

## Architecture Decisions
- **Deployment:** Helm-based, Kubernetes from day 0 (provider-agnostic)
- **Vote Options:** Cats vs Dogs (hardcoded, two options)
- **Redis Pattern:** Redis Streams (event log with consumer groups)
- **Live Updates:** Server-Sent Events (optional, nice-to-have)
- **Security:** Built-in from start, input validation, rate limiting, prepared statements
- **Containers:** Multistage Dockerfiles, non-root, minimal base images
- **User Model:** Each connection = new user (no auth, DDOS handled externally)

---

## Phase 0: Project Documentation (Completed ✓)
- [x] Create README.md with project overview
- [x] Create CONTRIBUTING.md with Conventional Commits and workflow
- [x] Create CHANGELOG.md with Semantic Versioning
- [x] Create ADR template
- [x] Document ADR-0001: Kubernetes-native deployment
- [x] Document ADR-0002: Redis Streams event pattern
- [x] Document ADR-0003: Cats vs Dogs voting scope
- [x] Create CONVENTIONS.md with code standards
- [x] Create .gitignore for Python/TypeScript/K8s
- [x] Create HANDOFF_GUIDE.md for AI assistant workflow
- [x] Create session logging structure (docs/sessions/)
- [x] Complete Session 01 log
- [x] Create ADR-0004: Layer-based namespace security architecture
- [x] Create issues tracking system (docs/issues/)
- [x] Document Issue-0001: Namespace security isolation problem

## Phase 1: K8s Foundation (Critical Priority)

**Note:** Tasks reorganized by execution order after atomization analysis. Priority 1 tasks are infrastructure-only, Priority 2 creates minimal app stubs, Priority 3 connects them.

### Priority 1: Namespace Infrastructure ✓
- [x] Define 4 namespace manifests
  - [x] Create `helm/templates/namespaces/voting-frontend.yaml` with metadata
  - [x] Create `helm/templates/namespaces/voting-api.yaml` with metadata
  - [x] Create `helm/templates/namespaces/voting-consumer.yaml` with metadata
  - [x] Create `helm/templates/namespaces/voting-data.yaml` with metadata
  - [x] Add standard K8s labels (app.kubernetes.io/name, component, managed-by)
  - [x] Test: `kubectl apply -f helm/templates/namespaces/` succeeds
  - [x] Verify: `kubectl get ns | grep voting` shows exactly 4 namespaces

### Priority 2: Minimal Application Stubs ✓
- [x] Create minimal application stubs (enables Deployment testing)
  - [x] Create `frontend/` with Dockerfile + React hello-world app
  - [x] Create `api/` with Dockerfile + FastAPI hello-world app
  - [x] Create `consumer/` with Dockerfile + Python hello-world script
  - [x] Build all 3 images locally with tags `frontend:0.1.0`, `api:0.1.0`, `consumer:0.1.0`
  - [x] Test: Run each container locally, verify hello-world response

### Priority 3: Kubernetes Resources ✓
- [x] Define frontend Deployment
  - [x] Create `helm/templates/frontend/deployment.yaml` with pod template
  - [x] Set replicas: 1, image: `frontend:0.1.0`, resources (128Mi/100m)
  - [x] Add liveness/readiness probes (httpGet: /health on port 8080 for non-root)
  - [x] Add environment variable `API_URL` placeholder
  - [x] Add labels matching voting-frontend namespace
  - [x] Validate: `kubectl apply --dry-run=client -f deployment.yaml`

- [x] Define API Deployment
  - [x] Create `helm/templates/api/deployment.yaml` with pod template
  - [x] Set replicas: 1, image: `api:0.1.0`, resources (256Mi/200m)
  - [x] Add liveness/readiness probes (httpGet: /health, /ready on port 8000)
  - [x] Add environment variables: `REDIS_URL`, `DATABASE_URL` (placeholders)
  - [x] Add securityContext: `runAsNonRoot: true`, `runAsUser: 1000`
  - [x] Add labels matching voting-api namespace
  - [x] Validate: `kubectl apply --dry-run=client -f deployment.yaml`

- [x] Create Helm chart foundation
  - [x] Create `helm/Chart.yaml` with apiVersion: v2, name: voting-app, version: 0.1.0
  - [x] Create `helm/values.yaml` with image registry/tags for all services
  - [x] Create `helm/templates/_helpers.tpl` with common label templates
  - [x] Create `helm/templates/NOTES.txt` with installation success message
  - [x] Run `helm lint helm/` - must pass with 0 errors
  - [x] Run `helm template voting-test helm/` - must render without errors

### Priority 4: Remaining Infrastructure ✓
- [x] Define K8s Job (consumer for event processing)
- [x] Define StatefulSets (PostgreSQL, Redis) or external service configs
- [x] Create Gateway API resources (Gateway, HTTPRoute) with rate limiting (ADR-0005)
- [x] Setup ConfigMaps and Secrets structure
- [x] Design PostgreSQL schema (votes table: id, option, count, timestamp)
- [x] Configure Redis Streams for event log

## Phase 2: Backend Core (High Priority)

**Critical Decision:** Consumer should be Deployment (continuous), not Job (batch) - Redis Streams require long-running process

- [ ] FastAPI production Dockerfile with Python 3.13-slim multistage build
  - [ ] Resolve base image: Use Python 3.13-slim (Alpine vs Debian - recommend slim for glibc compatibility)
  - [ ] Create api/requirements.txt with pinned versions (FastAPI, uvicorn, redis, asyncpg, pydantic)
  - [ ] Write Dockerfile stage 1: Builder (install deps, create wheels)
  - [ ] Write Dockerfile stage 2: Runtime (copy wheels, minimal runtime deps, UID 1000)
  - [ ] Add api/.dockerignore (exclude __pycache__, *.pyc, tests/, .git/)
  - [ ] Build image locally: `docker build -t api:0.2.0 api/`
  - [ ] Verify image size < 200MB: `docker images api:0.2.0`
  - [ ] Verify runs as non-root: `docker run --rm api:0.2.0 id` shows UID 1000
  - [ ] Test container starts: `docker run -p 8000:8000 api:0.2.0` responds on /health
  - [ ] Update helm/values.yaml: api.image.tag: "0.2.0"

- [ ] POST /api/vote endpoint with Redis Stream integration
  - [ ] Define Pydantic model: `VoteRequest(option: Literal["cats", "dogs"])`
  - [ ] Create Redis client singleton with connection pool (redis.asyncio)
  - [ ] Implement POST /vote route handler with input validation
  - [ ] Add XADD call to write vote to "votes" stream with fields: {vote, timestamp, request_id}
  - [ ] Define error responses: 400 for invalid option, 503 for Redis unavailable
  - [ ] Add structured logging (vote received, vote written, errors)
  - [ ] Write unit test: valid vote "cats" returns 201
  - [ ] Write unit test: invalid vote "birds" returns 400
  - [ ] Write unit test: Redis connection failure returns 503
  - [ ] Manual test: POST http://localhost:8000/vote with curl, verify XLEN increments

- [ ] GET /api/results endpoint with PostgreSQL integration
  - [ ] Add asyncpg dependency to api/requirements.txt
  - [ ] Create PostgreSQL connection pool singleton (asyncpg.create_pool)
  - [ ] Define Pydantic response model: `VoteResults(cats: int, dogs: int, total: int, cats_pct: float, dogs_pct: float)`
  - [ ] Implement GET /results route handler calling `get_vote_results()` function
  - [ ] Add error handling: 503 if DB unavailable, 500 on query failure
  - [ ] Add response caching with 2-second TTL (simple dict cache with timestamp)
  - [ ] Write unit test: mock DB returns counts, verify JSON structure
  - [ ] Write unit test: empty database returns zeros
  - [ ] Write integration test: Insert test votes, verify /results accuracy
  - [ ] Manual test: GET http://localhost:8000/results, verify response <100ms

- [ ] FastAPI security configuration (CORS, headers, request limits)
  - [ ] Add fastapi-cors middleware with origin from env var (default: http://localhost:3000)
  - [ ] Create security headers middleware (CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff)
  - [ ] Add request body size limit middleware (1MB max via LimitUploadSize)
  - [ ] Configure HSTS header (Strict-Transport-Security) for HTTPS enforcement
  - [ ] Add X-Forwarded-For trusted proxy configuration
  - [ ] Write test: Verify security headers in response
  - [ ] Write test: CORS preflight request succeeds for allowed origin
  - [ ] Write test: CORS rejects untrusted origin
  - [ ] Write test: Request body >1MB rejected with 413
  - [ ] Document security config in README: CORS_ORIGINS env var

- [ ] Python consumer Dockerfile with Python 3.13-slim multistage build
  - [ ] Create consumer/requirements.txt (redis, asyncpg, structlog)
  - [ ] Write consumer/Dockerfile stage 1: Builder (pip install dependencies)
  - [ ] Write consumer/Dockerfile stage 2: Runtime (Python 3.13-slim, UID 1000, copy code)
  - [ ] Add consumer/.dockerignore
  - [ ] Build image: `docker build -t consumer:0.2.0 consumer/`
  - [ ] Verify image size <180MB
  - [ ] Verify runs as UID 1000: `docker run --rm consumer:0.2.0 id`
  - [ ] Test container executes consumer script: `docker run consumer:0.2.0`
  - [ ] Update helm/values.yaml: consumer.image.tag: "0.2.0"

- [ ] Consumer: Redis Stream processor with PostgreSQL aggregation
  - [ ] Create consumer/consumer.py with Redis connection setup (redis.asyncio)
  - [ ] Create PostgreSQL connection pool (asyncpg)
  - [ ] Implement consumer group join: XGROUP CREATE with MKSTREAM if not exists
  - [ ] Implement XREADGROUP loop: read "votes" stream, batch size 10, block 5s
  - [ ] Parse message: extract vote field, validate "cats" or "dogs"
  - [ ] Call PostgreSQL `increment_vote(option)` for each valid message
  - [ ] XACK message after successful DB write
  - [ ] Add error handling: log malformed messages, retry DB failures 3x
  - [ ] Add SIGTERM signal handler for graceful shutdown
  - [ ] Add structured logging (message received, DB updated, errors)
  - [ ] Write unit test: Mock Redis, verify increment_vote called
  - [ ] Write unit test: Malformed message logged and skipped
  - [ ] Write integration test: Post vote via API, verify consumer increments DB

- [ ] Consumer: K8s Deployment (changed from Job - continuous processing required)
  - [ ] Create helm/templates/consumer/deployment.yaml
  - [ ] Set namespace: voting-consumer
  - [ ] Configure image: consumer:{{ .Values.consumer.image.tag }}
  - [ ] Set restartPolicy: Always (continuous processing)
  - [ ] Add env vars: DATABASE_URL, REDIS_URL from secrets
  - [ ] Set resources: requests (256Mi/200m), limits (512Mi/500m)
  - [ ] Set replicas: 1 (single consumer for consumer group)
  - [ ] Add securityContext: runAsNonRoot, runAsUser: 1000
  - [ ] Add liveness probe: TCP socket check (no HTTP endpoint for batch process)
  - [ ] Validate: kubectl apply --dry-run=client -f deployment.yaml
  - [ ] Update helm/values.yaml with consumer config

## Phase 3: Frontend (High Priority)
- [ ] TypeScript app multistage Dockerfile (nginx serving static files)
- [ ] Voting buttons UI (Cats vs Dogs, side-by-side)
- [ ] Results display component (percentages, counts, top half)
- [ ] API integration (fetch for voting/results)
- [ ] Optional: Server-Sent Events for live updates

## Phase 4: Security & Hardening (High Priority)
- [ ] Non-root containers for all services
- [ ] Input validation on all API endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] Container image scanning
- [ ] Network policies between services

## Phase 5: Integration (Medium Priority)
- [ ] Helm install on local K8s (minikube/kind)
- [ ] Test flow: Vote → Redis Stream → Consumer Job → PostgreSQL
- [ ] Verify results endpoint accuracy
- [ ] Test SSE live updates (if implemented)
- [ ] Load testing with multiple concurrent votes

## Phase 6: Documentation (Low Priority)
- [ ] Architecture diagram (K8s resources, event flow)
- [ ] Local deployment guide (helm install)
- [ ] Production readiness checklist

---

**Project Structure:**
```
Demo_project/
├── helm/                    # Helm chart (K8s manifests)
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
├── frontend/               # TypeScript voting UI
├── api/                    # FastAPI service
├── consumer/              # Python event consumer (K8s Job)
└── infrastructure/        # Shared configs
```
