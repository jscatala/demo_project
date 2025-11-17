# Voting Website: Cats vs Dogs

![Version](https://img.shields.io/badge/version-0.5.0--dev-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Phase](https://img.shields.io/badge/phase-3%20in%20progress-yellow)

Event-driven voting application deployed on Kubernetes with real-time results.

## Overview

A microservices-based voting platform where users vote between two options (Cats vs Dogs). Votes are processed through an event-driven architecture using Redis Streams, with results stored in PostgreSQL and displayed in real-time.

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, Nginx v0.4.0 - Phase 3 ⏳
- **API:** FastAPI v0.3.2 (Python) - Phase 2 ✓
- **Event Consumer:** Python v0.3.0 (K8s Deployment) - Phase 2 ✓
- **Data Store:** PostgreSQL 15
- **Event Stream:** Redis Streams 7
- **Deployment:** Kubernetes, Helm
- **Containerization:** Docker (multistage builds, distroless, non-root)

## Architecture

```
User → Frontend → API → Redis Streams → Consumer Deployment → PostgreSQL
                    ↓                                             ↑
                  POST /vote                                 GET /results
```

**Event Flow:**
1. User votes via frontend
2. API validates and writes to Redis Stream (XADD)
3. Consumer Deployment reads via consumer group (XREADGROUP)
4. Consumer aggregates votes in PostgreSQL (increment_vote function)
5. API serves results with 2-second caching
6. Frontend displays current counts/percentages

## Quick Start

### Prerequisites
- Kubernetes cluster (minikube/kind for local)
- Helm 3+
- kubectl

### Installation

```bash
# Install with Helm
helm install voting-app ./helm

# Port forward to access locally
kubectl port-forward svc/frontend 8080:80

# Visit http://localhost:8080
```

### Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Conventional Commits specification
- Branch naming conventions
- Development workflow

## Project Status

**Current Version:** 0.5.0-dev

**Completed Phases:**
- ✅ **Phase 0:** Project documentation and architecture
- ✅ **Phase 1:** Kubernetes infrastructure (namespaces, deployments, StatefulSets, Ingress)
- ✅ **Phase 2:** Backend core (FastAPI + Consumer implementation)

**In Progress:**
- ⏳ **Phase 3:** Frontend implementation
  - ✅ VoteButtons component (accessibility, responsive)
  - ✅ VoteResults component (progress bars, live updates)
  - ✅ API integration (custom hooks, error handling, refetch)
  - ⬜ Optional: Server-Sent Events for real-time updates

**Component Versions:**
- API: v0.3.2 (FastAPI, security hardened, Redis + PostgreSQL)
- Consumer: v0.3.0 (Redis Streams processor, asyncpg)
- Frontend: v0.5.0 (React 18, TypeScript, custom hooks, API integration)

## Documentation

- [Architecture Decision Records](docs/adr/) - Key architectural decisions
- [Issues & Solutions](docs/issues/) - Problems encountered and how we solved them
- [Conventions](docs/CONVENTIONS.md) - Code standards and security practices
- [Session Logs](docs/sessions/) - Development session history
- [Phase 1 Validation](docs/PHASE1_VALIDATION.md) - Infrastructure validation protocol
- [Phase 2 Validation](docs/PHASE2_VALIDATION.md) - Backend validation protocol
- [Changelog](CHANGELOG.md) - Version history

## Resuming Work

**For developers using AI assistants:**

See [Handoff Guide](docs/HANDOFF_GUIDE.md) for how to efficiently resume work.

**Quick start:**
```
Last session: @docs/sessions/[latest-session].md
Current todos: @todos.md
```

## Versioning

This project follows [Semantic Versioning](https://semver.org/):
- **MAJOR:** Incompatible API changes
- **MINOR:** Backwards-compatible functionality
- **PATCH:** Backwards-compatible bug fixes

## License

MIT
