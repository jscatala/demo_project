# Voting Website: Cats vs Dogs

![Version](https://img.shields.io/badge/version-0.1.0--dev-blue)
![License](https://img.shields.io/badge/license-MIT-green)

Event-driven voting application deployed on Kubernetes with real-time results.

## Overview

A microservices-based voting platform where users vote between two options (Cats vs Dogs). Votes are processed through an event-driven architecture using Redis Streams, with results stored in PostgreSQL and displayed in real-time.

## Tech Stack

- **Frontend:** TypeScript, Nginx
- **API:** FastAPI (Python)
- **Event Consumer:** Python (K8s Job)
- **Data Store:** PostgreSQL
- **Event Stream:** Redis Streams
- **Deployment:** Kubernetes, Helm
- **Containerization:** Docker (multistage builds)

## Architecture

```
User → Frontend → API → Redis Streams → Consumer Job → PostgreSQL
                    ↓                                      ↑
                  POST /vote                          GET /results
```

**Event Flow:**
1. User votes via frontend
2. API validates and writes to Redis Stream
3. K8s Job consumes events, aggregates votes
4. Results stored in PostgreSQL
5. Frontend displays current counts/percentages

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

## Documentation

- [Architecture Decision Records](docs/adr/) - Key architectural decisions
- [Issues & Solutions](docs/issues/) - Problems encountered and how we solved them
- [Conventions](docs/CONVENTIONS.md) - Code standards and security practices
- [Session Logs](docs/sessions/) - Development session history
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
