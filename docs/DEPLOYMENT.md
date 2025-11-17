# Deployment Guide

Complete guide for deploying the voting application to Kubernetes (Minikube or cloud).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Minikube Setup (Local Development)](#minikube-setup-local-development)
3. [Build Docker Images](#build-docker-images)
4. [Deploy with Helm](#deploy-with-helm)
5. [Verify Deployment](#verify-deployment)
6. [Access Application](#access-application)
7. [Troubleshooting](#troubleshooting)
8. [Cleanup](#cleanup)

---

## Prerequisites

### Required Tools

- **Docker** - Container runtime
- **Minikube** - Local Kubernetes cluster
- **kubectl** - Kubernetes CLI
- **Helm 3+** - Package manager for Kubernetes

### Installation

**macOS (Homebrew):**
```bash
brew install docker minikube kubectl helm
```

**Linux:**
```bash
# Minikube
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install kubectl /usr/local/bin/kubectl

# Helm
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### Verify Installation

```bash
docker --version     # Docker version 20.10+
minikube version     # minikube version v1.33+
kubectl version      # Client v1.29+
helm version         # v3.14+
```

---

## Minikube Setup (Local Development)

### 1. Start Minikube

**Using dedicated profile (recommended):**
```bash
# Start with project-specific profile
minikube start -p demo-project--dev \
  --cpus=4 \
  --memory=8192 \
  --driver=docker \
  --kubernetes-version=stable

# Verify cluster
kubectl cluster-info --context demo-project--dev
kubectl get nodes

# Set as default context (optional)
kubectl config use-context demo-project--dev
```

**Profile benefits:**
- Isolates project from other Minikube clusters
- Dedicated resources and configuration
- Easy cleanup: `minikube delete -p demo-project--dev`

**Default profile (alternative):**
```bash
# Start default profile
minikube start --cpus=4 --memory=8192 --driver=docker
```

### 2. Enable Addons (Optional but Recommended)

```bash
# Using profile (recommended)
minikube addons enable metrics-server -p demo-project--dev
minikube addons enable ingress -p demo-project--dev
minikube addons enable dashboard -p demo-project--dev

# Or without profile (if using default)
minikube addons enable metrics-server
```

### 3. Configure Docker Environment

**IMPORTANT:** Use Minikube's Docker daemon to build images locally.

```bash
# Point shell to Minikube's Docker (with profile)
eval $(minikube docker-env -p demo-project--dev)

# Or default profile
eval $(minikube docker-env)

# Verify (should show Minikube's Docker)
docker context ls
```

**Note:** Run `eval $(minikube docker-env -p demo-project--dev)` in each new terminal session.

---

## Build Docker Images

### Build All Images

**From project root, with Minikube Docker environment active:**

```bash
# Ensure using Minikube Docker (with profile)
eval $(minikube docker-env -p demo-project--dev)

# Build frontend
docker build -t frontend:0.5.0 frontend/

# Build API
docker build -t api:0.3.2 api/

# Build consumer
docker build -t consumer:0.3.0 consumer/

# Verify images
docker images | grep -E "frontend|api|consumer"
```

### Expected Output

```
frontend    0.5.0    [IMAGE_ID]   [TIME]   75.6MB
api         0.3.2    [IMAGE_ID]   [TIME]   166MB
consumer    0.3.0    [IMAGE_ID]   [TIME]   223MB
```

**Common Issue:** If images aren't found during deployment, ensure:
1. You ran `eval $(minikube docker-env -p demo-project--dev)` before building
2. Using correct profile context
3. `imagePullPolicy: IfNotPresent` is set in values.yaml
4. Image tags match exactly between build and values.yaml

See [Issue #0004](issues/0004-minikube-local-image-loading.md) for details.

---

## Image Loading: Why It's Not Needed

**TL;DR:** Our approach builds images INSIDE Minikube's Docker daemon, so no loading step is required.

### Two Approaches Explained

#### Approach A: Direct Build in Minikube (Current - Recommended)

**What we do:**
```bash
# 1. Point Docker CLI to Minikube's daemon
eval $(minikube docker-env -p demo-project--dev)

# 2. Build images (goes directly to Minikube)
docker build -t frontend:0.5.0 frontend/
docker build -t api:0.3.2 api/
docker build -t consumer:0.3.0 consumer/

# 3. Deploy with Helm (images already available)
helm install voting-app ./helm -f helm/values-local.yaml
```

**Why no loading?**
- `eval $(minikube docker-env)` redirects Docker commands to Minikube's Docker daemon
- Images are built directly inside Minikube
- Kubernetes can see them immediately
- `imagePullPolicy: IfNotPresent` prevents pull attempts

**Pros:**
- ✅ Faster (one-step process)
- ✅ Images automatically available to Kubernetes
- ✅ No duplicate storage
- ✅ Used by our scripts (`deploy-local.sh`)

**Cons:**
- ⚠️ Must run `eval $(minikube docker-env)` in each new terminal
- ⚠️ Build cache lives in Minikube (deleted with profile)
- ⚠️ Can't build images if Minikube is stopped

---

#### Approach B: Build on Host + Load (Alternative)

**Alternative workflow:**
```bash
# 1. Build on host Docker (normal)
docker build -t frontend:0.5.0 frontend/

# 2. Load into Minikube
minikube image load frontend:0.5.0 -p demo-project--dev
minikube image load api:0.3.2 -p demo-project--dev
minikube image load consumer:0.3.0 -p demo-project--dev

# 3. Deploy with Helm
helm install voting-app ./helm -f helm/values-local.yaml
```

**When to use:**
- Need to build images without Minikube running
- Want to keep build cache on host machine
- Prefer explicit image transfer step

**Pros:**
- ✅ Build cache persists on host
- ✅ Can build images offline
- ✅ Clear separation (build vs deploy)

**Cons:**
- ❌ Extra step (slower)
- ❌ Doubles disk usage (host + Minikube)
- ❌ More commands to remember
- ❌ Must reload after each rebuild

**Note:** See [Issue #0004](issues/0004-minikube-local-image-loading.md) for detailed analysis of both approaches.

---

### Verification: Where Are My Images?

**Check Minikube's Docker:**
```bash
# Point to Minikube
eval $(minikube docker-env -p demo-project--dev)

# List images
docker images | grep -E "frontend|api|consumer"

# Expected output:
# frontend    0.5.0    [ID]   [TIME]   75.6MB
# api         0.3.2    [ID]   [TIME]   166MB
# consumer    0.3.0    [ID]   [TIME]   223MB
```

**Check host Docker (for comparison):**
```bash
# Reset Docker to host
unset DOCKER_HOST DOCKER_TLS_VERIFY DOCKER_CERT_PATH DOCKER_API_VERSION

# List images
docker images | grep -E "frontend|api|consumer"

# If using Approach A (direct build):
# No output (images only in Minikube)

# If using Approach B (build + load):
# Shows images on both host and Minikube
```

**Verify images in Minikube (alternative method):**
```bash
# SSH into Minikube and check
minikube ssh -p demo-project--dev "docker images | grep -E 'frontend|api|consumer'"
```

---

### Troubleshooting: Images Not Found

**Symptom:** Pods show `ImagePullBackOff` or `ErrImagePull`

**Diagnosis:**
```bash
# Check if you're using Minikube's Docker
echo $DOCKER_HOST
# Expected: tcp://127.0.0.1:[PORT] (Minikube)
# If empty: Using host Docker (WRONG)

# Verify images exist in Minikube
eval $(minikube docker-env -p demo-project--dev)
docker images | grep frontend
```

**Solutions:**

1. **Forgot to run `eval $(minikube docker-env)`:**
   ```bash
   # Rebuild with correct Docker
   eval $(minikube docker-env -p demo-project--dev)
   docker build -t frontend:0.5.0 frontend/
   ```

2. **Built with host Docker by mistake:**
   ```bash
   # Option A: Reload images (quick)
   minikube image load frontend:0.5.0 -p demo-project--dev

   # Option B: Rebuild in Minikube (better)
   eval $(minikube docker-env -p demo-project--dev)
   docker build -t frontend:0.5.0 frontend/
   ```

3. **Wrong imagePullPolicy:**
   ```yaml
   # helm/values-local.yaml should have:
   images:
     frontend:
       pullPolicy: IfNotPresent  # NOT "Always"
   ```

4. **Wrong profile/context:**
   ```bash
   # Ensure using correct profile
   kubectl config current-context
   # Expected: demo-project--dev

   # Switch if needed
   kubectl config use-context demo-project--dev
   ```

---

## Deploy with Helm

### 1. Create values-local.yaml (Optional)

For local development customization:

```bash
cat > helm/values-local.yaml <<EOF
# Local Minikube overrides

# Use local images
images:
  frontend:
    repository: frontend
    tag: "0.5.0"
    pullPolicy: IfNotPresent  # Critical for local images

  api:
    repository: api
    tag: "0.3.2"
    pullPolicy: IfNotPresent

  consumer:
    repository: consumer
    tag: "0.3.0"
    pullPolicy: IfNotPresent

# Lower resource requests for local testing
frontend:
  replicas: 1
  resources:
    requests:
      memory: "64Mi"
      cpu: "50m"

api:
  replicas: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"

consumer:
  replicas: 1
  resources:
    requests:
      memory: "128Mi"
      cpu: "100m"

# Development secrets (DO NOT use in production)
secrets:
  create: true
  postgres:
    user: "postgres"
    password: "localdev"
  redis:
    password: ""
EOF
```

### 2. Deploy with Helm

**Using default values:**
```bash
helm install voting-app ./helm --wait --timeout 5m
```

**Using local overrides:**
```bash
helm install voting-app ./helm \
  -f helm/values-local.yaml \
  --wait --timeout 5m
```

**Dry-run first (recommended):**
```bash
helm install voting-app ./helm -f helm/values-local.yaml --dry-run --debug
```

### 3. Monitor Deployment

```bash
# Watch pods come up
kubectl get pods --all-namespaces -w

# Check specific namespaces
kubectl get pods -n voting-frontend
kubectl get pods -n voting-api
kubectl get pods -n voting-consumer
kubectl get pods -n voting-data
```

**Expected output (when ready):**
```
NAMESPACE          NAME                           READY   STATUS    RESTARTS
voting-frontend    frontend-[hash]                1/1     Running   0
voting-api         api-[hash]                     1/1     Running   0
voting-consumer    consumer-[hash]                1/1     Running   0
voting-data        redis-[hash]                   1/1     Running   0
voting-data        postgres-[hash]                1/1     Running   0
```

---

## Verify Deployment

### 1. Check All Resources

```bash
# List all Helm releases
helm list --all-namespaces

# Check deployments
kubectl get deployments --all-namespaces

# Check services
kubectl get svc --all-namespaces

# Check StatefulSets (Redis, PostgreSQL)
kubectl get statefulsets -n voting-data
```

### 2. Check Logs

```bash
# Frontend logs
kubectl logs -n voting-frontend -l app.kubernetes.io/name=frontend

# API logs
kubectl logs -n voting-api -l app.kubernetes.io/name=api

# Consumer logs
kubectl logs -n voting-consumer -l app.kubernetes.io/name=consumer -f

# Database logs
kubectl logs -n voting-data -l app=postgres
kubectl logs -n voting-data -l app=redis
```

### 3. Test Database Connections

```bash
# Test PostgreSQL
kubectl exec -n voting-data -it postgres-0 -- psql -U postgres -d votes -c "SELECT * FROM votes;"

# Test Redis
kubectl exec -n voting-data -it redis-0 -- redis-cli ping
# Expected: PONG

# Check Redis Stream
kubectl exec -n voting-data -it redis-0 -- redis-cli XLEN votes
# Expected: 0 (or number of votes)
```

---

## Access Application

### Option 1: Port Forward (Quick Testing)

```bash
# Forward frontend
kubectl port-forward -n voting-frontend svc/frontend 8080:80

# Forward API (for direct testing)
kubectl port-forward -n voting-api svc/api 8000:8000

# Visit http://localhost:8080
```

### Option 2: Minikube Service (Automatic)

```bash
# Open frontend in browser
minikube service frontend -n voting-frontend

# Get service URL
minikube service frontend -n voting-frontend --url
```

### Option 3: Ingress (Production-like)

**If ingress addon enabled:**

```bash
# Get Minikube IP
minikube ip

# Add to /etc/hosts
echo "$(minikube ip) voting.local" | sudo tee -a /etc/hosts

# Visit http://voting.local
```

---

## Verify Application Functionality

### 1. Health Checks

```bash
# Frontend health (via port-forward on 8080)
curl http://localhost:8080/

# API health
kubectl exec -n voting-api -it $(kubectl get pod -n voting-api -l app.kubernetes.io/name=api -o name | head -1) -- curl http://localhost:8000/health
# Expected: {"status":"ok"}

# API ready
kubectl exec -n voting-api -it $(kubectl get pod -n voting-api -l app.kubernetes.io/name=api -o name | head -1) -- curl http://localhost:8000/ready
```

### 2. Test Vote Flow

**Via browser (http://localhost:8080):**
1. Click "Cats" or "Dogs" button
2. Verify vote confirmation message
3. Check results update

**Via API (if port-forwarded on 8000):**
```bash
# Submit vote
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "cats"}'

# Get results
curl http://localhost:8000/api/results
```

### 3. Verify Event Processing

```bash
# Check consumer is processing
kubectl logs -n voting-consumer -l app.kubernetes.io/name=consumer --tail=20

# Expected log output:
# {"event": "consumer_started", "consumer_name": "..."}
# {"event": "message_received", "vote": "cats", "message_id": "..."}
# {"event": "vote_incremented", "option": "cats"}
```

---

## Troubleshooting

### Pods Not Starting

**Check events:**
```bash
kubectl get events --all-namespaces --sort-by='.lastTimestamp'
```

**Common issues:**

1. **ImagePullBackOff:**
   - Cause: Images not found in Minikube
   - Fix: Rebuild with `eval $(minikube docker-env)` active
   - Verify: `docker images | grep frontend`

2. **CrashLoopBackOff:**
   - Check logs: `kubectl logs -n [namespace] [pod-name]`
   - Common causes: Missing env vars, database connection failure

3. **Insufficient resources:**
   - Increase Minikube resources: `minikube delete && minikube start --cpus=4 --memory=8192`

### Database Connection Errors

**PostgreSQL not ready:**
```bash
# Check PostgreSQL pod
kubectl get pods -n voting-data | grep postgres

# Check logs
kubectl logs -n voting-data postgres-0

# Manually verify
kubectl exec -n voting-data -it postgres-0 -- psql -U postgres -c "\l"
```

**Redis not ready:**
```bash
# Check Redis pod
kubectl get pods -n voting-data | grep redis

# Test connection
kubectl exec -n voting-data -it redis-0 -- redis-cli ping
```

### Consumer Not Processing Votes

```bash
# Check consumer logs
kubectl logs -n voting-consumer -l app.kubernetes.io/name=consumer -f

# Verify Redis Stream exists
kubectl exec -n voting-data -it redis-0 -- redis-cli XINFO STREAM votes

# Check consumer group
kubectl exec -n voting-data -it redis-0 -- redis-cli XINFO GROUPS votes
```

### Network Policies Blocking Traffic

```bash
# List network policies
kubectl get networkpolicies --all-namespaces

# Temporarily disable for testing (NOT for production)
kubectl delete networkpolicies --all --all-namespaces
```

---

## Cleanup

### Uninstall Helm Release

```bash
# Uninstall application
helm uninstall voting-app

# Verify namespaces removed
kubectl get namespaces | grep voting
```

### Delete Namespaces (if needed)

```bash
kubectl delete namespace voting-frontend
kubectl delete namespace voting-api
kubectl delete namespace voting-consumer
kubectl delete namespace voting-data
```

### Stop Minikube

```bash
# Stop cluster (preserves state)
minikube stop

# Delete cluster (full cleanup)
minikube delete
```

---

## Production Deployment

**For production (cloud Kubernetes):**

1. **Build and push images to registry:**
   ```bash
   docker tag frontend:0.5.0 your-registry/frontend:0.5.0
   docker push your-registry/frontend:0.5.0
   # Repeat for api, consumer
   ```

2. **Create production values:**
   ```bash
   cp helm/values.yaml helm/values-prod.yaml
   # Edit: Set real registry, passwords, resources
   ```

3. **Use external secret management:**
   - Set `secrets.create: false` in values-prod.yaml
   - Use HashiCorp Vault, AWS Secrets Manager, or External Secrets Operator

4. **Deploy with production values:**
   ```bash
   helm install voting-app ./helm -f helm/values-prod.yaml --namespace voting-prod --create-namespace
   ```

---

## Quick Reference

**Full deployment flow:**
```bash
# 1. Start Minikube
minikube start --cpus=4 --memory=8192

# 2. Use Minikube Docker
eval $(minikube docker-env)

# 3. Build images
docker build -t frontend:0.5.0 frontend/
docker build -t api:0.3.2 api/
docker build -t consumer:0.3.0 consumer/

# 4. Deploy
helm install voting-app ./helm -f helm/values-local.yaml --wait

# 5. Access
kubectl port-forward -n voting-frontend svc/frontend 8080:80
# Visit http://localhost:8080

# 6. Cleanup
helm uninstall voting-app
minikube stop -p demo-project--dev
```

**Common commands:**
```bash
# Watch pods
kubectl get pods --all-namespaces -w

# Check logs
kubectl logs -n voting-api -l app.kubernetes.io/name=api -f

# Port forward
kubectl port-forward -n voting-frontend svc/frontend 8080:80

# Restart pod
kubectl rollout restart deployment/api -n voting-api

# Delete and redeploy
helm uninstall voting-app && helm install voting-app ./helm -f helm/values-local.yaml
```

---

## See Also

- [TESTING.md](TESTING.md) - Integration tests with Minikube
- [PHASE*_VALIDATION.md](PHASE1_VALIDATION.md) - Validation protocols
- [Issue #0004](issues/0004-minikube-local-image-loading.md) - Image loading troubleshooting
- [ADR-0001](adr/0001-kubernetes-native-deployment.md) - Why Kubernetes from day 0
