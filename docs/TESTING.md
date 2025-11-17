# Testing Guide

**TDD is mandatory for all new features.**

## Quick Reference

### Test-First Development Flow

```bash
# 1. Create test file
touch frontend/src/components/NewFeature.test.tsx

# 2. Write failing test
# (Edit test file)

# 3. Run tests - verify RED
./scripts/run-unit-tests.sh frontend

# 4. Implement minimal code
# (Edit component)

# 5. Run tests - verify GREEN
./scripts/run-unit-tests.sh frontend

# 6. Refactor while keeping GREEN
# (Improve code)

# 7. Commit with tests
git add . && git commit -m "feat: add new feature"
```

## Testing Tiers

### Tier 1: Unit Tests (Docker)
**When:** Single component, fast feedback needed
**Environment:** Docker container
**Speed:** <5 seconds

**Run all unit tests:**
```bash
./scripts/run-unit-tests.sh
```

**Run specific component:**
```bash
./scripts/run-unit-tests.sh frontend
./scripts/run-unit-tests.sh api
./scripts/run-unit-tests.sh consumer
```

**Manual (development):**
```bash
# Frontend
docker run --rm frontend-test:latest npm test

# API (once Dockerfile.test exists)
docker run --rm api-test:latest pytest tests/unit/

# Consumer (once Dockerfile.test exists)
docker run --rm consumer-test:latest pytest tests/unit/
```

### Tier 2: Integration Tests (Minikube)
**When:** Multi-component flows, real dependencies
**Environment:** Minikube cluster with Helm
**Speed:** 30s - 2min

**Run integration tests:**
```bash
./scripts/run-integration-tests.sh
```

**Manual setup:**
```bash
# Start Minikube
minikube start

# Deploy test stack
helm install voting-test ./helm -n voting-integration-test \
  --create-namespace \
  --wait --timeout 5m

# Run tests (TODO: Create integration test image)
kubectl run integration-tests --image=voting-integration-tests:latest \
  -n voting-integration-test --restart=Never --rm -it

# Cleanup
helm uninstall voting-test -n voting-integration-test
kubectl delete namespace voting-integration-test
```

## Coverage Requirements

### Enforced Thresholds

**Components (Frontend):**
- Statements: 95%
- Functions: 95%
- Lines: 95%
- Branches: 95%

**API Endpoints:**
- Statements: 90%
- Functions: 90%
- Lines: 90%
- Branches: 85%

**Consumer Processors:**
- Statements: 90%
- Functions: 90%
- Lines: 90%
- Branches: 85%

**Utilities:**
- All metrics: 100%

### View Coverage

**Frontend:**
```bash
docker run --rm frontend-test:latest npm run test:coverage -- --run
# HTML report in frontend/coverage/index.html
```

**API (once implemented):**
```bash
docker run --rm api-test:latest pytest --cov=api --cov-report=html tests/unit/
# HTML report in api/htmlcov/index.html
```

## TDD Examples

### Frontend Component (React + TypeScript)

**1. Write Test First (RED):**
```typescript
// VoteButton.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import VoteButton from './VoteButton';

describe('VoteButton', () => {
  it('calls onClick with option when clicked', () => {
    const handleClick = vi.fn();
    render(<VoteButton option="cats" onClick={handleClick} />);

    fireEvent.click(screen.getByRole('button'));

    expect(handleClick).toHaveBeenCalledWith('cats');
  });
});
```

**2. Implement Minimal Code (GREEN):**
```typescript
// VoteButton.tsx
interface VoteButtonProps {
  option: string;
  onClick: (option: string) => void;
}

export default function VoteButton({ option, onClick }: VoteButtonProps) {
  return (
    <button onClick={() => onClick(option)}>
      Vote {option}
    </button>
  );
}
```

**3. Refactor:**
```typescript
// VoteButton.tsx - Improved
export default function VoteButton({ option, onClick }: VoteButtonProps) {
  return (
    <button
      onClick={() => onClick(option)}
      aria-label={`Vote for ${option}`}
      className={styles.voteButton}
    >
      {option === 'cats' ? '🐱' : '🐶'} Vote {option}
    </button>
  );
}
```

### API Endpoint (FastAPI + Python)

**1. Write Test First (RED):**
```python
# tests/unit/test_vote.py
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_vote_endpoint_accepts_cats():
    response = client.post("/api/vote", json={"option": "cats"})
    assert response.status_code == 201
    assert response.json()["vote"] == "cats"

def test_vote_endpoint_rejects_invalid_option():
    response = client.post("/api/vote", json={"option": "birds"})
    assert response.status_code == 422
```

**2. Implement Minimal Code (GREEN):**
```python
# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, validator

app = FastAPI()

class VoteRequest(BaseModel):
    option: str

    @validator('option')
    def validate_option(cls, v):
        if v not in ['cats', 'dogs']:
            raise ValueError('Invalid option')
        return v

@app.post("/api/vote", status_code=201)
async def vote(request: VoteRequest):
    return {"status": "accepted", "vote": request.option}
```

**3. Refactor:**
```python
# routes/vote.py
from services.vote_service import write_vote_to_stream

@app.post("/api/vote", status_code=201)
async def vote(request: VoteRequest):
    event_id = await write_vote_to_stream(request.option)
    return {
        "status": "accepted",
        "vote": request.option,
        "event_id": event_id
    }
```

## Validation Phase Checklist

**Before marking a phase complete:**

- [ ] All unit tests written BEFORE implementation (TDD)
- [ ] All unit tests passing (Docker)
- [ ] Coverage thresholds met
- [ ] Integration tests passing (Minikube) - if multi-component
- [ ] Validation protocol executed (PHASE*_VALIDATION.md)
- [ ] Session log documented
- [ ] Code committed with test results in commit message

## Common Issues

### "Tests pass locally but fail in Docker"
**Cause:** Environment differences (Node.js version, dependencies)
**Solution:** Always test in Docker before commit
```bash
./scripts/run-unit-tests.sh
```

### "Integration tests timeout"
**Cause:** Pods not ready, insufficient resources
**Solution:** Increase Minikube resources, check pod logs
```bash
minikube config set memory 8192
minikube config set cpus 4
minikube delete && minikube start
```

### "Coverage below threshold"
**Cause:** Missing tests for edge cases
**Solution:** Check coverage report, add tests
```bash
docker run --rm frontend-test:latest npm run test:coverage -- --run
# Review coverage/index.html for uncovered lines
```

## Best Practices

### ✅ DO

- **Write test first** - See it fail (RED)
- **Minimal implementation** - Make it pass (GREEN)
- **Refactor with confidence** - Tests protect you
- **Test edge cases** - Null, empty, invalid inputs
- **Use real dependencies** - For integration tests
- **Fast tests** - Unit tests should run in <5s
- **Descriptive test names** - `test_vote_endpoint_rejects_invalid_option`

### ❌ DON'T

- **Implementation first** - That's not TDD
- **Skip tests** - Even for "simple" code
- **Only happy paths** - Test failures too
- **Mock everything** - Integration tests need real services
- **Large test files** - Split by feature/component
- **Flaky tests** - Fix or remove, never ignore

## Resources

- **TDD Workflow:** [CONVENTIONS.md](CONVENTIONS.md#test-driven-development-tdd)
- **Development Guide:** [CONTRIBUTING.md](../CONTRIBUTING.md#development-workflow-tdd-required)
- **Validation Protocols:** `docs/PHASE*_VALIDATION.md`

## Scripts

**Unit tests:**
```bash
./scripts/run-unit-tests.sh [frontend|api|consumer|all]
```

**Integration tests:**
```bash
./scripts/run-integration-tests.sh
```

**Coverage only:**
```bash
docker run --rm frontend-test:latest npm run test:coverage -- --run
docker run --rm api-test:latest pytest --cov=api tests/unit/  # TODO
docker run --rm consumer-test:latest pytest --cov=consumer tests/unit/  # TODO
```
