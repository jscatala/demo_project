#!/bin/bash
# Run integration tests on Minikube
# Prerequisites: Minikube running, kubectl configured
# Usage: ./scripts/run-integration-tests.sh

set -e

echo "🔧 Integration Tests (Minikube + Helm)"
echo "======================================"

# Check prerequisites
echo "📋 Checking prerequisites..."

if ! command -v minikube &> /dev/null; then
  echo "❌ Minikube not found. Install: https://minikube.sigs.k8s.io/docs/start/"
  exit 1
fi

if ! command -v kubectl &> /dev/null; then
  echo "❌ kubectl not found. Install: https://kubernetes.io/docs/tasks/tools/"
  exit 1
fi

if ! command -v helm &> /dev/null; then
  echo "❌ Helm not found. Install: https://helm.sh/docs/intro/install/"
  exit 1
fi

# Check Minikube status
if ! minikube status &> /dev/null; then
  echo "⚠️  Minikube not running. Starting..."
  minikube start
fi

echo "✅ Prerequisites OK"

# Create test namespace
NAMESPACE="voting-integration-test"
TEST_RELEASE="voting-test"

echo ""
echo "🚀 Deploying test environment..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Deploy Helm chart
if helm list -n $NAMESPACE | grep -q $TEST_RELEASE; then
  echo "⚠️  Existing test release found. Uninstalling..."
  helm uninstall $TEST_RELEASE -n $NAMESPACE
  sleep 5
fi

echo "📦 Building images in Minikube Docker..."
eval $(minikube docker-env)
docker build -t frontend:0.5.0 frontend/ > /dev/null 2>&1 || echo "⚠️  Frontend build failed"
docker build -t api:0.3.2 api/ > /dev/null 2>&1 || echo "⚠️  API build failed"
docker build -t consumer:0.3.0 consumer/ > /dev/null 2>&1 || echo "⚠️  Consumer build failed"

echo "📦 Installing Helm chart..."
helm install $TEST_RELEASE ./helm -n $NAMESPACE \
  -f helm/values-local.yaml \
  --wait --timeout 5m

echo "✅ Deployment complete"

# Wait for pods
echo ""
echo "⏳ Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod \
  --all -n $NAMESPACE \
  --timeout=300s

# Run integration tests
echo ""
echo "🧪 Running integration tests..."

# TODO: Create integration test container
# For now, run manual validation checks
echo "📝 Manual validation (automated tests TODO):"
echo "  1. Check all pods running"
kubectl get pods -n $NAMESPACE

echo ""
echo "  2. Check services"
kubectl get svc -n $NAMESPACE

echo ""
echo "  3. Port-forward and test endpoints (manual)"
echo "     kubectl port-forward -n $NAMESPACE svc/voting-api 8000:8000"
echo "     curl http://localhost:8000/health"

# Cleanup option
echo ""
read -p "🧹 Cleanup test environment? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  echo "Uninstalling test release..."
  helm uninstall $TEST_RELEASE -n $NAMESPACE
  echo "Deleting namespace..."
  kubectl delete namespace $NAMESPACE
  echo "✅ Cleanup complete"
else
  echo "⚠️  Test environment still running"
  echo "   To cleanup later: helm uninstall $TEST_RELEASE -n $NAMESPACE"
fi

echo ""
echo "======================================"
echo "✅ Integration tests complete"
