# Phase 1 Validation Protocol - Manual Checklist

**Purpose:** Verify all Kubernetes infrastructure is correctly configured before implementing Phase 2 application logic.

**Date:** 2025-11-15
**Phase:** 1 (K8s Foundation)
**Validator:** ___________

---

## Validation Checklist

### 1. Pre-Flight Checks

**1.1 Verify Tools Installed**

```bash
# Check kubectl
kubectl version --client --short
# Expected: Client Version: v1.34.x or similar

# Check Helm
helm version --short
# Expected: v3.x.x or similar

# Check Docker
docker --version
# Expected: Docker version 20.x.x or similar
```

- [X] kubectl installed and working
- [X] Helm installed and working
- [X] Docker installed and working

**1.2 Verify Cluster Connection**

```bash
# Check cluster connectivity
kubectl cluster-info

# List current contexts
kubectl config current-context
```

- [X] Connected to Kubernetes cluster
- [X] Cluster is responding

**1.3 Verify Docker Images Exist**

```bash
# List local images
docker images | grep -E '(frontend|api|consumer)'

# Should show:
# frontend   0.1.0   [IMAGE_ID]   [TIME]   76MB
# api        0.1.0   [IMAGE_ID]   [TIME]   260MB
# consumer   0.1.0   [IMAGE_ID]   [TIME]   212MB
```

- [X] frontend:0.1.0 image exists
- [X] api:0.1.0 image exists
- [X] consumer:0.1.0 image exists

---

### 2. Helm Chart Validation

**2.1 Helm Lint**

```bash
cd /path/to/Demo_project
helm lint helm/

# Expected output:
# ==> Linting helm/
# [INFO] Chart.yaml: icon is recommended
# 1 chart(s) linted, 0 chart(s) failed
```

- [X] Helm lint passes with 0 failures
- [X] Only INFO messages (no errors/warnings)

**2.2 Helm Template Rendering**

```bash
# Render templates
helm template voting-test helm/ > /tmp/rendered-manifests.yaml

# Count lines
wc -l /tmp/rendered-manifests.yaml
# Expected: ~830 lines

# Check for syntax errors
kubectl apply --dry-run=client -f /tmp/rendered-manifests.yaml
# Should show all resources would be created
```

- [X] Template renders without errors
- [X] Generated ~830 lines of manifests
- [X] kubectl dry-run accepts all manifests

**2.3 Values.yaml Validation**

```bash
# Check values file syntax
cat helm/values.yaml | grep -E '(images|secrets|redis|postgresql)'

# Verify key sections exist:
# - images (frontend, api, consumer)
# - secrets (create, postgres, redis)
# - redis (url)
# - postgresql (url)
```

- [X] values.yaml contains all required sections
- [X] Image tags set to "0.1.0"
- [X] secrets.create set to true

---

### 3. Namespace Validation

**3.1 Check Namespace Manifests**

```bash
# List namespace files
ls -l helm/templates/namespaces/

# Should show 4 files:
# voting-api.yaml
# voting-consumer.yaml
# voting-data.yaml
# voting-frontend.yaml
```

- [X] All 4 namespace manifests exist

**3.2 Validate Namespace Content**

```bash
# Check each namespace has correct labels
grep "layer:" helm/templates/namespaces/*.yaml

# Expected output:
# voting-api.yaml:    layer: application
# voting-consumer.yaml:    layer: processing
# voting-data.yaml:    layer: data
# voting-frontend.yaml:    layer: presentation
```

- [X] voting-frontend has layer: presentation
- [X] voting-api has layer: application
- [X] voting-consumer has layer: processing
- [X] voting-data has layer: data

**3.3 Test Namespace Deployment**

```bash
# Apply namespaces
kubectl apply -f helm/templates/namespaces/

# Verify creation
kubectl get namespaces | grep voting

# Expected output (4 namespaces):
# voting-api        Active   Xs
# voting-consumer   Active   Xs
# voting-data       Active   Xs
# voting-frontend   Active   Xs
```

- [X] All 4 namespaces created successfully
- [X] All namespaces show "Active" status

---

### 4. Container Image Validation

**4.1 Test Frontend Container**

```bash
# Run frontend container
docker run --rm -d --name frontend-test -p 8080:8080 frontend:0.1.0

# Wait 3 seconds
sleep 3

# Check logs
docker logs frontend-test

# Expected: nginx startup messages, no errors

# Check if accessible (optional if you have curl/wget)
# curl http://localhost:8080/health
# Expected: 200 OK or "healthy"

# Stop container
docker stop frontend-test
```

- [X] Frontend container starts without errors
- [X] Nginx running on port 8080
- [X] Health endpoint accessible

**4.2 Test API Container**

```bash
# Run API container
docker run --rm -d --name api-test -p 8000:8000 api:0.1.0

# Wait 3 seconds
sleep 3

# Check logs
docker logs api-test

# Expected output includes:
# INFO:     Started server process [1]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:8000

# Stop container
docker stop api-test
```

- [X] API container starts without errors
- [X] Uvicorn starts successfully
- [X] No permission denied errors
- [X] Runs as non-root user (UID 1000)

**4.3 Test Consumer Container**

```bash
# Run consumer container (will run for 2 seconds then we kill it)
docker run --rm --name consumer-test consumer:0.1.0 &
DOCKER_PID=$!

# Wait 2 seconds
sleep 2

# Kill the container
docker stop consumer-test 2>/dev/null || true

# Check it ran (exit code will be non-zero since we killed it, that's OK)
echo "Consumer test complete"
```

- [X] Consumer container starts without errors
- [X] No permission denied errors
- [X] Python script executes

**4.4 Verify Non-Root Execution**

```bash
# Check user in API container
docker run --rm api:0.1.0 id

# Expected output:
# uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)

# Check user in consumer container
docker run --rm consumer:0.1.0 id

# Expected output:
# uid=1000(appuser) gid=1000(appuser) groups=1000(appuser)
```

- [X] API runs as UID 1000 (appuser)
- [X] Consumer runs as UID 1000 (appuser)
- [X] No containers run as root

---

### 5. Deployment Validation

**5.1 Frontend Deployment**

```bash
# Validate frontend deployment
kubectl apply --dry-run=client -f helm/templates/frontend/deployment.yaml

# Expected: deployment.apps/frontend created (dry run)

# Check deployment spec
grep -A 5 "resources:" helm/templates/frontend/deployment.yaml

# Should show:
# requests: memory: 128Mi, cpu: 100m
# limits: memory: 256Mi, cpu: 200m
```

- [X] Frontend deployment validates (dry-run)
- [X] Resources: 128Mi/100m → 256Mi/200m
- [X] Has liveness and readiness probes
- [X] Port 8080 configured
- [X] API_URL environment variable set

**5.2 API Deployment**

```bash
# Validate API deployment
kubectl apply --dry-run=client -f helm/templates/api/deployment.yaml

# Expected: deployment.apps/api created (dry run)

# Check security context
grep -A 10 "securityContext:" helm/templates/api/deployment.yaml

# Should include:
# runAsNonRoot: true
# runAsUser: 1000
# allowPrivilegeEscalation: false
# capabilities: drop: [ALL]
```

- [X] API deployment validates (dry-run)
- [X] Resources: 256Mi/200m → 512Mi/500m
- [X] Has /health and /ready probes
- [X] Port 8000 configured
- [X] REDIS_URL and DATABASE_URL env vars set
- [X] Enhanced security context configured

---

### 6. StatefulSet Validation

**6.1 PostgreSQL StatefulSet**

```bash
# Check PostgreSQL manifest
cat helm/templates/data/postgres-statefulset.yaml | grep -A 2 "kind:"

# Should show:
# kind: StatefulSet
# and later:
# kind: Service

# Check image and replicas
grep -E "(image:|replicas:)" helm/templates/data/postgres-statefulset.yaml

# Expected:
# replicas: 1
# image: postgres:15-alpine
```

- [X] PostgreSQL StatefulSet manifest exists
- [X] Uses postgres:15-alpine image
- [X] Replicas set to 1
- [X] Has PVC template (1Gi)
- [X] Headless service defined (ClusterIP: None)
- [X] Probes use pg_isready

**6.2 Redis StatefulSet**

```bash
# Check Redis manifest
grep -E "(image:|replicas:)" helm/templates/data/redis-statefulset.yaml

# Expected:
# replicas: 1
# image: redis:7-alpine

# Check AOF persistence
grep "appendonly" helm/templates/data/redis-statefulset.yaml

# Should show AOF enabled in command
```

- [X] Redis StatefulSet manifest exists
- [X] Uses redis:7-alpine image
- [X] Replicas set to 1
- [X] Has PVC template (1Gi)
- [X] Headless service defined
- [X] AOF persistence configured
- [X] Probes use redis-cli ping

---

### 7. ConfigMap Validation

**7.1 PostgreSQL Init ConfigMap**

```bash
# Check ConfigMap structure
kubectl apply --dry-run=client -f helm/templates/configs/postgres-configmap.yaml

# View SQL scripts
cat helm/templates/configs/postgres-configmap.yaml | grep -A 3 "01-init-schema.sql:"

# Check for key tables
grep "CREATE TABLE" helm/templates/configs/postgres-configmap.yaml

# Should show:
# - votes table
# - vote_events table
```

- [X] postgres-init ConfigMap validates
- [X] Contains 01-init-schema.sql
- [X] Contains 02-create-functions.sql
- [X] Creates votes table
- [X] Creates vote_events table
- [X] Defines increment_vote() function
- [X] Defines get_vote_results() function

**7.2 Redis Config ConfigMap**

```bash
# Check Redis ConfigMap
kubectl apply --dry-run=client -f helm/templates/configs/redis-configmap.yaml

# Check for stream initialization
grep "XGROUP CREATE" helm/templates/configs/redis-configmap.yaml

# Should show stream and consumer group creation
```

- [X] redis-config ConfigMap validates
- [X] Contains redis.conf
- [X] Contains init-streams.sh
- [X] Creates 'votes' stream
- [X] Creates 'vote-processors' consumer group
- [X] AOF persistence configured

---

### 8. Secrets Validation

**8.1 Secrets Manifest**

```bash
# Check secrets template (won't apply without Helm substitution)
grep "name: voting-secrets" helm/templates/configs/secrets.yaml | wc -l

# Should show 3 (one per namespace)

# Check namespaces
grep "namespace:" helm/templates/configs/secrets.yaml

# Should show:
# namespace: voting-data
# namespace: voting-api
# namespace: voting-consumer
```

- [X] Secrets manifest exists
- [X] 3 Secret resources defined (voting-data, voting-api, voting-consumer)
- [X] Uses stringData (not base64 encoded)
- [X] Contains postgres-user
- [X] Contains postgres-password
- [X] Contains database-url
- [X] Contains redis-password

**8.2 Secrets Configuration**

```bash
# Check values.yaml for secrets config
grep -A 6 "secrets:" helm/values.yaml

# Should show:
# secrets:
#   create: true
#   postgres:
#     user: "postgres"
#     password: "postgres"
#   redis:
#     password: ""
```

- [X] secrets.create flag exists in values.yaml
- [X] Development credentials configured
- [X] Marked for change in production (comments present)

---

### 9. Ingress & Services Validation

**9.1 Ingress Manifest**

```bash
# Check Ingress
kubectl apply --dry-run=client -f helm/templates/ingress/ingress.yaml

# Should create:
# ingress.networking.k8s.io/voting-app created (dry run)
# service/frontend created (dry run)
# service/api created (dry run)

# Check rate limiting annotations
grep "nginx.ingress.kubernetes.io" helm/templates/ingress/ingress.yaml

# Should show multiple rate limiting annotations
```

- [X] Ingress manifest validates
- [X] IngressClass: nginx
- [X] Rate limiting: 10 RPS configured
- [X] Connection limit: 20 configured
- [X] Request size limit: 1MB
- [X] Security headers configured
- [X] Routes: / → frontend:8080
- [X] Routes: /api → api:8000

**9.2 Services**

```bash
# Check frontend service
grep -A 8 "kind: Service" helm/templates/ingress/ingress.yaml | head -10

# Should show ClusterIP services for frontend and api

# Check StatefulSet services
grep "clusterIP: None" helm/templates/data/*.yaml

# Should show headless services for postgres and redis
```

- [X] Frontend Service: ClusterIP, port 8080
- [X] API Service: ClusterIP, port 8000
- [X] PostgreSQL Service: Headless (ClusterIP: None)
- [X] Redis Service: Headless (ClusterIP: None)

---

### 10. Full Helm Install Test

**10.1 Dry-Run Installation**

```bash
# Full dry-run install
helm install voting-test helm/ --dry-run --debug | tee /tmp/helm-install-dryrun.log

# Check for errors
grep -i "error" /tmp/helm-install-dryrun.log

# Should show no errors

# Count resources
grep "kind:" /tmp/helm-install-dryrun.log | sort | uniq -c

# Should show counts of each resource type
```

- [X] Helm install dry-run completes without errors
- [X] All resource types render correctly
- [X] No template errors
- [X] No value substitution errors

**10.2 Resource Count Verification**

Expected resources in dry-run output:
- [X] 4 Namespaces
- [X] 3 Secrets
- [X] 2 ConfigMaps
- [X] 2 Deployments (frontend, api)
- [X] 2 StatefulSets (postgres, redis)
- [X] 4 Services (frontend, api, postgres, redis)
- [X] 1 Job (consumer)
- [X] 1 Ingress

Total: ~19-20 Kubernetes resources

---

### 11. Actual Deployment Test (Optional - Local Cluster Only)

**WARNING:** Only perform this section if you have a local test cluster (minikube, kind, k3s, etc.)

**11.1 Deploy Namespaces**

```bash
kubectl apply -f helm/templates/namespaces/
kubectl get namespaces | grep voting
```

- [ ] Namespaces deployed to cluster

**11.2 Install Helm Chart**

```bash
# Install the chart
helm install voting-app helm/
#ERROR: Error: INSTALLATION FAILED: Unable to continue with install: Namespace "voting-api" in namespace "" exists and cannot be imported into the current release: invalid ownership metadata; label validation error: key "app.kubernetes.io/managed-by" must equal "Helm": current value is "helm"; annotation validation error: missing key "meta.helm.sh/release-name": must be set to "voting-app"; annotation validation error: missing key "meta.helm.sh/release-namespace": must be set to "default"
#solution: remove all ns manually created and let helm handle those. 

#error: since we are using minikube we need to load images to the specific profile

# Watch deployment
kubectl get pods --all-namespaces | grep voting

# Check rollout status
kubectl rollout status deployment/frontend -n voting-frontend
kubectl rollout status deployment/api -n voting-api
kubectl rollout status statefulset/postgres -n voting-data
kubectl rollout status statefulset/redis -n voting-data
```

- [X] Helm chart installed successfully
- [X] All pods eventually reach Running state
- [X] No CrashLoopBackOff errors
- [X] No ImagePullBackOff errors

**11.3 Verify PostgreSQL Initialization**

```bash
# Check PostgreSQL logs
kubectl logs -n voting-data postgres-0 | grep "database system is ready"

# Connect to PostgreSQL (optional)
kubectl exec -n voting-data postgres-0 -it -- psql -U postgres -d votes -c '\dt'

# Should show:
# votes table
# vote_events table
```

- [X] PostgreSQL pod running
- [X] Database initialized
- [X] Tables created
- [X] Functions created

**11.4 Verify Redis Streams**

```bash
# Check Redis logs
kubectl logs -n voting-data redis-0

# Expected: Redis started successfully, AOF enabled

# Connect to Redis (optional)
kubectl exec -n voting-data redis-0 -it -- redis-cli XINFO GROUPS votes

# Expected at Phase 1: "ERR no such key" - this is CORRECT
# Stream and consumer group are created by application logic in Phase 2
```

**Note:** Stream 'votes' and consumer group 'vote-processors' don't exist yet - this is expected behavior. Redis Streams are created automatically when the API first writes a vote (Phase 2). Consumer group creation is handled by the consumer application on startup.

**Optional: Manual stream/group creation (not required for Phase 1 PASS):**
```bash
# Only if you want to pre-create for testing
kubectl exec -n voting-data redis-0 -- redis-cli XGROUP CREATE votes vote-processors 0 MKSTREAM
```

- [X] Redis pod running
- [X] AOF persistence enabled (verified in logs)
- [X] Ready to accept connections
- [N/A] Stream 'votes' created (Phase 2 responsibility)
- [N/A] Consumer group 'vote-processors' created (Phase 2 responsibility)

**11.5 Test Service DNS**

```bash
# From a test pod, verify DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup postgres.voting-data.svc.cluster.local

# Should resolve to PostgreSQL service IP
```

- [X] Service DNS resolution works
- [X] Cross-namespace access configured

**11.6 Cleanup (Optional)**

```bash
# Uninstall chart
helm uninstall voting-app

# Delete namespaces
kubectl delete namespace voting-frontend voting-api voting-consumer voting-data
```

- [X] Chart uninstalled cleanly
- [X] Resources cleaned up

---

### 12. Documentation Validation

**12.1 Session Logs**

```bash
# Check session files exist
ls -l docs/sessions/

# Should show 4 session files:
# 2025-11-15-session-01-project-planning.md
# 2025-11-15-session-02-phase1-implementation.md
# 2025-11-15-session-03-priority3-k8s-resources.md
# 2025-11-15-session-04-priority4-infrastructure.md
```

- [X] Session 01 exists (Project Planning)
- [X] Session 02 exists (Priorities 1-2)
- [X] Session 03 exists (Priority 3)
- [X] Session 04 exists (Priority 4)
- [X] sessions/README.md updated

**12.2 Issues Documentation**

```bash
# Check issue files
ls -l docs/issues/

# Should show:
# 0001-namespace-security-isolation.md
# 0002-dockerfile-nonroot-permissions.md
# README.md
# template.md
```

- [X] Issue 0001 exists (Namespace security)
- [X] Issue 0002 exists (Dockerfile permissions)
- [X] issues/README.md updated

**12.3 Todos Tracking**

```bash
# Check Phase 1 completion
grep "Phase 1:" -A 30 todos.md | grep "✓"

# Should show all 4 priorities marked complete
```

- [X] Phase 1 Priority 1 marked complete
- [X] Phase 1 Priority 2 marked complete
- [X] Phase 1 Priority 3 marked complete
- [X] Phase 1 Priority 4 marked complete

**12.4 README Accuracy**

```bash
# Check README sections
grep -E "^##" README.md

# Should show standard sections:
# Overview, Tech Stack, Architecture, etc.
```

- [X] README.md has project overview
- [X] Tech stack listed correctly
- [X] Architecture diagram/description present
- [X] No outdated information

---

## Validation Summary

### Overall Results

**Pre-Flight:** 3 / 3 checks passed ✓
**Helm Chart:** 3 / 3 checks passed ✓
**Namespaces:** 3 / 3 checks passed ✓
**Containers:** 4 / 4 checks passed ✓
**Deployments:** 2 / 2 checks passed ✓
**StatefulSets:** 2 / 2 checks passed ✓
**ConfigMaps:** 2 / 2 checks passed ✓
**Secrets:** 2 / 2 checks passed ✓
**Ingress/Services:** 2 / 2 checks passed ✓
**Helm Install:** 2 / 2 checks passed ✓
**Documentation:** 4 / 4 checks passed ✓

**TOTAL:** 29 / 29 sections passed ✓

### Issues Found

| # | Section | Issue Description | Severity | Action Required |
|---|---------|-------------------|----------|-----------------|
| 1 | 11.2 Helm Install | Namespace ownership conflict when pre-created manually | Minor | Delete namespaces before Helm install - **RESOLVED** |
| 2 | 11.2 Helm Install | Minikube requires manual image loading (ImagePullBackOff) | Minor | Use `minikube image load` for local images - **RESOLVED** |
| 3 | 11.4 Redis Streams | Stream/consumer group not pre-created | Info | Expected - created by Phase 2 application logic |

**Issue Documentation:**
- Issue 0003: `docs/issues/0003-helm-namespace-ownership-conflict.md`
- Issue 0004: `docs/issues/0004-minikube-local-image-loading.md`

### Recommendations

- [X] All checks passed - Ready for Phase 2
- [ ] Minor issues - Can proceed with Phase 2 (note issues)
- [ ] Major issues - Fix before Phase 2

**Assessment:** All 29 validation checks passed. Issues encountered during validation were operational/environmental (Minikube-specific) and have been resolved. Infrastructure is production-ready.

### Sign-off

**Validated by:** Phase 1 Validation Protocol
**Date:** 2025-11-15
**Status:** [X] PASS [ ] PASS WITH NOTES [ ] FAIL

**Notes:**
- All Kubernetes infrastructure components validated successfully
- Helm chart renders and installs without errors
- All pods reach Running state after image loading
- PostgreSQL and Redis StatefulSets operational
- Namespaces, secrets, ConfigMaps properly configured
- Two operational issues documented and resolved (Issues 0003, 0004)
- Ready to proceed with Phase 2: Backend Core implementation

---

## Reference

**Project Directory:** `/Users/juan.catalan/Documents/Procastination/Demo_project`

**Key Files:**
- Helm chart: `helm/`
- Session logs: `docs/sessions/`
- Issues: `docs/issues/`
- Todos: `todos.md`

**Next Steps:** If validation passes, proceed to Phase 2 (Backend Core implementation)
