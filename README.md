# Voting Website: Cats vs Dogs

![Version](https://img.shields.io/badge/version-0.5.0-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Phase](https://img.shields.io/badge/phase-5.3_complete-green)

Event-driven voting application deployed on Kubernetes with real-time results.

## Overview

A microservices-based voting platform where users vote between two options (Cats vs Dogs). Votes are processed through an event-driven architecture using Redis Streams, with results stored in PostgreSQL and displayed in real-time.

## Tech Stack

- **Frontend:** React 18, TypeScript, Vite, Nginx v0.5.0 - Phase 3 ✓
- **API:** FastAPI v0.3.2 (Python) - Phase 2 ✓
- **Event Consumer:** Python v0.3.1 (K8s Deployment) - Phase 2 ✓
- **Data Store:** PostgreSQL 15
- **Event Stream:** Redis Streams 7
- **Deployment:** Kubernetes, Helm
- **Containerization:** Docker (multistage builds, distroless, non-root)

## UI Preview

**[View Interactive Mockup](frontend/mockup.html)** - Open in browser to see the voting interface

**Features:**
- Side-by-side voting buttons (Cats vs Dogs)
- Real-time results with progress bars
- Responsive design (mobile stacks vertically)
- Full accessibility (ARIA, keyboard navigation)

> **Note:** The mockup is a fully interactive HTML page demonstrating the UI without backend dependencies

## Architecture

### Kubernetes Infrastructure

```mermaid
graph TB
    subgraph "voting-frontend namespace"
        FE[Frontend Deployment<br/>v0.5.0 nginx:1.25-alpine<br/>UID 1000]
        FE_SVC[Frontend Service<br/>ClusterIP]
    end

    subgraph "voting-api namespace"
        API[API Deployment<br/>FastAPI v0.3.2<br/>distroless UID 65532]
        API_SVC[API Service<br/>ClusterIP]
    end

    subgraph "voting-consumer namespace"
        CONSUMER[Consumer Deployment<br/>Python v0.3.1<br/>UID 1000]
    end

    subgraph "voting-data namespace"
        REDIS[Redis StatefulSet<br/>Streams enabled]
        REDIS_SVC[Redis Service<br/>ClusterIP]
        PG[PostgreSQL StatefulSet<br/>votes table]
        PG_SVC[PostgreSQL Service<br/>ClusterIP]
    end

    GATEWAY[Gateway API<br/>Rate Limiting]
    USER[User Browser]

    USER -->|HTTPS| GATEWAY
    GATEWAY -->|HTTP| FE_SVC
    FE_SVC --> FE
    FE -->|POST /api/vote<br/>GET /api/results| API_SVC
    API_SVC --> API
    API -->|XADD| REDIS_SVC
    REDIS_SVC --> REDIS
    API -->|SELECT| PG_SVC
    PG_SVC --> PG
    CONSUMER -->|XREADGROUP| REDIS_SVC
    CONSUMER -->|INSERT/UPDATE| PG_SVC

    classDef frontend fill:#667eea,color:#fff
    classDef api fill:#764ba2,color:#fff
    classDef consumer fill:#f093fb,color:#fff
    classDef data fill:#4facfe,color:#fff
    classDef gateway fill:#43e97b,color:#fff

    class FE,FE_SVC frontend
    class API,API_SVC api
    class CONSUMER consumer
    class REDIS,REDIS_SVC,PG,PG_SVC data
    class GATEWAY gateway
```

### Event Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant API
    participant Redis
    participant Consumer
    participant PostgreSQL

    User->>Frontend: Click vote (cats/dogs)
    Frontend->>API: POST /api/vote {option: "cats"}
    API->>API: Validate input
    API->>Redis: XADD votes {vote, timestamp, id}
    Redis-->>API: Message ID
    API-->>Frontend: 201 Created
    Frontend->>Frontend: Show confirmation
    Frontend->>API: GET /api/results

    Note over Consumer,Redis: Consumer runs continuously
    Consumer->>Redis: XREADGROUP votes-group
    Redis-->>Consumer: Batch of messages
    Consumer->>Consumer: Validate & process
    Consumer->>PostgreSQL: Call increment_vote(option)
    PostgreSQL-->>Consumer: Success
    Consumer->>Redis: XACK message

    API->>PostgreSQL: SELECT cats, dogs FROM votes
    PostgreSQL-->>API: {cats: 151, dogs: 100}
    API->>API: Calculate percentages
    API-->>Frontend: {cats: 151, dogs: 100}
    Frontend->>Frontend: Update progress bars
```

### Network Policy Topology

**Phase 4.5:** 12 NetworkPolicy resources implementing zero-trust security (Calico CNI v3.27.0)

```mermaid
graph LR
    subgraph "voting-frontend namespace"
        FE_POD[Frontend Pod<br/>v0.5.0]
    end

    subgraph "voting-api namespace"
        API_POD[API Pod<br/>v0.3.2]
    end

    subgraph "voting-consumer namespace"
        CONSUMER_POD[Consumer Pod<br/>v0.3.1]
    end

    subgraph "voting-data namespace"
        REDIS_POD[Redis Pod]
        PG_POD[PostgreSQL Pod]
    end

    subgraph "kube-system namespace"
        DNS[CoreDNS<br/>port 53]
    end

    FE_POD -->|❌ DENIED| REDIS_POD
    FE_POD -->|❌ DENIED| PG_POD
    FE_POD -->|✅ ALLOW| API_POD
    FE_POD -.->|✅ DNS| DNS

    API_POD -->|✅ ALLOW| REDIS_POD
    API_POD -->|✅ ALLOW| PG_POD
    API_POD -.->|✅ DNS| DNS

    CONSUMER_POD -->|✅ ALLOW| REDIS_POD
    CONSUMER_POD -->|✅ ALLOW| PG_POD
    CONSUMER_POD -->|❌ DENIED| API_POD
    CONSUMER_POD -.->|✅ DNS| DNS

    classDef allowed fill:#10b981,stroke:#059669,color:#fff
    classDef denied fill:#ef4444,stroke:#dc2626,color:#fff
    classDef dns fill:#3b82f6,stroke:#2563eb,color:#fff,stroke-dasharray: 5 5

    class API_POD,CONSUMER_POD,FE_POD allowed
    class REDIS_POD,PG_POD allowed
```

**Policy Summary:**
- **4 default-deny policies:** Block all ingress by default (one per voting namespace)
- **4 DNS egress policies:** Allow DNS lookups (CoreDNS port 53 TCP/UDP)
- **4 service-specific policies:** Frontend→API, API→Data, Consumer→Data

### Security Boundaries

```mermaid
graph TB
    subgraph "Security Layers"
        subgraph "Presentation Layer"
            FE[Frontend<br/>nginx:1.25-alpine<br/>UID 1000 non-root<br/>Read-only filesystem]
        end

        subgraph "Application Layer"
            API[API<br/>FastAPI distroless<br/>UID 65532 non-root<br/>Drop all capabilities]
        end

        subgraph "Processing Layer"
            CONSUMER[Consumer<br/>Python 3.13-slim<br/>UID 1000 non-root<br/>Read-only filesystem]
        end

        subgraph "Data Layer"
            REDIS[Redis StatefulSet<br/>Persistent volumes<br/>AOF enabled]
            PG[PostgreSQL StatefulSet<br/>Persistent volumes<br/>Encrypted at rest]
        end
    end

    subgraph "Network Policies"
        NP1[Default Deny All<br/>voting-frontend]
        NP2[Default Deny All<br/>voting-api]
        NP3[Default Deny All<br/>voting-consumer]
        NP4[Default Deny All<br/>voting-data]
    end

    subgraph "Observability - Phase 5.3"
        METRICS[metrics-server<br/>kubectl top<br/>CPU/Memory monitoring]
    end

    FE ---|Network Policy| NP1
    API ---|Network Policy| NP2
    CONSUMER ---|Network Policy| NP3
    REDIS ---|Network Policy| NP4
    PG ---|Network Policy| NP4

    API -.->|Metrics| METRICS
    CONSUMER -.->|Metrics| METRICS
    FE -.->|Metrics| METRICS

    classDef secure fill:#10b981,stroke:#059669,color:#fff
    classDef policy fill:#ef4444,stroke:#dc2626,color:#fff
    classDef obs fill:#f59e0b,stroke:#d97706,color:#fff

    class FE,API,CONSUMER,REDIS,PG secure
    class NP1,NP2,NP3,NP4 policy
    class METRICS obs
```

**Security Features:**
1. **Non-root execution:** All containers run as unprivileged users (UIDs: 1000, 65532)
2. **Network isolation:** 12 NetworkPolicy resources enforcing zero-trust
3. **Container hardening:** Distroless images, dropped capabilities, read-only filesystems
4. **Input validation:** Pydantic models, SQL parameterization, request size limits
5. **Vulnerability scanning:** Trivy scans (0 HIGH/CRITICAL in consumer, 7 in API, 18 in frontend)

**Key Design Decisions:**
1. **4-namespace isolation:** Security boundaries between layers (ADR-0004)
2. **Redis Streams:** Event log with consumer groups (ADR-0002)
3. **Non-root containers:** All services run as unprivileged users
4. **Gateway API:** Rate limiting and ingress (ADR-0005)
5. **Consumer as Deployment:** Continuous processing, not batch Job

## Quick Start

### Prerequisites
- Kubernetes cluster (minikube/kind for local)
- Helm 3+
- kubectl

### Installation

**Quick Start (Minikube):**
```bash
# Automated deployment script
./scripts/deploy-local.sh --rebuild

# Or manual steps:
# 1. Start Minikube
minikube start --cpus=4 --memory=8192

# 2. Build images in Minikube
eval $(minikube docker-env)
docker build -t frontend:0.5.0 frontend/
docker build -t api:0.3.2 api/
docker build -t consumer:0.3.1 consumer/

# 3. Deploy with Helm
helm install voting-app ./helm -f helm/values-local.yaml

# 4. Access application
kubectl port-forward -n voting-frontend svc/frontend 8080:80
# Visit http://localhost:8080
```

**See [DEPLOYMENT.md](docs/DEPLOYMENT.md) for complete guide.**

### Development

**TDD Required:** Test-Driven Development is mandatory for all new features.

See documentation:
- [CONTRIBUTING.md](CONTRIBUTING.md) - Conventional Commits, TDD workflow
- [TESTING.md](docs/TESTING.md) - Testing guide, coverage requirements
- [CONVENTIONS.md](docs/CONVENTIONS.md) - Code standards, atomic principles

**Run tests:**
```bash
# Unit tests (Docker)
./scripts/run-unit-tests.sh [frontend|api|consumer|all]

# Integration tests (Minikube + Helm)
./scripts/run-integration-tests.sh
```

## Project Status

**Current Version:** 0.5.0

**Completed Phases:**
- ✅ **Phase 0:** Project documentation and architecture
- ✅ **Phase 1:** Kubernetes infrastructure (namespaces, deployments, StatefulSets, Ingress)
- ✅ **Phase 2:** Backend core (FastAPI + Consumer implementation)
- ✅ **Phase 3:** Frontend implementation (VoteButtons, VoteResults, API integration)
- ✅ **Phase 3.5:** Testing & Validation (Vitest, 100% component coverage, TDD established)
- ✅ **Phase 4:** Security & Hardening (14/14 tasks complete - network policies, container scanning, input validation, SQL injection prevention)
- ✅ **Phase 5.1-5.3:** Integration testing (Helm deployment to minikube, end-to-end vote flow verification, load testing baseline established)

**Next Phases:**
- **Phase 5.4:** SSE live updates
- **Phase 6:** Documentation and production readiness

**Component Versions:**
- API: v0.3.2 (FastAPI, security hardened, Redis + PostgreSQL)
- Consumer: v0.3.1 (Redis Streams processor, asyncpg, fixed field name handling)
- Frontend: v0.5.0 (React 18, TypeScript, custom hooks, API integration)

## Documentation

**Development:**
- [CONTRIBUTING.md](CONTRIBUTING.md) - TDD workflow, conventional commits, PR process
- [TESTING.md](docs/TESTING.md) - Testing guide, TDD examples, coverage requirements
- [CONVENTIONS.md](docs/CONVENTIONS.md) - Code standards, atomic principles, security practices
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Minikube setup, Helm deployment, troubleshooting

**Architecture:**
- [Architecture Decision Records](docs/adr/) - Key architectural decisions (5 ADRs)
- [Issues & Solutions](docs/issues/) - Problems encountered and solutions

**Validation:**
- [Phase 1 Validation](docs/PHASE1_VALIDATION.md) - Infrastructure validation protocol
- [Phase 2 Validation](docs/PHASE2_VALIDATION.md) - Backend validation protocol
- [Phase 3 Validation](docs/PHASE3_VALIDATION.md) - Frontend validation protocol
- [Phase 4 Validation](docs/PHASE4_VALIDATION.md) - Security validation checklist
- [Phase 5 Validation](docs/PHASE5_VALIDATION.md) - Integration testing & load testing validation

**History:**
- [Session Logs](docs/sessions/) - Development session history (13 sessions)
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
