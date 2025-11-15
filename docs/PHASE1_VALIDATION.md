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

- [ ] kubectl installed and working
- [ ] Helm installed and working
- [ ] Docker installed and working

**1.2 Verify Cluster Connection**

```bash
# Check cluster connectivity
kubectl cluster-info

# List current contexts
kubectl config current-context
```

- [ ] Connected to Kubernetes cluster
- [ ] Cluster is responding

**1.3 Verify Docker Images Exist**

```bash
# List local images
docker images | grep -E '(frontend|api|consumer)'

# Should show:
# frontend   0.1.0   [IMAGE_ID]   [TIME]   76MB
# api        0.1.0   [IMAGE_ID]   [TIME]   260MB
# consumer   0.1.0   [IMAGE_ID]   [TIME]   212MB
```

- [ ] frontend:0.1.0 image exists
- [ ] api:0.1.0 image exists
- [ ] consumer:0.1.0 image exists

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

- [ ] Helm lint passes with 0 failures
- [ ] Only INFO messages (no errors/warnings)

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

- [ ] Template renders without errors
- [ ] Generated ~830 lines of manifests
- [ ] kubectl dry-run accepts all manifests

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

- [ ] values.yaml contains all required sections
- [ ] Image tags set to "0.1.0"
- [ ] secrets.create set to true

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

- [ ] All 4 namespace manifests exist

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

- [ ] voting-frontend has layer: presentation
- [ ] voting-api has layer: application
- [ ] voting-consumer has layer: processing
- [ ] voting-data has layer: data

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

- [ ] All 4 namespaces created successfully
- [ ] All namespaces show "Active" status

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

- [ ] Frontend container starts without errors
- [ ] Nginx running on port 8080
- [ ] Health endpoint accessible

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

- [ ] API container starts without errors
- [ ] Uvicorn starts successfully
- [ ] No permission denied errors
- [ ] Runs as non-root user (UID 1000)

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

- [ ] Consumer container starts without errors
- [ ] No permission denied errors
- [ ] Python script executes

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

- [ ] API runs as UID 1000 (appuser)
- [ ] Consumer runs as UID 1000 (appuser)
- [ ] No containers run as root

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

- [ ] Frontend deployment validates (dry-run)
- [ ] Resources: 128Mi/100m → 256Mi/200m
- [ ] Has liveness and readiness probes
- [ ] Port 8080 configured
- [ ] API_URL environment variable set

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

- [ ] API deployment validates (dry-run)
- [ ] Resources: 256Mi/200m → 512Mi/500m
- [ ] Has /health and /ready probes
- [ ] Port 8000 configured
- [ ] REDIS_URL and DATABASE_URL env vars set
- [ ] Enhanced security context configured

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

- [ ] PostgreSQL StatefulSet manifest exists
- [ ] Uses postgres:15-alpine image
- [ ] Replicas set to 1
- [ ] Has PVC template (1Gi)
- [ ] Headless service defined (ClusterIP: None)
- [ ] Probes use pg_isready

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

- [ ] Redis StatefulSet manifest exists
- [ ] Uses redis:7-alpine image
- [ ] Replicas set to 1
- [ ] Has PVC template (1Gi)
- [ ] Headless service defined
- [ ] AOF persistence configured
- [ ] Probes use redis-cli ping

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

- [ ] postgres-init ConfigMap validates
- [ ] Contains 01-init-schema.sql
- [ ] Contains 02-create-functions.sql
- [ ] Creates votes table
- [ ] Creates vote_events table
- [ ] Defines increment_vote() function
- [ ] Defines get_vote_results() function

**7.2 Redis Config ConfigMap**

```bash
# Check Redis ConfigMap
kubectl apply --dry-run=client -f helm/templates/configs/redis-configmap.yaml

# Check for stream initialization
grep "XGROUP CREATE" helm/templates/configs/redis-configmap.yaml

# Should show stream and consumer group creation
```

- [ ] redis-config ConfigMap validates
- [ ] Contains redis.conf
- [ ] Contains init-streams.sh
- [ ] Creates 'votes' stream
- [ ] Creates 'vote-processors' consumer group
- [ ] AOF persistence configured

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

- [ ] Secrets manifest exists
- [ ] 3 Secret resources defined (voting-data, voting-api, voting-consumer)
- [ ] Uses stringData (not base64 encoded)
- [ ] Contains postgres-user
- [ ] Contains postgres-password
- [ ] Contains database-url
- [ ] Contains redis-password

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

- [ ] secrets.create flag exists in values.yaml
- [ ] Development credentials configured
- [ ] Marked for change in production (comments present)

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

- [ ] Ingress manifest validates
- [ ] IngressClass: nginx
- [ ] Rate limiting: 10 RPS configured
- [ ] Connection limit: 20 configured
- [ ] Request size limit: 1MB
- [ ] Security headers configured
- [ ] Routes: / → frontend:8080
- [ ] Routes: /api → api:8000

**9.2 Services**

```bash
# Check frontend service
grep -A 8 "kind: Service" helm/templates/ingress/ingress.yaml | head -10

# Should show ClusterIP services for frontend and api

# Check StatefulSet services
grep "clusterIP: None" helm/templates/data/*.yaml

# Should show headless services for postgres and redis
```

- [ ] Frontend Service: ClusterIP, port 8080
- [ ] API Service: ClusterIP, port 8000
- [ ] PostgreSQL Service: Headless (ClusterIP: None)
- [ ] Redis Service: Headless (ClusterIP: None)

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

- [ ] Helm install dry-run completes without errors
- [ ] All resource types render correctly
- [ ] No template errors
- [ ] No value substitution errors

**10.2 Resource Count Verification**

Expected resources in dry-run output:
- [ ] 4 Namespaces
- [ ] 3 Secrets
- [ ] 2 ConfigMaps
- [ ] 2 Deployments (frontend, api)
- [ ] 2 StatefulSets (postgres, redis)
- [ ] 4 Services (frontend, api, postgres, redis)
- [ ] 1 Job (consumer)
- [ ] 1 Ingress

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

# Watch deployment
kubectl get pods --all-namespaces | grep voting

# Check rollout status
kubectl rollout status deployment/frontend -n voting-frontend
kubectl rollout status deployment/api -n voting-api
kubectl rollout status statefulset/postgres -n voting-data
kubectl rollout status statefulset/redis -n voting-data
```

- [ ] Helm chart installed successfully
- [ ] All pods eventually reach Running state
- [ ] No CrashLoopBackOff errors
- [ ] No ImagePullBackOff errors

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

- [ ] PostgreSQL pod running
- [ ] Database initialized
- [ ] Tables created
- [ ] Functions created

**11.4 Verify Redis Streams**

```bash
# Check Redis logs
kubectl logs -n voting-data redis-0

# Connect to Redis (optional)
kubectl exec -n voting-data redis-0 -it -- redis-cli XINFO GROUPS votes

# Should show 'vote-processors' consumer group
```

- [ ] Redis pod running
- [ ] Stream 'votes' created
- [ ] Consumer group 'vote-processors' created

**11.5 Test Service DNS**

```bash
# From a test pod, verify DNS resolution
kubectl run -it --rm debug --image=busybox --restart=Never -- nslookup postgres.voting-data.svc.cluster.local

# Should resolve to PostgreSQL service IP
```

- [ ] Service DNS resolution works
- [ ] Cross-namespace access configured

**11.6 Cleanup (Optional)**

```bash
# Uninstall chart
helm uninstall voting-app

# Delete namespaces
kubectl delete namespace voting-frontend voting-api voting-consumer voting-data
```

- [ ] Chart uninstalled cleanly
- [ ] Resources cleaned up

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

- [ ] Session 01 exists (Project Planning)
- [ ] Session 02 exists (Priorities 1-2)
- [ ] Session 03 exists (Priority 3)
- [ ] Session 04 exists (Priority 4)
- [ ] sessions/README.md updated

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

- [ ] Issue 0001 exists (Namespace security)
- [ ] Issue 0002 exists (Dockerfile permissions)
- [ ] issues/README.md updated

**12.3 Todos Tracking**

```bash
# Check Phase 1 completion
grep "Phase 1:" -A 30 todos.md | grep "✓"

# Should show all 4 priorities marked complete
```

- [ ] Phase 1 Priority 1 marked complete
- [ ] Phase 1 Priority 2 marked complete
- [ ] Phase 1 Priority 3 marked complete
- [ ] Phase 1 Priority 4 marked complete

**12.4 README Accuracy**

```bash
# Check README sections
grep -E "^##" README.md

# Should show standard sections:
# Overview, Tech Stack, Architecture, etc.
```

- [ ] README.md has project overview
- [ ] Tech stack listed correctly
- [ ] Architecture diagram/description present
- [ ] No outdated information

---

## Validation Summary

### Overall Results

**Pre-Flight:** _____ / 3 checks passed
**Helm Chart:** _____ / 3 checks passed
**Namespaces:** _____ / 3 checks passed
**Containers:** _____ / 4 checks passed
**Deployments:** _____ / 2 checks passed
**StatefulSets:** _____ / 2 checks passed
**ConfigMaps:** _____ / 2 checks passed
**Secrets:** _____ / 2 checks passed
**Ingress/Services:** _____ / 2 checks passed
**Helm Install:** _____ / 2 checks passed
**Documentation:** _____ / 4 checks passed

**TOTAL:** _____ / 29 sections passed

### Issues Found

| # | Section | Issue Description | Severity | Action Required |
|---|---------|-------------------|----------|-----------------|
| 1 |         |                   |          |                 |
| 2 |         |                   |          |                 |
| 3 |         |                   |          |                 |

### Recommendations

- [ ] All checks passed - Ready for Phase 2
- [ ] Minor issues - Can proceed with Phase 2 (note issues)
- [ ] Major issues - Fix before Phase 2

### Sign-off

**Validated by:** ___________
**Date:** ___________
**Status:** [ ] PASS [ ] PASS WITH NOTES [ ] FAIL

**Notes:**
_______________________________________________________________________________
_______________________________________________________________________________
_______________________________________________________________________________

---

## Reference

**Project Directory:** `/Users/juan.catalan/Documents/Procastination/Demo_project`

**Key Files:**
- Helm chart: `helm/`
- Session logs: `docs/sessions/`
- Issues: `docs/issues/`
- Todos: `todos.md`

**Next Steps:** If validation passes, proceed to Phase 2 (Backend Core implementation)
