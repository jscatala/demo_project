# Phase 5 Validation Protocol - Integration Testing & Load Testing

**Purpose:** Verify complete system integration on Kubernetes with end-to-end vote flow and performance baseline.

**Date:** 2025-11-19
**Phase:** 5.1-5.3 (Integration Testing & Load Testing)
**Validator:** ___________

---

## Validation Checklist

### 1. Pre-Deployment Checks

**1.1 Verify Minikube Cluster**

```bash
# Check minikube profile
minikube profile list

# Expected: demo-project--dev profile exists and is running

# Verify cluster connection
kubectl cluster-info
kubectl get nodes

# Expected: 1 node, Ready status
```

- [ ] Minikube profile demo-project--dev exists
- [ ] Cluster is running and accessible
- [ ] Node is in Ready state

**1.2 Verify Container Images Loaded**

```bash
# List images in minikube
minikube image ls --profile demo-project--dev | grep -E '(frontend|api|consumer)'

# Expected images:
# frontend:0.5.0
# api:0.3.2
# consumer:0.3.1
```

- [ ] frontend:0.5.0 loaded in minikube
- [ ] api:0.3.2 loaded in minikube
- [ ] consumer:0.3.1 loaded in minikube

**1.3 Verify Helm Chart**

```bash
# Helm lint
cd /path/to/Demo_project
helm lint helm/

# Expected: 0 errors, 0 warnings (INFO messages acceptable)

# Check values-local.yaml exists
test -f helm/values-local.yaml && echo "✓ values-local.yaml exists" || echo "✗ Missing"
```

- [ ] Helm lint passes
- [ ] helm/values-local.yaml exists
- [ ] Image tags in values-local.yaml match loaded images
- [ ] pullPolicy set to "Never" for local images

---

### 2. Helm Deployment Validation

**2.1 Install or Verify Existing Deployment**

```bash
# Check if already installed
helm list --all-namespaces

# If not installed:
# helm install voting-app helm/ -f helm/values-local.yaml

# If already installed, verify revision
helm history voting-app

# Expected: STATUS: deployed
```

- [ ] Helm release "voting-app" deployed
- [ ] Deployment status: deployed
- [ ] Current revision documented: _____

**2.2 Verify All Namespaces Created**

```bash
# List voting namespaces
kubectl get namespaces | grep voting

# Expected: 4 namespaces
# voting-frontend   Active   Xs
# voting-api        Active   Xs
# voting-consumer   Active   Xs
# voting-data       Active   Xs
```

- [ ] voting-frontend namespace exists
- [ ] voting-api namespace exists
- [ ] voting-consumer namespace exists
- [ ] voting-data namespace exists

**2.3 Verify All Pods Running**

```bash
# Check pod status across all namespaces
kubectl get pods --all-namespaces | grep voting

# Expected pods:
# voting-frontend   frontend-xxxxx-xxxxx          1/1     Running
# voting-api        api-xxxxx-xxxxx               1/1     Running
# voting-consumer   consumer-xxxxx-xxxxx          1/1     Running
# voting-data       postgres-0                    1/1     Running
# voting-data       redis-0                       1/1     Running

# Check for crashloops or errors
kubectl get pods --all-namespaces | grep -E "(voting.*Error|voting.*CrashLoop)"

# Expected: No output (no errors)
```

- [ ] Frontend pod running (1/1 Ready)
- [ ] API pod running (1/1 Ready)
- [ ] Consumer pod running (1/1 Ready)
- [ ] PostgreSQL pod running (1/1 Ready)
- [ ] Redis pod running (1/1 Ready)
- [ ] No pods in CrashLoopBackOff
- [ ] No pods in Error state

**2.4 Verify Services**

```bash
# List services
kubectl get svc --all-namespaces | grep voting

# Expected services:
# voting-frontend   frontend    ClusterIP      x.x.x.x    8080/TCP
# voting-api        api         ClusterIP      x.x.x.x    8000/TCP
# voting-data       postgres    ClusterIP None            5432/TCP
# voting-data       redis       ClusterIP None            6379/TCP
```

- [ ] Frontend service exists (ClusterIP, port 8080)
- [ ] API service exists (ClusterIP, port 8000)
- [ ] PostgreSQL service exists (Headless, port 5432)
- [ ] Redis service exists (Headless, port 6379)

---

### 3. Network Policy Validation

**3.1 Verify Network Policies Deployed**

```bash
# Check network policies exist
kubectl get networkpolicies --all-namespaces

# Expected: 12 policies total
# 4 default-deny policies (one per namespace)
# 4 allow-dns egress policies (one per namespace)
# 4 service-specific allow policies

# Count policies
kubectl get networkpolicies --all-namespaces --no-headers | wc -l

# Expected: 12
```

- [ ] 12 network policies deployed
- [ ] 4 default-deny ingress policies (one per voting namespace)
- [ ] 4 allow-dns egress policies (one per voting namespace)
- [ ] 4 service-specific allow policies

**3.2 Verify Calico CNI**

```bash
# Check Calico pods
kubectl get pods -n kube-system | grep calico

# Expected:
# calico-kube-controllers-xxxxx   1/1     Running
# calico-node-xxxxx               1/1     Running

# Verify Calico version
kubectl get pod -n kube-system -l k8s-app=calico-node -o jsonpath='{.items[0].spec.containers[0].image}'

# Expected: calico/node:v3.27.0 or similar
```

- [ ] Calico kube-controllers pod running
- [ ] Calico node pod running
- [ ] Calico version: v3.27.0 or compatible

**3.3 Test Network Connectivity**

```bash
# Run network policy validation script
./scripts/test-network-policies.sh

# Expected: All tests pass
# - Allowed connections succeed (API→Redis, API→PostgreSQL, Consumer→Redis, Consumer→PostgreSQL, DNS)
# - Denied connections fail (Frontend→Redis, Frontend→PostgreSQL, Consumer→API)

# Note: Script requires 'nc' tool in containers
# Alternative: Verify via working vote flow (Section 4)
```

- [ ] Network policy test script exists
- [ ] Allowed connections working (verified via vote flow)
- [ ] Denied connections blocked (documented in NETWORK_POLICY.md)

---

### 4. End-to-End Vote Flow Validation

**4.1 Setup Port Forwarding**

```bash
# Forward frontend and API ports
kubectl port-forward -n voting-frontend svc/frontend 8081:8080 --address=127.0.0.1 &
FRONTEND_PID=$!

kubectl port-forward -n voting-api svc/api 8000:8000 --address=127.0.0.1 &
API_PID=$!

# Wait for port forwards to establish
sleep 3

# Verify ports listening
lsof -i :8081 | grep kubectl
lsof -i :8000 | grep kubectl
```

- [ ] Frontend port forward established (8081→8080)
- [ ] API port forward established (8000→8000)
- [ ] Ports responding to connections

**4.2 Verify API Health Endpoints**

```bash
# Test API health
curl -i http://localhost:8000/health

# Expected: HTTP/1.1 200 OK
# {"status": "healthy"}

# Test API readiness
curl -i http://localhost:8000/ready

# Expected: HTTP/1.1 200 OK
# {"status": "ready", "redis": "connected", "database": "connected"}
```

- [ ] GET /health returns 200 OK
- [ ] GET /ready returns 200 OK
- [ ] Redis connection confirmed in /ready response
- [ ] Database connection confirmed in /ready response

**4.3 Submit Test Vote**

```bash
# Submit vote for cats
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option":"cats"}' \
  -i

# Expected: HTTP/1.1 201 Created
# Response body: {"message":"Vote recorded successfully","option":"cats","stream_id":"xxxxx-x"}

# Submit vote for dogs
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option":"dogs"}' \
  -i

# Expected: HTTP/1.1 201 Created
```

- [ ] POST /api/vote returns 201 Created
- [ ] Response includes stream_id
- [ ] Response includes submitted option
- [ ] Vote for "cats" successful
- [ ] Vote for "dogs" successful

**4.4 Verify Vote in Redis Stream**

```bash
# Check Redis Stream length
kubectl exec -n voting-data redis-0 -- redis-cli XLEN votes

# Expected: Number of votes submitted (2 if following above)

# Check stream messages
kubectl exec -n voting-data redis-0 -- redis-cli XRANGE votes - + COUNT 5

# Expected: Stream entries with vote data

# Check consumer group status
kubectl exec -n voting-data redis-0 -- redis-cli XINFO GROUPS votes

# Expected:
# name: vote-processors
# pending: 0 (or low number if processing in progress)
# lag: 0
```

- [ ] Redis Stream "votes" exists
- [ ] XLEN matches submitted vote count
- [ ] Consumer group "vote-processors" exists
- [ ] Consumer lag is 0 (all votes processed)

**4.5 Verify Consumer Processing**

```bash
# Check consumer logs for vote processing
kubectl logs -n voting-consumer deployment/consumer --tail=20

# Expected: JSON logs showing:
# - "event": "messages_received"
# - "event": "processing_vote"
# - "event": "vote_processed"
# - message_id matching stream IDs

# Check consumer is running
kubectl get pods -n voting-consumer -l app.kubernetes.io/component=consumer

# Expected: 1/1 Running
```

- [ ] Consumer pod logs show vote processing
- [ ] No error logs in consumer
- [ ] "vote_processed" events logged
- [ ] message_id in logs matches Redis Stream IDs

**4.6 Verify Vote Counts in PostgreSQL**

```bash
# Query vote counts
kubectl exec -n voting-data postgres-0 -- \
  psql -U postgres -d votes -c "SELECT option, count FROM votes ORDER BY count DESC;"

# Expected output:
#  option | count
# --------+-------
#  cats   |     1
#  dogs   |     1
# (2 rows)

# Verify total matches submitted votes
kubectl exec -n voting-data postgres-0 -- \
  psql -U postgres -d votes -c "SELECT SUM(count) as total FROM votes;"

# Expected: total | 2
```

- [ ] PostgreSQL votes table contains data
- [ ] Vote counts match submitted votes
- [ ] Both "cats" and "dogs" options present
- [ ] No duplicate or lost votes

**4.7 Verify Results Endpoint**

```bash
# Get vote results
curl -s http://localhost:8000/api/results | jq

# Expected JSON:
# {
#   "results": [
#     {"option": "cats", "count": 1, "percentage": 50.0},
#     {"option": "dogs", "count": 1, "percentage": 50.0}
#   ],
#   "total_votes": 2,
#   "last_updated": "2025-11-19T..."
# }

# Verify Cache-Control header
curl -I http://localhost:8000/api/results | grep -i cache-control

# Expected: Cache-Control: public, max-age=2
```

- [ ] GET /api/results returns 200 OK
- [ ] Results JSON matches PostgreSQL counts
- [ ] Percentages calculated correctly (50%/50%)
- [ ] total_votes matches sum of counts
- [ ] Cache-Control header present
- [ ] last_updated timestamp present

**4.8 Cleanup Port Forwards**

```bash
# Kill port forward processes
kill $FRONTEND_PID $API_PID 2>/dev/null || true

# Or find and kill all kubectl port-forwards
pkill -f "kubectl port-forward"
```

- [ ] Port forwards cleaned up

---

### 5. Load Testing Baseline Validation

**5.1 Verify metrics-server Installed**

```bash
# Check metrics-server addon
minikube addons list -p demo-project--dev | grep metrics-server

# Expected: metrics-server: enabled

# Verify metrics-server pod
kubectl get pods -n kube-system | grep metrics-server

# Expected: metrics-server-xxxxx   1/1     Running

# Test kubectl top
kubectl top nodes
kubectl top pods --all-namespaces | grep voting
```

- [ ] metrics-server addon enabled
- [ ] metrics-server pod running
- [ ] kubectl top nodes works
- [ ] kubectl top pods shows voting pods

**5.2 Verify Load Testing Tools**

```bash
# Check Apache Bench installed
which ab || echo "Apache Bench not found"

# Expected: /usr/bin/ab or /usr/local/bin/ab

# Test ab version
ab -V

# Expected: ApacheBench Version 2.3 or similar
```

- [ ] Apache Bench (ab) installed
- [ ] ab command accessible in PATH

**5.3 Run Baseline Performance Test**

```bash
# Setup port forward
kubectl port-forward -n voting-api svc/api 8000:8000 --address=127.0.0.1 &
sleep 3

# Create vote payload
echo '{"option":"cats"}' > /tmp/vote.json

# Run baseline test (10 sequential requests)
ab -n 10 -c 1 -p /tmp/vote.json -T application/json http://127.0.0.1:8000/api/vote

# Expected output:
# - Complete requests: 10
# - Failed requests: 0
# - Time per request: ~500ms (mean)
# - Requests per second: ~2 [#/sec]

# Record P50 and P95 latency from "Percentage of requests" section
```

- [ ] Baseline test completed successfully
- [ ] 0 failed requests
- [ ] P50 latency documented: _____ ms
- [ ] P95 latency documented: _____ ms

**5.4 Run Concurrent Load Test**

```bash
# Run 10 concurrent users, 100 total requests
ab -n 100 -c 10 -p /tmp/vote.json -T application/json http://127.0.0.1:8000/api/vote

# Expected output:
# - Complete requests: 100
# - Failed requests: 0
# - Time per request: ~600ms (mean)
# - Requests per second: ~15-20 [#/sec]
# - P50: ~500-600ms
# - P95: ~1000-1500ms

# Record metrics
```

- [ ] Concurrent load test completed
- [ ] 0 failed requests
- [ ] Throughput documented: _____ req/sec
- [ ] P50 latency documented: _____ ms
- [ ] P95 latency documented: _____ ms
- [ ] P99 latency documented: _____ ms

**5.5 Verify Resource Usage Under Load**

```bash
# Monitor pod metrics during load test
# (Run in separate terminal while load test runs)
watch -n 1 'kubectl top pods --all-namespaces | grep voting'

# Expected observations:
# - API CPU increases (5m idle → 15-20m under load)
# - Consumer CPU increases (3m idle → 30-50m under load)
# - PostgreSQL CPU stable (~15m)
# - Redis CPU stable (~10-15m)
# - Memory usage stable (no leaks)

# Record peak usage
kubectl top pods --all-namespaces | grep voting
```

- [ ] API CPU under load: _____ millicores
- [ ] Consumer CPU under load: _____ millicores
- [ ] PostgreSQL CPU: _____ millicores
- [ ] Redis CPU: _____ millicores
- [ ] Memory usage stable (no leaks observed)

**5.6 Verify Vote Accuracy After Load Test**

```bash
# Query total votes in PostgreSQL
kubectl exec -n voting-data postgres-0 -- \
  psql -U postgres -d votes -c "SELECT SUM(count) as total FROM votes;"

# Expected: total matches number of requests submitted
# (2 baseline + 10 sequential + 100 concurrent = 112 total)

# Check Redis consumer lag
kubectl exec -n voting-data redis-0 -- redis-cli XINFO GROUPS votes

# Expected: lag: 0, pending: 0
```

- [ ] Total votes match submitted requests
- [ ] Consumer lag is 0 (all votes processed)
- [ ] No lost or duplicate votes

---

### 6. Performance Metrics Documentation

**6.1 Verify Session Documentation**

```bash
# Check session file exists
test -f docs/sessions/2025-11-19-session-13-phase5.3-load-testing.md && \
  echo "✓ Session 13 exists" || echo "✗ Missing"

# Check file size (should be substantial)
wc -l docs/sessions/2025-11-19-session-13-phase5.3-load-testing.md

# Expected: 700+ lines
```

- [ ] Session 13 documentation exists
- [ ] File size > 700 lines (comprehensive)
- [ ] Contains performance metrics tables
- [ ] Contains Apache Bench raw output
- [ ] Contains recommendations section

**6.2 Verify Technology Documentation**

```bash
# Check tech-to-review.md updated
grep -A 5 "Kubernetes Observability" docs/tech-to-review.md
grep -A 5 "Load Testing Tools" docs/tech-to-review.md

# Expected: Both sections exist with detailed content
```

- [ ] Observability section added to tech-to-review.md
- [ ] Load testing tools section added to tech-to-review.md
- [ ] metrics-server vs Prometheus/Grafana comparison documented
- [ ] Apache Bench, k6, Locust comparison documented

**6.3 Verify CHANGELOG.md Updated**

```bash
# Check Phase 5.3 entry in CHANGELOG
grep -A 10 "Phase 5.3" CHANGELOG.md

# Expected: Comprehensive entry with metrics
```

- [ ] Phase 5.3 entry in CHANGELOG.md
- [ ] Performance metrics documented (P50, P95, throughput)
- [ ] Vote accuracy documented (100%)
- [ ] Consumer lag documented (0)

---

### 7. Documentation Validation

**7.1 Verify README Updated**

```bash
# Check phase badge
grep "phase-5.3_complete" README.md

# Expected: ![Phase](https://img.shields.io/badge/phase-5.3_complete-green)

# Check phase status section
grep -A 5 "Phase 5.1-5.3" README.md

# Expected: Shows Phase 5.1-5.3 complete
```

- [ ] Phase badge updated to 5.3
- [ ] Phase status shows 5.1-5.3 complete
- [ ] Session count updated to 13

**7.2 Verify todos.md Updated**

```bash
# Check Phase 5.3 marked complete
grep -A 20 "Load testing:" todos.md | grep "\[x\]" | wc -l

# Expected: 11 completed subtasks
```

- [ ] Phase 5.3 main task marked complete
- [ ] 11 of 15 subtasks marked complete
- [ ] Deferred tasks documented with rationale

**7.3 Verify values-local.yaml Configuration**

```bash
# Check local values file
cat helm/values-local.yaml

# Verify key settings:
# - pullPolicy: Never
# - networkPolicies.enabled: true
# - Image tags match deployed versions
```

- [ ] values-local.yaml exists
- [ ] pullPolicy: Never (for local images)
- [ ] networkPolicies.enabled: true
- [ ] Image tags: frontend:0.5.0, api:0.3.2, consumer:0.3.1

---

## Validation Summary

### Overall Results

**Pre-Deployment:** ___ / 3 sections passed
**Helm Deployment:** ___ / 4 sections passed
**Network Policies:** ___ / 3 sections passed
**Vote Flow:** ___ / 8 sections passed
**Load Testing:** ___ / 6 sections passed
**Documentation:** ___ / 3 sections passed

**TOTAL:** ___ / 27 sections passed

### Performance Baseline Summary

| Metric | Sequential | Concurrent (10 users) |
|--------|-----------|----------------------|
| **Throughput** | _____ req/sec | _____ req/sec |
| **P50 Latency** | _____ ms | _____ ms |
| **P95 Latency** | _____ ms | _____ ms |
| **P99 Latency** | _____ ms | _____ ms |
| **Failed Requests** | 0 | 0 |

**Expected Values (Reference):**
- Sequential: 1.92 req/sec, P50: 516ms, P95: 570ms
- Concurrent: 15.94 req/sec, P50: 528ms, P95: 1300ms, P99: 1302ms

**Resource Usage:**
- API CPU: _____ m (idle) → _____ m (load)
- Consumer CPU: _____ m (idle) → _____ m (load)
- Vote Accuracy: 100% (_____/_____ votes processed)
- Consumer Lag: 0

### Issues Found

| # | Section | Issue Description | Severity | Action Required |
|---|---------|-------------------|----------|-----------------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

**Issue Documentation:** docs/issues/

### Recommendations

- [ ] All checks passed - Phase 5.1-5.3 complete
- [ ] Minor issues - Document and proceed
- [ ] Major issues - Fix before marking phase complete

**Assessment:** ___________

### Key Findings

**What Worked:**
- End-to-end vote flow functioning correctly
- Network policies properly isolating services
- Zero vote loss or duplication
- System stable under 10 concurrent users

**Bottlenecks Identified:**
- Consumer CPU usage increases 13.3x under load (most active component)
- P95 latency doubles under concurrent load (570ms → 1300ms)
- Throughput limited to ~16 req/sec (single API pod)

**Next Steps:**
1. Phase 5.4: SSE live updates (deferred to future improvement)
2. Phase 6: Production readiness documentation
3. Future: Horizontal Pod Autoscaling, Prometheus/Grafana, k6 load testing

### Sign-off

**Validated by:** _________________
**Date:** _________________
**Status:** [ ] PASS [ ] PASS WITH NOTES [ ] FAIL

**Notes:**
- Phase 5.1: Helm deployment successful with internal StatefulSets
- Phase 5.2: End-to-end vote flow verified (Vote → Redis → Consumer → PostgreSQL)
- Phase 5.3: Performance baseline established (P50: 528ms, P95: 1300ms, 15.94 req/sec)
- Network policies enabled and validated (12 policies active)
- Zero failures, 100% vote accuracy, zero consumer lag
- System ready for Phase 6 (Documentation) or Phase 5.4 (SSE, deferred)

---

## Reference

**Project Directory:** `/Users/juan.catalan/Documents/Procastination/Demo_project`

**Key Files:**
- Helm chart: `helm/`
- Local config: `helm/values-local.yaml`
- Session logs: `docs/sessions/2025-11-19-session-13-phase5.3-load-testing.md`
- Network policies: `helm/templates/network-policies/`
- Test scripts: `scripts/test-network-policies.sh`

**Key Documentation:**
- [NETWORK_POLICY.md](NETWORK_POLICY.md) - Network policy design and troubleshooting
- [PHASE4_VALIDATION.md](PHASE4_VALIDATION.md) - Security validation checklist
- [tech-to-review.md](../tech-to-review.md) - Technology decisions and future improvements

**Minikube Profile:** demo-project--dev

**Next Steps:** If validation passes, proceed to Phase 6 (Documentation) or Phase 5.4 (SSE live updates)
