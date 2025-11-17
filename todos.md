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

- [x] FastAPI production Dockerfile with distroless + uv (completed 2025-11-15)
  - [x] Replaced pip with uv package manager (5-10x faster)
  - [x] Switched to Google distroless Python 3.11 base image
  - [x] Create api/requirements.txt with pinned versions (FastAPI, uvicorn, redis, asyncpg, pydantic)
  - [x] Write Dockerfile stage 1: Builder (Python 3.11-slim + uv, install deps)
  - [x] Write Dockerfile stage 2: Runtime (distroless, minimal deps, UID 65532)
  - [x] Add api/.dockerignore (exclude __pycache__, *.pyc, tests/, .git/)
  - [x] Build image locally: `docker build -t api:0.2.1 api/`
  - [x] Verify image size: 166MB (39% reduction from 274MB)
  - [x] Verify runs as non-root: distroless runs as UID 65532 by default
  - [x] Test container starts: `docker run -p 8000:8000 api:0.2.1` responds on /health
  - [x] Update helm/values.yaml: api.image.tag: "0.2.1"
  - [x] Fix HEAD method support on /health and /ready endpoints

- [x] POST /api/vote endpoint with Redis Stream integration (completed 2025-11-15)
  - [x] Define Pydantic model: `VoteRequest(option: Literal["cats", "dogs"])`
  - [x] Create Redis client singleton with connection pool (redis.asyncio)
  - [x] Implement POST /vote route handler with input validation
  - [x] Add XADD call to write vote to "votes" stream with fields: {vote, timestamp, request_id}
  - [x] Define error responses: 422 for invalid option, 503 for Redis unavailable
  - [x] Add structured logging (vote received, vote written, errors)
  - [x] Write unit test: valid vote "cats" returns 201
  - [x] Write unit test: invalid vote "birds" returns 422 (Pydantic validation)
  - [x] Write unit test: Redis connection failure returns 503
  - [x] Manual test: POST http://localhost:8000/api/vote with curl, verify XLEN increments
  - [x] Created modular architecture: models.py, redis_client.py, routes/, services/
  - [x] Added 6 unit tests with mocked Redis client
  - [x] Updated Dockerfile to copy all application files
  - [x] Added async-timeout dependency
  - [x] Built and tested Docker image: api:0.3.0
  - [x] Updated helm/values.yaml: api.tag: "0.3.0"

- [x] GET /api/results endpoint with PostgreSQL integration (completed 2025-11-15)
  - [x] asyncpg dependency already in api/requirements.txt (0.30.0)
  - [x] Create PostgreSQL connection pool singleton (asyncpg.create_pool)
  - [x] Define Pydantic response models: `VoteOption`, `VoteResults` with validations
  - [x] Implement GET /results route handler calling `get_vote_results()` function
  - [x] Add error handling: 503 if DB unavailable, 500 on query failure
  - [x] Add response caching with 2-second TTL (simple dict cache with timestamp)
  - [x] Write unit test: mock DB returns counts, verify JSON structure
  - [x] Write unit test: empty database returns zeros
  - [x] Write unit test: database unavailable returns 503
  - [x] Write unit test: Cache-Control header verification
  - [x] Write unit test: caching behavior
  - [x] Manual test: GET http://localhost:8000/api/results, response time 55ms (<100ms ✓)
  - [x] Created db_client.py with connection pooling (min=2, max=10)
  - [x] Created services/results_service.py with caching logic
  - [x] Created routes/results.py with GET handler
  - [x] Extended models.py with VoteOption and VoteResults
  - [x] Updated main.py with DB lifecycle and results router
  - [x] Updated Dockerfile to include db_client.py
  - [x] Built and tested Docker image: api:0.3.1
  - [x] Updated helm/values.yaml: api.tag: "0.3.1"
  - [x] Manual validation: zero votes, actual votes (66.67% / 33.33%), caching

- [x] FastAPI security configuration (CORS, headers, request limits) (completed 2025-11-15)
  - [x] CORS middleware already configured with CORS_ORIGINS env var (enhanced)
  - [x] Create security headers middleware (CSP, X-Frame-Options: DENY, X-Content-Type-Options: nosniff)
  - [x] Add request body size limit middleware (1MB max, configurable via MAX_REQUEST_SIZE)
  - [x] Configure HSTS header (Strict-Transport-Security) for HTTPS enforcement (production only)
  - [x] Skipped X-Forwarded-For trusted proxy (handled by Kubernetes/Ingress)
  - [x] Write test: Verify security headers in response
  - [x] Write test: CORS preflight request succeeds for allowed origin
  - [x] Write test: CORS rejects untrusted origin
  - [x] Write test: Request body >1MB rejected with 413
  - [x] Document security config in README: CORS_ORIGINS, MAX_REQUEST_SIZE, ENVIRONMENT
  - [x] Created middleware/security.py with SecurityHeadersMiddleware and RequestSizeLimitMiddleware
  - [x] Enhanced CORS: restricted headers (Content-Type, Authorization, Accept), max_age=600
  - [x] Added 13 security tests in tests/test_security.py
  - [x] Created comprehensive api/README.md with security documentation
  - [x] Updated main.py with middleware (correct order)
  - [x] Built and tested Docker image: api:0.3.2
  - [x] Updated helm/values.yaml: api.tag: "0.3.2"
  - [x] Manual validation: security headers verified, CORS working, endpoints functional

- [x] Python consumer Dockerfile with Python 3.13-slim multistage build
  - [x] Create consumer/requirements.txt (redis, asyncpg, structlog)
  - [x] Write consumer/Dockerfile stage 1: Builder (pip install dependencies)
  - [x] Write consumer/Dockerfile stage 2: Runtime (Python 3.13-slim, UID 1000, copy code)
  - [x] Add consumer/.dockerignore
  - [x] Build image: `docker build -t consumer:0.2.0 consumer/`
  - [x] Verify image size: 223MB (acceptable for Python 3.13 + async deps)
  - [x] Verify runs as UID 1000: `docker run --rm consumer:0.2.0 id`
  - [x] Test container executes consumer script: `docker run consumer:0.2.0`
  - [x] Update helm/values.yaml: consumer.image.tag: "0.2.0"

- [x] Consumer: Redis Stream processor with PostgreSQL aggregation (completed 2025-11-16)
  - [x] Created modular architecture: config.py, logger.py, redis_client.py, db_client.py, main.py
  - [x] Redis connection with consumer group support (XGROUP CREATE with MKSTREAM)
  - [x] PostgreSQL connection pool (asyncpg, min=2, max=10)
  - [x] XREADGROUP loop implementation (batch size 10, block 5000ms)
  - [x] Message parsing and validation ("cats" or "dogs" only)
  - [x] Call PostgreSQL increment_vote() function for valid messages
  - [x] XACK message after successful processing or if malformed
  - [x] Error handling: log malformed messages, retry DB failures 3x with exponential backoff
  - [x] SIGTERM/SIGINT signal handlers for graceful shutdown
  - [x] Structured logging with structlog (JSON output, ISO timestamps)
  - [x] Environment-based configuration (12-factor app pattern)
  - [x] Built and tested Docker image: consumer:0.3.0 (223MB, UID 1000)
  - [x] Updated helm/values.yaml: consumer.tag: "0.3.0"
  - [x] Import validation passed

- [x] Consumer: K8s Deployment (completed 2025-11-16)
  - [x] Created helm/templates/consumer/deployment.yaml
  - [x] Set namespace: voting-consumer
  - [x] Configured image: consumer:{{ .Values.images.consumer.tag }} (0.3.0)
  - [x] Set restartPolicy: Always (continuous processing)
  - [x] Added 9 environment variables: REDIS_URL, DATABASE_URL, STREAM_NAME, CONSUMER_GROUP, CONSUMER_NAME, BATCH_SIZE, BLOCK_MS, MAX_RETRIES, LOG_LEVEL
  - [x] Set resources: requests (256Mi/200m), limits (512Mi/500m)
  - [x] Set replicas: 1 (single consumer for consumer group)
  - [x] Added securityContext: runAsNonRoot: true, runAsUser: 1000, fsGroup: 1000
  - [x] Added liveness probe: exec command (ps aux check for python process)
  - [x] Validated: kubectl apply --dry-run=client (passed)
  - [x] Updated helm/values.yaml with consumer config (replicas, streamName, consumerGroup, batchSize, blockMs, maxRetries, logLevel)
  - [x] Helm lint: 0 errors
  - [x] Helm template: renders successfully

## Phase 3: Frontend (High Priority)

**Decisions Made:**
1. ✅ API URL: K8s ConfigMap + runtime config.js (mounted as volume, frontend fetches before init)
2. ✅ Build tool: Vite (modern, fast)
3. ✅ Dev workflow: Minikube only (production-like, no docker-compose)

**Note:** Configuration server (Consul, Spring Cloud Config) documented in tech-to-review.md as future improvement

- [x] TypeScript app multistage Dockerfile (nginx serving static files) - Completed 2025-11-17
  - [x] Create frontend/package.json with React 18, TypeScript, Vite dependencies
  - [x] Create frontend/tsconfig.json with strict mode, ES2020 target, React JSX
  - [x] Create frontend/.dockerignore excluding node_modules, dist, .git
  - [x] Create frontend/nginx.conf with SPA routing (try_files), gzip compression, security headers
  - [x] Write Dockerfile stage 1: Builder (node:20-alpine, install deps, run vite build)
  - [x] Write Dockerfile stage 2: Runtime (nginx:1.25-alpine, copy dist/, expose 8080, non-root)
  - [x] Create frontend/vite.config.ts with build optimizations (minify, chunk size limits)
  - [x] Test build locally: `docker build -t frontend:0.2.0 frontend/` ✓ Built in 922ms
  - [x] Test runtime: Container serves index.html on port 8080 ✓
  - [x] Verify image size: 75.6MB (acceptable, includes React bundle)
  - [x] Verify non-root: UID 1000 (appuser) ✓
  - [x] Verify SPA routing: /vote returns 200 OK (not 404) ✓
- [x] Voting buttons UI (Cats vs Dogs, side-by-side) - Completed 2025-11-17
  - [x] Create `frontend/src/components/VoteButtons.tsx` with TypeScript interface
  - [x] Define props type: `{ onVote: (option: 'cats' | 'dogs') => void, disabled?: boolean }`
  - [x] Implement two button elements with onClick handlers calling onVote
  - [x] Add CSS module `VoteButtons.module.css` with side-by-side flexbox layout
  - [x] Add responsive breakpoint (@media max-width: 768px) for vertical stacking
  - [x] Implement disabled state styling (opacity 0.5, cursor not-allowed)
  - [x] Add hover/focus styles (scale transform, border highlight)
  - [x] Add ARIA attributes (aria-label, role="button" if not using <button>)
  - [x] Implement keyboard navigation (Tab focus, Enter/Space triggers vote)
  - [x] Add loading state prop to disable buttons during API call
  - [x] Create basic component test (renders, click calls onVote, disabled prevents click)
  - [x] Manual test: buttons render, responsive works, keyboard accessible
  - [x] Integrated into App.tsx with state management
  - [x] Built and tested Docker image: frontend:0.3.0 (bundle 140KB gzip)
  - [x] Updated helm/values.yaml: frontend.tag: "0.3.0"
  - [x] Added CSS module type definitions (vite-env.d.ts)
  - [x] Verified security headers and non-root execution (UID 1000)
- [x] Results display component (percentages, counts, top half) - Completed 2025-11-17
  - [x] Create `frontend/src/components/VoteResults.tsx` with TypeScript interface
  - [x] Define `VoteResultsProps` type: `{ data?: VoteData, loading?: boolean, error?: string }`
  - [x] Define `VoteData` interface: `{ cats: number, dogs: number }` with percentage calculation logic
  - [x] Implement component structure: container, title, two result items (cats/dogs)
  - [x] Add percentage calculation function: `(count, total) => ((count / total) * 100).toFixed(1)`
  - [x] Render progress bars with dynamic width based on percentage
  - [x] Display vote counts with thousand separators (e.g., "1,234 votes")
  - [x] Display total votes sum at bottom
  - [x] Create `VoteResults.module.css` with progress bar styling and animations
  - [x] Implement loading state: skeleton placeholder or spinner
  - [x] Implement error state: error message display
  - [x] Implement empty state: handle zero total votes (show 0% for both)
  - [x] Add ARIA live region for dynamic updates (aria-live="polite")
  - [x] Add CSS transition for progress bar width changes (0.5s ease)
  - [x] Create component tests: renders data, calculates percentages, shows states
  - [x] Integrate into App.tsx above VoteButtons
  - [x] Manual test: verify calculations, state transitions, responsive layout
  - [x] Built and tested Docker image: frontend:0.4.0 (bundle 6.88KB gzip)
  - [x] Updated helm/values.yaml: frontend.tag: "0.4.0"
- [x] API integration (fetch for voting/results) - Completed 2025-11-17
  - [x] Create `frontend/src/services/api.ts` with base URL configuration from `window.APP_CONFIG?.API_URL`
  - [x] Define TypeScript interfaces: `VoteRequest`, `VoteResponse`, `ResultsResponse` in `types/api.ts`
  - [x] Implement `postVote(option: VoteOption): Promise<VoteResponse>` function with error handling
  - [x] Implement `getResults(): Promise<ResultsResponse>` function with error handling
  - [x] Add generic error handler: map HTTP status codes to user messages (404, 500, 503, network errors)
  - [x] Create custom hook `useVote()` returning `{ vote, isLoading, error }` for VoteButtons
  - [x] Create custom hook `useResults()` returning `{ data, isLoading, error, refetch }` for VoteResults
  - [x] Update App.tsx: integrated useVote and useResults hooks
  - [x] Results auto-fetch on component mount via useResults
  - [x] Add POST /vote success handler: refetch results after successful vote
  - [x] Add error display in App.tsx with error-message styling
  - [x] Error handling: network failures, HTTP status codes, API_URL undefined
  - [x] Loading states: VoteButtons and VoteResults display loading skeletons
  - [x] Vote confirmation message shows after successful submission
  - [x] "Vote Again" button clears errors and allows re-voting
  - [x] Built and tested Docker image: frontend:0.5.0 (9.05KB gzip bundle)
  - [x] Updated helm/values.yaml: frontend.tag: "0.5.0"
- [~] Server-Sent Events for live updates (Deferred - see Future Improvements)

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

## Future Improvements

**See:** `docs/tech-to-review.md` for detailed analysis of each improvement

### Real-time & Performance
- **Server-Sent Events (SSE):** Real-time vote updates without polling
  - Backend: FastAPI SSE endpoint streaming from Redis
  - Frontend: EventSource client with auto-reconnect
  - Trade-off: Complexity vs better UX
  - Status: Deferred post-Phase 3

### Configuration Management
- **Configuration Server:** Centralized config with hot reload
  - Options: Consul, Spring Cloud Config, etcd, custom service
  - Benefits: No pod restarts for config changes, versioning, audit trail
  - Trade-off: Additional infrastructure vs better DX
  - Status: Revisit at 5+ microservices

### Observability
- **Distributed Tracing:** OpenTelemetry + Jaeger/Tempo
- **Metrics:** Prometheus + Grafana dashboards
- **Centralized Logging:** ELK/Loki stack
- **Service Mesh:** Istio/Linkerd for advanced traffic management

### Security Enhancements
- **mTLS:** Service-to-service encryption
- **OPA/Kyverno:** Policy enforcement
- **Secrets Management:** HashiCorp Vault or External Secrets Operator
- **Image Signing:** Cosign + admission controller

### Testing
- **Contract Testing:** Pact for API contracts
- **Chaos Engineering:** Chaos Mesh for resilience testing
- **Performance Testing:** k6 or Locust for load testing

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
