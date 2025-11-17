# Contributing Guide

## Conventional Commits

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation only
- **style:** Code style changes (formatting, no logic change)
- **refactor:** Code refactoring (no feature/fix)
- **perf:** Performance improvements
- **test:** Adding/updating tests
- **build:** Build system changes (Docker, Helm, dependencies)
- **ci:** CI/CD configuration changes
- **chore:** Other changes (maintenance, tooling)

### Examples

```bash
feat(api): add vote validation for cats/dogs options
fix(consumer): prevent duplicate vote processing
docs(adr): add decision record for Redis Streams choice
build(helm): update ingress rate limiting config
```

### Breaking Changes

Append `!` after type or add `BREAKING CHANGE:` in footer:

```bash
feat(api)!: change vote endpoint from POST to PUT

BREAKING CHANGE: Vote endpoint now requires PUT instead of POST
```

## Branch Naming

- `feature/short-description` - New features
- `bugfix/short-description` - Bug fixes
- `hotfix/short-description` - Critical production fixes
- `docs/short-description` - Documentation updates

**Examples:**
- `feature/sse-live-updates`
- `bugfix/redis-connection-leak`
- `docs/update-deployment-guide`

## Development Workflow (TDD Required)

**Test-Driven Development (TDD) is mandatory for all new features.**

### 1. Create Branch
```bash
git checkout -b feature/your-feature
```

### 2. Write Tests First (🔴 Red)
**Before writing implementation code:**

**Unit Tests (Docker):**
```bash
# Frontend: Create component test
touch frontend/src/components/YourComponent.test.tsx

# API: Create endpoint test
touch api/tests/test_your_endpoint.py

# Consumer: Create processor test
touch consumer/tests/test_your_processor.py
```

**Integration Tests (Minikube):**
```bash
# Create integration test for multi-component flows
touch tests/integration/test_vote_flow.py
```

### 3. Run Tests - Verify Failure
**Unit tests:**
```bash
# Frontend
docker build -f frontend/Dockerfile.test -t frontend-test .
docker run --rm frontend-test:latest npm test -- --run

# API
docker build -f api/Dockerfile.test -t api-test .
docker run --rm api-test:latest pytest tests/

# Consumer
docker build -f consumer/Dockerfile.test -t consumer-test .
docker run --rm consumer-test:latest pytest tests/
```

**Integration tests:**
```bash
# Deploy to Minikube
helm install voting-test ./helm -f helm/values-test.yaml

# Run integration tests
kubectl run integration-tests --image=voting-integration-tests:latest \
  --restart=Never --rm -it
```

### 4. Implement Code (🟢 Green)
**Write minimal code to make tests pass:**
- Follow conventions in [CONVENTIONS.md](docs/CONVENTIONS.md)
- Keep functions atomic (single responsibility)
- Implement only what's needed for tests

### 5. Refactor (🔵 Refactor)
**Improve code while keeping tests passing:**
- Optimize performance
- Improve readability
- Extract reusable functions
- Update documentation

### 6. Verify All Tests Pass
**Before committing:**
```bash
# Run all unit tests
./scripts/run-unit-tests.sh  # Docker-based

# Run integration tests (if multi-component changes)
./scripts/run-integration-tests.sh  # Minikube + Helm

# Verify non-root container security
./scripts/verify-nonroot.sh  # Docker + Trivy scan
```

### 7. Commit Using Conventional Commits
```bash
git commit -m "feat(frontend): add live results via SSE

- Add SSE connection hook
- Create EventSource client
- Update results on vote events
- Tests: 15 unit, 3 integration (all passing)"
```

### 8. Push and Create PR
```bash
git push origin feature/your-feature
```

### 9. PR Requirements
- ✅ Descriptive title (conventional commit format)
- ✅ Description of changes
- ✅ **Tests written BEFORE implementation (TDD)**
- ✅ All tests passing (unit + integration)
- ✅ Coverage thresholds met
- ✅ No security vulnerabilities
- ✅ **Non-root container verification passed** (`./scripts/verify-nonroot.sh`)
- ✅ Code review approval

## Testing Strategy

### When to Use Docker Tests (Unit)
- **Single component** functionality
- **Fast execution** required (<5s)
- **No external dependencies** (or mocked)
- Examples: Component rendering, API validation, utility functions

### When to Use Minikube Tests (Integration)
- **Multi-component** interactions
- **Real dependencies** needed (Redis, PostgreSQL, etc.)
- **End-to-end flows**
- Examples: Vote submission flow, event processing, database updates

### Test Coverage Requirements
**Minimum thresholds (enforced in CI):**
- Components: 95% (statements, functions, lines, branches)
- API endpoints: 90%
- Consumer processors: 90%
- Utilities: 100%

**Integration tests:**
- Critical user flows: 100%
- Error scenarios: 100%
- Edge cases: 80%

## Pull Request Process

1. Update CHANGELOG.md under "Unreleased" section
2. Update documentation if needed
3. Ensure all tests pass
4. Obtain at least one approval
5. Squash and merge with conventional commit message

## Security Validation

### Pre-Deployment Checklist

Before deploying changes that modify Docker images or Kubernetes manifests:

```bash
# 1. Verify all containers run as non-root
./scripts/verify-nonroot.sh

# Expected output:
# ✓ frontend:0.5.0: Non-root user configured (UID: 1000)
# ✓ api:0.3.2: Non-root user configured (UID: 65532)
# ✓ consumer:0.3.0: Non-root user configured (UID: 1000)
# ✓ All images verified as non-root
```

**The script validates:**
- Docker image USER configuration (UID ≠ 0)
- Trivy security scan (no HIGH/CRITICAL misconfigurations)
- All 3 service images (frontend, api, consumer)

**If script fails:**
1. Check Dockerfile USER directive
2. Review Trivy scan output for specific issues
3. Fix security issues before proceeding
4. Re-run verification

### CI/CD Integration (Future)

Add to GitHub Actions workflow:

```yaml
- name: Verify Non-Root Containers
  run: ./scripts/verify-nonroot.sh
```

## Code Review Guidelines

**Reviewers should check:**
- Code follows conventions (CONVENTIONS.md)
- Security best practices applied
- Tests cover new functionality
- Documentation updated
- No hardcoded secrets
- Docker images are minimal and non-root
- `./scripts/verify-nonroot.sh` passes for image changes

## Questions?

Open an issue or discussion for clarification.
