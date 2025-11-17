#!/bin/bash
# Deploy voting app to local Minikube cluster
# Usage: ./scripts/deploy-local.sh [--rebuild]

set -e

REBUILD=${1:-}
NAMESPACE_PREFIX="voting"
RELEASE_NAME="voting-app"

echo "🚀 Deploying Voting App to Minikube"
echo "===================================="

# Check prerequisites
echo ""
echo "📋 Checking prerequisites..."

if ! command -v minikube &> /dev/null; then
  echo "❌ Minikube not found. Install: https://minikube.sigs.k8s.io/docs/start/"
  exit 1
fi

if ! command -v helm &> /dev/null; then
  echo "❌ Helm not found. Install: https://helm.sh/docs/intro/install/"
  exit 1
fi

# Check Minikube status
if ! minikube status &> /dev/null; then
  echo "⚠️  Minikube not running. Starting..."
  minikube start --cpus=4 --memory=8192 --driver=docker
else
  echo "✅ Minikube running"
fi

# Build images if requested
if [ "$REBUILD" = "--rebuild" ]; then
  echo ""
  echo "🔨 Building Docker images..."
  echo "Using Minikube Docker environment"

  # Use Minikube's Docker daemon
  eval $(minikube docker-env)

  echo "  Building frontend:0.5.0..."
  docker build -t frontend:0.5.0 frontend/ > /dev/null 2>&1

  echo "  Building api:0.3.2..."
  docker build -t api:0.3.2 api/ > /dev/null 2>&1

  echo "  Building consumer:0.3.0..."
  docker build -t consumer:0.3.0 consumer/ > /dev/null 2>&1

  echo "✅ Images built"
else
  echo "⚠️  Skipping image build (use --rebuild to build images)"
  echo "   Assuming images exist in Minikube Docker"
fi

# Verify images exist
echo ""
echo "🔍 Verifying images in Minikube..."
eval $(minikube docker-env)

if ! docker images | grep -q "frontend.*0.5.0"; then
  echo "❌ frontend:0.5.0 not found in Minikube Docker"
  echo "   Run: ./scripts/deploy-local.sh --rebuild"
  exit 1
fi

if ! docker images | grep -q "api.*0.3.2"; then
  echo "❌ api:0.3.2 not found in Minikube Docker"
  echo "   Run: ./scripts/deploy-local.sh --rebuild"
  exit 1
fi

if ! docker images | grep -q "consumer.*0.3.0"; then
  echo "❌ consumer:0.3.0 not found in Minikube Docker"
  echo "   Run: ./scripts/deploy-local.sh --rebuild"
  exit 1
fi

echo "✅ All images present"

# Uninstall existing release if exists
if helm list --all-namespaces | grep -q $RELEASE_NAME; then
  echo ""
  echo "🧹 Uninstalling existing release..."
  helm uninstall $RELEASE_NAME
  sleep 5
fi

# Deploy with Helm
echo ""
echo "📦 Deploying with Helm..."
helm install $RELEASE_NAME ./helm \
  -f helm/values-local.yaml \
  --wait --timeout 5m

echo "✅ Deployment complete"

# Show status
echo ""
echo "📊 Deployment Status"
echo "===================="
kubectl get pods --all-namespaces | grep $NAMESPACE_PREFIX

echo ""
echo "📍 Access Application"
echo "===================="
echo "Port forward frontend:"
echo "  kubectl port-forward -n voting-frontend svc/frontend 8080:80"
echo ""
echo "Or use Minikube service:"
echo "  minikube service frontend -n voting-frontend"
echo ""
echo "Then visit: http://localhost:8080"

echo ""
echo "🔧 Useful Commands"
echo "=================="
echo "View logs:"
echo "  kubectl logs -n voting-api -l app.kubernetes.io/name=api -f"
echo "  kubectl logs -n voting-consumer -l app.kubernetes.io/name=consumer -f"
echo ""
echo "Check database:"
echo "  kubectl exec -n voting-data -it postgres-0 -- psql -U postgres -d votes -c 'SELECT * FROM votes;'"
echo ""
echo "Uninstall:"
echo "  helm uninstall $RELEASE_NAME"
