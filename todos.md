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
- [x] Create Ingress with rate limiting annotations
- [x] Setup ConfigMaps and Secrets structure
- [x] Design PostgreSQL schema (votes table: id, option, count, timestamp)
- [x] Configure Redis Streams for event log

## Phase 2: Backend Core (High Priority)
- [ ] FastAPI multistage Dockerfile (distroless/alpine base)
- [ ] POST /vote endpoint → writes to Redis Stream (validate input: cats/dogs only)
- [ ] GET /results endpoint → reads from PostgreSQL (prepared statements)
- [ ] Security: Helmet headers, CORS, request size limits
- [ ] Python consumer multistage Dockerfile
- [ ] Consumer: Read Redis Stream → aggregate → PostgreSQL (prepared statements)
- [ ] Consumer: K8s Job definition with restart policy

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
