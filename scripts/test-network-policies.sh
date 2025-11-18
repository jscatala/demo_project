#!/bin/bash
# Network Policy Connectivity Validation Script
# Tests allowed and denied connections between pods

set -e

PROFILE="${MINIKUBE_PROFILE:-demo-project--dev}"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔒 Network Policy Connectivity Validation"
echo "=========================================="
echo "Profile: $PROFILE"
echo ""

# Helper functions
test_connection() {
    local from_ns=$1
    local from_pod=$2
    local to_host=$3
    local to_port=$4
    local should_succeed=$5
    local description=$6

    echo -n "Testing: $description... "

    if kubectl exec -n "$from_ns" "$from_pod" -- timeout 3 nc -zv "$to_host" "$to_port" >/dev/null 2>&1; then
        if [ "$should_succeed" = "true" ]; then
            echo -e "${GREEN}✓ PASS${NC} (connection allowed as expected)"
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (connection should be blocked)"
            return 1
        fi
    else
        if [ "$should_succeed" = "false" ]; then
            echo -e "${GREEN}✓ PASS${NC} (connection blocked as expected)"
            return 0
        else
            echo -e "${RED}✗ FAIL${NC} (connection should be allowed)"
            return 1
        fi
    fi
}

# Get pod names
echo "📋 Finding pods..."
FRONTEND_POD=$(kubectl get pods -n voting-frontend -l app.kubernetes.io/component=frontend -o jsonpath='{.items[0].metadata.name}')
API_POD=$(kubectl get pods -n voting-api -l app.kubernetes.io/component=api -o jsonpath='{.items[0].metadata.name}')
CONSUMER_POD=$(kubectl get pods -n voting-consumer -l app.kubernetes.io/component=consumer -o jsonpath='{.items[0].metadata.name}' | head -1)
REDIS_POD=$(kubectl get pods -n voting-data -l app.kubernetes.io/component=cache -o jsonpath='{.items[0].metadata.name}')
POSTGRES_POD=$(kubectl get pods -n voting-data -l app.kubernetes.io/component=database -o jsonpath='{.items[0].metadata.name}')

echo "Frontend: $FRONTEND_POD"
echo "API: $API_POD"
echo "Consumer: $CONSUMER_POD"
echo "Redis: $REDIS_POD"
echo "Postgres: $POSTGRES_POD"
echo ""

FAILED=0

echo "🧪 Testing Allowed Connections"
echo "==============================="

# API → Redis (should succeed)
test_connection "voting-api" "$API_POD" "redis.voting-data.svc.cluster.local" "6379" "true" "API → Redis:6379" || ((FAILED++))

# API → PostgreSQL (should succeed)
test_connection "voting-api" "$API_POD" "postgres.voting-data.svc.cluster.local" "5432" "true" "API → PostgreSQL:5432" || ((FAILED++))

# Consumer → Redis (should succeed)
test_connection "voting-consumer" "$CONSUMER_POD" "redis.voting-data.svc.cluster.local" "6379" "true" "Consumer → Redis:6379" || ((FAILED++))

# Consumer → PostgreSQL (should succeed)
test_connection "voting-consumer" "$CONSUMER_POD" "postgres.voting-data.svc.cluster.local" "5432" "true" "Consumer → PostgreSQL:5432" || ((FAILED++))

# All → DNS (should succeed)
test_connection "voting-api" "$API_POD" "kube-dns.kube-system.svc.cluster.local" "53" "true" "API → DNS:53" || ((FAILED++))
test_connection "voting-consumer" "$CONSUMER_POD" "kube-dns.kube-system.svc.cluster.local" "53" "true" "Consumer → DNS:53" || ((FAILED++))

echo ""
echo "🚫 Testing Denied Connections"
echo "=============================="

# Frontend → Redis (should fail - not in allow list)
test_connection "voting-frontend" "$FRONTEND_POD" "redis.voting-data.svc.cluster.local" "6379" "false" "Frontend → Redis:6379 (should be blocked)" || ((FAILED++))

# Frontend → PostgreSQL (should fail - not in allow list)
test_connection "voting-frontend" "$FRONTEND_POD" "postgres.voting-data.svc.cluster.local" "5432" "false" "Frontend → PostgreSQL:5432 (should be blocked)" || ((FAILED++))

# Consumer → API (should fail - consumer doesn't need API access)
test_connection "voting-consumer" "$CONSUMER_POD" "api.voting-api.svc.cluster.local" "8000" "false" "Consumer → API:8000 (should be blocked)" || ((FAILED++))

echo ""
echo "📊 Test Summary"
echo "==============="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    echo "Network policies are correctly configured."
    exit 0
else
    echo -e "${RED}✗ $FAILED test(s) failed${NC}"
    echo "Network policies may need adjustment."
    exit 1
fi
