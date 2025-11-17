#!/bin/bash
# Run all unit tests (Docker-based)
# Usage: ./scripts/run-unit-tests.sh [component]
# Example: ./scripts/run-unit-tests.sh frontend

set -e

COMPONENT=${1:-all}
FAILED=0

echo "🧪 Running Unit Tests (Docker)"
echo "=============================="

run_frontend_tests() {
  echo ""
  echo "📦 Frontend Tests..."
  docker build -f frontend/Dockerfile.test -t frontend-test:latest frontend/ > /dev/null 2>&1
  if docker run --rm frontend-test:latest npm test -- --run; then
    echo "✅ Frontend tests passed"
  else
    echo "❌ Frontend tests failed"
    FAILED=$((FAILED + 1))
  fi
}

run_api_tests() {
  echo ""
  echo "📦 API Tests..."
  if [ ! -f "api/Dockerfile.test" ]; then
    echo "⚠️  API Dockerfile.test not found - skipping"
    return
  fi
  docker build -f api/Dockerfile.test -t api-test:latest api/ > /dev/null 2>&1
  if docker run --rm api-test:latest pytest tests/unit/ -v; then
    echo "✅ API tests passed"
  else
    echo "❌ API tests failed"
    FAILED=$((FAILED + 1))
  fi
}

run_consumer_tests() {
  echo ""
  echo "📦 Consumer Tests..."
  if [ ! -f "consumer/Dockerfile.test" ]; then
    echo "⚠️  Consumer Dockerfile.test not found - skipping"
    return
  fi
  docker build -f consumer/Dockerfile.test -t consumer-test:latest consumer/ > /dev/null 2>&1
  if docker run --rm consumer-test:latest pytest tests/unit/ -v; then
    echo "✅ Consumer tests passed"
  else
    echo "❌ Consumer tests failed"
    FAILED=$((FAILED + 1))
  fi
}

# Run tests based on component argument
case $COMPONENT in
  frontend)
    run_frontend_tests
    ;;
  api)
    run_api_tests
    ;;
  consumer)
    run_consumer_tests
    ;;
  all)
    run_frontend_tests
    run_api_tests
    run_consumer_tests
    ;;
  *)
    echo "Unknown component: $COMPONENT"
    echo "Usage: $0 [frontend|api|consumer|all]"
    exit 1
    ;;
esac

echo ""
echo "=============================="
if [ $FAILED -eq 0 ]; then
  echo "✅ All tests passed!"
  exit 0
else
  echo "❌ $FAILED test suite(s) failed"
  exit 1
fi
