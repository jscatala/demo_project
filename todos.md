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
- [ ] Create Helm chart structure (Chart.yaml, values.yaml, templates/)
- [ ] Define K8s Deployments (frontend, api)
- [ ] Define K8s Job (consumer for event processing)
- [ ] Define StatefulSets (PostgreSQL, Redis) or external service configs
- [ ] Create Ingress with rate limiting annotations
- [ ] Setup ConfigMaps and Secrets structure
- [ ] Design PostgreSQL schema (votes table: id, option, count, timestamp)
- [ ] Configure Redis Streams for event log

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
