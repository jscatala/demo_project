# Production Readiness Checklist

Comprehensive pre-deployment validation for Kubernetes production environments.

**Target Audience:** SRE teams, DevOps engineers, platform teams deploying the voting application to cloud Kubernetes clusters.

**Scope:** Production deployments (GKE, EKS, AKS, self-managed Kubernetes). Not applicable to local Minikube development.

---

## Table of Contents

1. [Security Checklist](#1-security-checklist)
2. [Reliability Checklist](#2-reliability-checklist)
3. [Observability Checklist](#3-observability-checklist)
4. [Operational Readiness](#4-operational-readiness)
5. [Scalability Checklist](#5-scalability-checklist)
6. [Compliance Checklist](#6-compliance-checklist)
7. [Pre-Deployment Validation](#7-pre-deployment-validation)
8. [Post-Deployment Verification](#8-post-deployment-verification)
9. [Future Improvements](#9-future-improvements)

---

## 1. Security Checklist

### 1.1 Container Security (Phase 4.2)

- [ ] **All containers run as non-root users**
  - Frontend: UID 1000 (nginx user)
  - API: UID 65532 (distroless nonroot)
  - Consumer: UID 1000 (Python user)
  - Verify: `kubectl get pods -n voting-api -o jsonpath='{.items[*].spec.securityContext.runAsUser}'`

- [ ] **Read-only root filesystems enabled**
  - API and Consumer have `readOnlyRootFilesystem: true`
  - Writable volumes mounted only where required (`/tmp`, `/var/run`)
  - Verify: Check `securityContext.readOnlyRootFilesystem` in pod specs

- [ ] **Capabilities dropped**
  - `securityContext.capabilities.drop: ["ALL"]`
  - Only add back essential capabilities (none required for voting app)
  - Verify: `kubectl get pods -n voting-api -o jsonpath='{.items[*].spec.containers[*].securityContext.capabilities.drop}'`

- [ ] **Container images scanned for vulnerabilities**
  - Run `trivy image` on all production images
  - Zero HIGH/CRITICAL vulnerabilities (see [VULNERABILITY_SCAN.md](VULNERABILITY_SCAN.md))
  - Action items:
    - Frontend (Alpine 3.19.1): Upgrade to Alpine 3.20+ (18 vulnerabilities)
    - API (Debian 12.12): Update python-multipart, starlette (7 vulnerabilities)
    - Consumer (Debian 13.1): Baseline clean (0 vulnerabilities)

- [ ] **Distroless images used where possible**
  - API uses `gcr.io/distroless/python3-debian12:nonroot`
  - Consider migrating frontend to distroless nginx variant
  - Benefits: Reduced attack surface, no shell/package manager

### 1.2 Network Security (Phase 4.5)

- [ ] **NetworkPolicy enforcement enabled**
  - CNI plugin supports NetworkPolicies (Calico v3.27.0, Cilium, or cloud-native)
  - Verify: `kubectl get pods -n kube-system | grep calico`
  - Deploy 12 NetworkPolicy resources: 4 default-deny, 4 DNS egress, 4 service-specific allow

- [ ] **Default-deny ingress policies applied**
  - All 4 namespaces have default-deny ingress policies
  - Only explicit allow rules permit traffic
  - Verify: `kubectl get networkpolicy -n voting-frontend default-deny-ingress`

- [ ] **DNS egress enabled**
  - All namespaces allow egress to `kube-dns` on port 53 (TCP/UDP)
  - Required for Service discovery and external DNS lookups
  - Verify: `kubectl get networkpolicy -n voting-api dns-egress`

- [ ] **Service-specific allow rules configured**
  - Frontend → API:8000 (HTTP)
  - API → PostgreSQL:5432, Redis:6379
  - Consumer → PostgreSQL:5432, Redis:6379
  - See [NETWORK_POLICY.md](NETWORK_POLICY.md) for traffic matrix

- [ ] **Network policies validated**
  - Run `scripts/test-network-policies.sh` with zero failures
  - Verify allowed connections succeed (6 tests)
  - Verify denied connections blocked (3 tests)

- [ ] **Ingress TLS enabled** (if using Ingress)
  - TLS certificates configured (Let's Encrypt, AWS ACM, GCP Managed Certs)
  - HTTP → HTTPS redirect enforced
  - Minimum TLS 1.2, prefer TLS 1.3
  - Verify: `kubectl get ingress -n voting-frontend -o yaml | grep tls`

### 1.3 Application Security (Phase 4.3)

- [ ] **API input validation audited**
  - Pydantic models validate all request bodies
  - SQL injection prevention: 100% asyncpg parameterized queries ($1 placeholders)
  - XSS protection: Pydantic rejects HTML tags in vote options
  - Request size limits: 1MB middleware protection
  - See [api/docs/VALIDATION.md](../api/docs/VALIDATION.md) for 18-scenario audit

- [ ] **SQL injection prevention verified**
  - All 4 database queries use parameterized queries or stored procedures
  - Zero unsafe patterns (f-strings, % formatting, concatenation)
  - Automated scan: `grep -r "f\".*SELECT\|%.*SELECT" api/` returns no matches
  - See Phase 4.3 audit in [CHANGELOG.md](../CHANGELOG.md#security)

- [ ] **CORS origins restricted**
  - Production `values.yaml` has explicit CORS allow list
  - **NOT** `CORS_ORIGINS: "*"` (local development only)
  - Example: `CORS_ORIGINS: "https://voting.example.com"`
  - Verify: `kubectl exec -n voting-api [pod] -- env | grep CORS_ORIGINS`

- [ ] **Secrets externalized** (see Compliance 6.1)

### 1.4 Database Security

- [ ] **PostgreSQL password authentication enforced**
  - No trust authentication in production
  - Use strong passwords (16+ chars, alphanumeric + special)
  - Verify: `kubectl exec -n voting-data postgres-0 -- psql -U postgres -c "SHOW password_encryption"`

- [ ] **Redis authentication enabled** (if required)
  - Set `requirepass` in Redis configuration
  - Update `REDIS_URL` to include password: `redis://:password@redis:6379`
  - Consider Redis ACLs for granular permissions (Redis 6.0+)

- [ ] **Database connections use TLS** (recommended)
  - PostgreSQL: `sslmode=require` in connection string
  - Redis: `rediss://` protocol for TLS
  - Configure TLS certificates in StatefulSets

- [ ] **Database access restricted by NetworkPolicy**
  - Only API and Consumer pods can reach PostgreSQL:5432
  - Only API and Consumer pods can reach Redis:6379
  - Frontend cannot directly access data layer
  - Verify: Run `scripts/test-network-policies.sh`

---

## 2. Reliability Checklist

### 2.1 Health Checks & Probes

- [ ] **Liveness probes configured**
  - API: `GET /health` (checks application health)
  - Frontend: `GET /` (nginx status)
  - Consumer: TCP socket check on port 8080 or custom health endpoint
  - Failure threshold: 3 consecutive failures before restart
  - Verify: `kubectl get pods -n voting-api -o jsonpath='{.items[*].spec.containers[*].livenessProbe}'`

- [ ] **Readiness probes configured**
  - API: `GET /ready` (checks database/Redis connectivity)
  - Frontend: `GET /` (nginx ready)
  - Consumer: Custom readiness check (Redis Stream connection)
  - Initial delay: 10s (allow initialization)
  - Verify: `kubectl get pods -n voting-api -o jsonpath='{.items[*].spec.containers[*].readinessProbe}'`

- [ ] **Startup probes configured** (for slow-starting apps)
  - PostgreSQL: Allow 60s for initialization
  - Redis: Allow 30s for initialization
  - Prevents liveness probe from killing pods during startup

### 2.2 Resource Management

- [ ] **Resource requests defined**
  - API: `requests.memory: 256Mi, requests.cpu: 200m` (baseline from Phase 5.3)
  - Consumer: `requests.memory: 128Mi, requests.cpu: 100m`
  - Frontend: `requests.memory: 64Mi, requests.cpu: 50m`
  - PostgreSQL: `requests.memory: 512Mi, requests.cpu: 250m`
  - Redis: `requests.memory: 256Mi, requests.cpu: 100m`
  - Verify: `kubectl describe pod -n voting-api | grep -A5 Requests`

- [ ] **Resource limits defined**
  - Limits set to 2x requests (API: `limits.memory: 512Mi, limits.cpu: 400m`)
  - Prevents resource starvation and noisy neighbor issues
  - Configure OOMKilled restart policy
  - Verify: `kubectl describe pod -n voting-api | grep -A5 Limits`

- [ ] **Quality of Service (QoS) class verified**
  - Production workloads: **Guaranteed** (requests = limits) or **Burstable** (requests < limits)
  - Avoid **BestEffort** (no requests/limits defined)
  - Verify: `kubectl get pods -n voting-api -o jsonpath='{.items[*].status.qosClass}'`

### 2.3 High Availability

- [ ] **Multiple replicas configured**
  - Frontend: `replicas: 3` (load balanced across nodes)
  - API: `replicas: 3` (horizontal scaling for vote submissions)
  - Consumer: `replicas: 2+` (Redis Stream consumer group parallelism)
  - Verify: `kubectl get deployments -n voting-api -o jsonpath='{.items[*].spec.replicas}'`

- [ ] **Pod anti-affinity configured** (spread across nodes)
  ```yaml
  affinity:
    podAntiAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
              - api
          topologyKey: kubernetes.io/hostname
  ```

- [ ] **Pod Disruption Budgets (PDB) configured**
  - API PDB: `minAvailable: 2` (ensures 2/3 replicas always available during node drains)
  - Consumer PDB: `minAvailable: 1` (ensures continuous vote processing)
  - Verify: `kubectl get pdb -n voting-api`

### 2.4 Data Persistence

- [ ] **Persistent Volumes (PV) configured**
  - PostgreSQL: `volumeClaimTemplates` with `storageClassName` (gp3, pd-ssd, etc.)
  - Redis: Optional PV for AOF/RDB persistence (or use cloud-managed Redis)
  - Verify: `kubectl get pvc -n voting-data`

- [ ] **Storage class supports dynamic provisioning**
  - Cloud providers: `gp3` (AWS), `pd-ssd` (GCP), `managed-premium` (Azure)
  - Reclaim policy: **Retain** (for PostgreSQL data protection)
  - Verify: `kubectl get storageclass`

- [ ] **Backup strategy defined** (see Operations 4.2)

---

## 3. Observability Checklist

### 3.1 Logging

- [ ] **Structured logging implemented**
  - JSON log format (machine-parsable)
  - Include: `timestamp`, `level`, `message`, `service`, `trace_id`, `user_id`
  - API: Python `structlog` library
  - Consumer: JSON logging for vote processing events

- [ ] **Log aggregation configured**
  - Centralized logging (ELK Stack, Loki, CloudWatch, Stackdriver)
  - Retention: 30 days minimum for production logs
  - Indexing: By namespace, pod name, container name, log level

- [ ] **Log levels appropriate**
  - Production default: `INFO` or `WARN`
  - Debug logs disabled (enable dynamically for troubleshooting)
  - Sensitive data redacted (passwords, tokens, PII)

### 3.2 Metrics (Phase 5.3)

- [ ] **Metrics collection enabled**
  - **Lightweight (current):** metrics-server for `kubectl top` (Phase 5.3)
  - **Production (recommended):** kube-prometheus-stack (Prometheus + Grafana)
  - Scrape interval: 15s
  - Retention: 15 days minimum

- [ ] **Application metrics exposed**
  - API: `/metrics` endpoint (Prometheus format)
    - `http_requests_total` (counter)
    - `http_request_duration_seconds` (histogram)
    - `votes_submitted_total` (counter)
  - Consumer: Custom metrics endpoint
    - `votes_processed_total` (counter)
    - `redis_stream_lag` (gauge)
    - `database_insert_duration_seconds` (histogram)
  - Verify: `curl http://api:8000/metrics`

- [ ] **Kubernetes metrics monitored**
  - Pod CPU/memory usage
  - Node resource utilization
  - Persistent volume usage
  - Network traffic (bytes in/out)
  - Use `kubectl top pods --all-namespaces`

- [ ] **Dashboards created**
  - Grafana dashboards for:
    - API latency (P50, P95, P99)
    - Vote submission rate (requests/sec)
    - Consumer lag (pending messages in Redis Stream)
    - Database connection pool usage
    - Error rate (HTTP 5xx responses)

### 3.3 Tracing (Optional)

- [ ] **Distributed tracing configured** (OpenTelemetry, Jaeger, Zipkin)
  - Trace vote flow: Frontend → API → Redis → Consumer → PostgreSQL
  - Identify latency bottlenecks (current P95: 1300ms under load)
  - Sample rate: 10% in production (reduce overhead)

### 3.4 Alerting

- [ ] **Critical alerts defined**
  - Pod crash loop: 3+ restarts in 5 minutes
  - High error rate: 5xx responses > 1% of total requests
  - Consumer lag: Redis Stream pending messages > 1000
  - Database connection failures: PostgreSQL unreachable for 1+ minute
  - Resource saturation: CPU > 80%, Memory > 85%

- [ ] **Alert routing configured**
  - On-call rotation (PagerDuty, Opsgenie, VictorOps)
  - Severity levels: P0 (immediate), P1 (15min), P2 (1hr)
  - Escalation policy defined

---

## 4. Operational Readiness

### 4.1 Deployment Strategy

- [ ] **Rolling update strategy configured**
  - `strategy.type: RollingUpdate`
  - `maxUnavailable: 1` (keep 2/3 replicas running during updates)
  - `maxSurge: 1` (allow 1 extra pod during rollout)
  - Verify: `kubectl get deployment api -n voting-api -o yaml | grep -A5 strategy`

- [ ] **Rollback procedure documented**
  ```bash
  # Rollback to previous revision
  kubectl rollout undo deployment/api -n voting-api

  # Rollback to specific revision
  kubectl rollout undo deployment/api -n voting-api --to-revision=3

  # Check rollout history
  kubectl rollout history deployment/api -n voting-api
  ```

- [ ] **Helm release management**
  - Use Helm 3 for versioned deployments
  - `helm upgrade --install voting-app ./helm -f values-prod.yaml`
  - Rollback: `helm rollback voting-app [REVISION]`
  - History: `helm history voting-app`

### 4.2 Backup & Disaster Recovery

- [ ] **PostgreSQL backups automated**
  - **Option A:** `pg_dump` CronJob (daily full backup, 7-day retention)
    ```bash
    kubectl create cronjob postgres-backup \
      --image=postgres:16 \
      --schedule="0 2 * * *" \
      --namespace=voting-data \
      -- /bin/bash -c "pg_dump -U postgres -d votes > /backup/votes-$(date +%Y%m%d).sql"
    ```
  - **Option B:** Cloud-managed backups (AWS RDS, GCP Cloud SQL, Azure Database)
  - **Option C:** Velero for full cluster backups

- [ ] **Backup storage configured**
  - S3, GCS, Azure Blob Storage for offsite backups
  - Encryption at rest enabled
  - Cross-region replication for DR
  - Verify: Test restore procedure quarterly

- [ ] **Redis persistence configured**
  - **Option A:** AOF (Append-Only File) for durability
  - **Option B:** RDB snapshots (hourly)
  - **Option C:** Cloud-managed Redis (ElastiCache, MemoryStore, Azure Cache)
  - Redis Streams: `XREAD` commands are durable with AOF

- [ ] **Disaster recovery plan documented**
  - RTO (Recovery Time Objective): < 4 hours
  - RPO (Recovery Point Objective): < 1 hour (hourly backups)
  - Runbook: Database restore, DNS failover, cluster rebuild

### 4.3 Upgrade Procedures

- [ ] **Kubernetes version upgrade tested**
  - Test minor version upgrades in staging (e.g., 1.28 → 1.29)
  - Verify NetworkPolicy compatibility (Calico CNI upgrade)
  - Check deprecated APIs: `kubectl api-resources --api-group=policy`

- [ ] **Application version upgrade tested**
  - Blue/Green deployment for zero-downtime upgrades
  - Canary releases: 10% → 50% → 100% traffic
  - Database schema migrations (Alembic, Flyway, Liquibase)

- [ ] **Dependency upgrades tracked**
  - Python dependencies: `pip list --outdated`
  - Node.js dependencies: `npm outdated`
  - Container base images: Track Alpine/Debian security advisories

### 4.4 Access Control & Auditing

- [ ] **RBAC configured** (see Compliance 6.5)

- [ ] **Kubectl access restricted**
  - Developers: Read-only access to logs, pods (no exec/delete)
  - SRE: Full access to voting namespaces (no cluster-admin)
  - CI/CD: ServiceAccount with minimal permissions (deploy, upgrade)

- [ ] **Audit logging enabled**
  - Kubernetes audit logs: Track `kubectl exec`, `delete`, `patch` operations
  - Retention: 90 days minimum
  - See Compliance 6.4 for details

---

## 5. Scalability Checklist

### 5.1 Horizontal Pod Autoscaling (HPA)

- [ ] **HPA configured for API**
  ```yaml
  apiVersion: autoscaling/v2
  kind: HorizontalPodAutoscaler
  metadata:
    name: api
    namespace: voting-api
  spec:
    scaleTargetRef:
      apiVersion: apps/v1
      kind: Deployment
      name: api
    minReplicas: 3
    maxReplicas: 10
    metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  ```
  - Verify: `kubectl get hpa -n voting-api`

- [ ] **HPA configured for Consumer**
  - Scale based on Redis Stream lag (custom metric)
  - Example: Scale up if `XPENDING` count > 100 messages
  - Requires Prometheus Adapter or KEDA (Kubernetes Event-Driven Autoscaling)

- [ ] **Cluster Autoscaler enabled** (cloud providers)
  - AWS: Cluster Autoscaler or Karpenter
  - GCP: GKE Autopilot or Cluster Autoscaler
  - Azure: AKS Cluster Autoscaler
  - Scale nodes when pods are `Pending` due to insufficient resources

### 5.2 Database Scalability

- [ ] **PostgreSQL connection pooling configured**
  - **Option A:** PgBouncer sidecar (connection multiplexing)
  - **Option B:** Application-level pooling (asyncpg `pool_size=20`)
  - Current API setting: `max_pool_size=10` (increase to 20 for production)
  - Verify: `kubectl exec -n voting-data postgres-0 -- psql -U postgres -c "SHOW max_connections"`

- [ ] **PostgreSQL read replicas configured** (optional)
  - For read-heavy workloads (e.g., `/api/results` endpoint)
  - Use PostgreSQL streaming replication or cloud-managed replicas
  - Update API to route `SELECT` queries to read replicas

- [ ] **Redis Cluster configured** (for high throughput)
  - Single Redis instance limit: ~50k ops/sec
  - Redis Cluster: Horizontal partitioning across 3+ nodes
  - Alternative: Cloud-managed Redis (AWS ElastiCache Cluster Mode)

### 5.3 Load Testing & Capacity Planning

- [ ] **Load testing completed** (Phase 5.3 baseline)
  - Sequential: P50 516ms, P95 570ms, 1.92 req/sec
  - Concurrent (10 users): P50 528ms, P95 1300ms, 15.94 req/sec
  - See [session-13-phase5.3-load-testing.md](sessions/2025-11-19-session-13-phase5.3-load-testing.md)

- [ ] **SLOs defined** (Service Level Objectives)
  - Latency: P50 < 200ms, P95 < 500ms, P99 < 1000ms
  - Availability: 99.9% uptime (43 minutes downtime/month)
  - Throughput: 100 req/sec sustained, 500 req/sec peak

- [ ] **Capacity planning documented**
  - Expected traffic: X votes/hour, Y concurrent users
  - Resource projections: CPU/memory per 1000 req/min
  - Cost estimates: Cloud provider pricing (compute, storage, egress)

- [ ] **Advanced load testing** (future)
  - Migrate from Apache Bench to k6 (progressive load profiles)
  - Test scenarios: Ramp-up, spike, soak (sustained load)
  - See [tech-to-review.md](tech-to-review.md#load-testing-tools) for tooling comparison

---

## 6. Compliance Checklist

### 6.1 Secret Management

- [ ] **Kubernetes Secrets not hardcoded**
  - **Production:** Set `secrets.create: false` in `values-prod.yaml`
  - **DO NOT** commit secrets to Git (check with `git log -p | grep -i password`)
  - Verify: `kubectl get secrets -n voting-data -o yaml | grep password` returns base64 (not plaintext)

- [ ] **External secret management configured**
  - **Option A:** HashiCorp Vault (vault-agent injector)
  - **Option B:** AWS Secrets Manager + External Secrets Operator
  - **Option C:** GCP Secret Manager + Workload Identity
  - **Option D:** Azure Key Vault + CSI Secret Store Driver

- [ ] **Secret rotation implemented**
  - PostgreSQL password: Rotate every 90 days
  - Redis password: Rotate every 90 days
  - Automate rotation with secret manager (Vault dynamic secrets)

- [ ] **Secrets encrypted at rest**
  - etcd encryption enabled: `--encryption-provider-config`
  - Cloud providers: Enabled by default (AWS EKS, GCP GKE, Azure AKS)
  - Verify: `kubectl get secrets -n voting-data -o yaml | head -1` shows encrypted data

### 6.2 TLS/mTLS

- [ ] **Ingress TLS configured**
  - TLS certificates for HTTPS (Let's Encrypt, AWS ACM, GCP Managed Certs)
  - Minimum TLS 1.2, prefer TLS 1.3
  - HSTS header: `Strict-Transport-Security: max-age=31536000`

- [ ] **Internal mTLS configured** (optional, service mesh)
  - Istio, Linkerd, or Consul service mesh
  - Encrypt all pod-to-pod traffic (Frontend ↔ API, API ↔ PostgreSQL)
  - Automatic certificate rotation (cert-manager)

- [ ] **Database connections use TLS**
  - PostgreSQL: `sslmode=require` in connection string
  - Redis: `rediss://` protocol (TLS-enabled Redis)

### 6.3 Image Registry Security

- [ ] **Container images from trusted registries**
  - Use private registries (ECR, GCR, ACR, Harbor)
  - Scan images before push: `trivy image --severity HIGH,CRITICAL frontend:0.5.0`
  - Verify image signatures (Cosign, Notary)

- [ ] **ImagePullSecrets configured**
  - Create secret: `kubectl create secret docker-registry regcred --docker-server=...`
  - Reference in Deployment: `imagePullSecrets: [name: regcred]`
  - Verify: `kubectl get serviceaccount default -n voting-api -o yaml | grep imagePullSecrets`

### 6.4 Audit Logging

- [ ] **Kubernetes audit logs enabled**
  - Cloud providers: Enabled by default (view in CloudWatch, Stackdriver, Azure Monitor)
  - Self-managed: Configure `--audit-log-path`, `--audit-policy-file`
  - Track: `kubectl exec`, `delete`, `patch`, `create secret` operations

- [ ] **Application audit logs configured**
  - API: Log all `/vote` submissions (user_id, timestamp, option, IP address)
  - Consumer: Log all vote processing events (message_id, option, new_count)
  - Retention: 90 days minimum for compliance

### 6.5 RBAC (Role-Based Access Control)

- [ ] **Namespace-scoped roles defined**
  - **Developer role:** Read-only access to pods, logs (no exec, delete)
  - **SRE role:** Full access to voting namespaces (no cluster-admin)
  - **CI/CD role:** Deploy, upgrade, rollback (minimal ServiceAccount)

- [ ] **ClusterRoles restricted**
  - Avoid `cluster-admin` for application access
  - Use `view`, `edit` built-in ClusterRoles
  - Custom ClusterRoles for specific permissions

- [ ] **ServiceAccounts configured**
  - API ServiceAccount: Access to ConfigMaps, Secrets in voting-api namespace
  - Consumer ServiceAccount: Access to Secrets in voting-consumer namespace
  - Disable auto-mount: `automountServiceAccountToken: false` (if not needed)

---

## 7. Pre-Deployment Validation

Run all Phase 1-5 validation protocols before production deployment:

### Phase 1: Architecture Validation
- [ ] Verify Kubernetes cluster version (1.28+)
- [ ] Confirm namespace design (4 namespaces: frontend, api, consumer, data)
- [ ] Validate Helm chart structure (templates, values, Chart.yaml)
- [ ] Review ADRs (Architecture Decision Records)

### Phase 2: Application Development Validation
- [ ] API endpoints functional (`/health`, `/ready`, `/vote`, `/results`)
- [ ] Frontend serves static UI (Cats vs Dogs voting buttons)
- [ ] Consumer processes Redis Stream messages
- [ ] Unit tests passing (`pytest api/tests`, `npm test`)

### Phase 3: Event-Driven Architecture Validation
- [ ] Redis Streams configured (stream: `votes`)
- [ ] Consumer group created (`vote-processors`)
- [ ] End-to-end vote flow validated (POST /vote → Redis → Consumer → PostgreSQL → GET /results)
- [ ] Zero consumer lag (`XPENDING` count = 0)

### Phase 4: Security Hardening Validation
- [ ] **Phase 4.1:** Non-root container validation (run `scripts/verify-nonroot.sh`)
- [ ] **Phase 4.2:** Trivy vulnerability scans (0 HIGH/CRITICAL in production images)
- [ ] **Phase 4.3:** API input validation audit (18-scenario matrix, see `api/docs/VALIDATION.md`)
- [ ] **Phase 4.4:** SQL injection prevention audit (100% parameterized queries)
- [ ] **Phase 4.5:** Network policies deployed and tested (run `scripts/test-network-policies.sh`)

### Phase 5: Integration & Performance Validation
- [ ] **Phase 5.1-5.2:** Helm deployment to Kubernetes (all pods Running)
- [ ] **Phase 5.3:** Load testing baseline established (P50, P95, P99 latency)
- [ ] **Phase 5.3:** metrics-server enabled for observability
- [ ] See [PHASE5_VALIDATION.md](PHASE5_VALIDATION.md) for 27 validation checkpoints

---

## 8. Post-Deployment Verification

### 8.1 Smoke Tests (< 5 minutes)

```bash
# 1. Verify all pods running
kubectl get pods --all-namespaces | grep voting

# 2. Test API health
curl -X GET https://voting.example.com/api/health
# Expected: {"status":"ok"}

# 3. Submit test vote
curl -X POST https://voting.example.com/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "cats"}'

# 4. Verify vote counted
curl -X GET https://voting.example.com/api/results
# Expected: {"cats": 1, "dogs": 0}

# 5. Check consumer processing
kubectl logs -n voting-consumer -l app.kubernetes.io/name=consumer --tail=10
# Expected: {"event": "vote_processed", "option": "cats"}
```

### 8.2 Network Policy Verification

```bash
# Run automated connectivity tests
./scripts/test-network-policies.sh

# Expected: ✓ All tests passed! (9 tests)
# - 6 allowed connections succeed
# - 3 denied connections blocked
```

### 8.3 Performance Validation

```bash
# Run baseline load test (10 concurrent users, 100 requests)
ab -n 100 -c 10 -p /tmp/vote.json -T application/json https://voting.example.com/api/vote

# Verify metrics:
# - Complete requests: 100
# - Failed requests: 0
# - P95 latency: < 500ms (SLO)
# - Requests per second: > 15 (baseline)
```

### 8.4 Monitoring Validation

```bash
# 1. Verify metrics collection
kubectl top pods -n voting-api

# 2. Check Prometheus targets (if using kube-prometheus-stack)
kubectl port-forward -n monitoring svc/prometheus 9090:9090
# Visit http://localhost:9090/targets

# 3. Verify Grafana dashboards
kubectl port-forward -n monitoring svc/grafana 3000:80
# Visit http://localhost:3000 (default: admin/prom-operator)

# 4. Test alerts (trigger intentional failure)
kubectl delete pod -n voting-api [api-pod-name]
# Verify alert fires: "Pod crash loop detected"
```

---

## 9. Future Improvements

Reference [tech-to-review.md](tech-to-review.md) for detailed technology evaluations:

### Observability Upgrades (Post-Phase 6)
- [ ] **kube-prometheus-stack** (Prometheus + Grafana)
  - Replace metrics-server with full observability stack
  - Configure dashboards, alerts, recording rules
  - Retention: 15 days (Prometheus), 90 days (Thanos for long-term storage)

- [ ] **Distributed tracing** (OpenTelemetry + Jaeger)
  - Trace vote flow latency across services
  - Identify bottlenecks (current P95: 1300ms under 10 concurrent users)

### Load Testing Evolution
- [ ] **k6** (JavaScript-based load testing)
  - Progressive load profiles (ramp-up, spike, soak tests)
  - Advanced metrics (custom thresholds, trend analysis)
  - See [tech-to-review.md#load-testing-tools](tech-to-review.md#load-testing-tools)

### Network Policy Evolution
- [ ] **Cilium CNI** (L7-aware NetworkPolicies)
  - HTTP method filtering (allow GET, deny DELETE)
  - gRPC/Kafka protocol support
  - eBPF-based performance (lower overhead than Calico)
  - See [tech-to-review.md#cilium-cni](tech-to-review.md#cilium-cni-evaluation)

### Policy-as-Code (Post-Phase 6)
- [ ] **OPA Gatekeeper** or **Kyverno**
  - Enforce policies: "All deployments must have resource limits"
  - Validate: "All images must be from approved registries"
  - Mutate: "Auto-inject securityContext if missing"
  - See [tech-to-review.md#policy-as-code](tech-to-review.md#policy-as-code-options)

### Database Scalability
- [ ] **PostgreSQL read replicas** (for `/api/results` endpoint)
- [ ] **Redis Cluster** (for high-throughput vote submissions)
- [ ] **Cloud-managed data services** (AWS RDS, ElastiCache)

### Service Mesh (Optional)
- [ ] **Istio** or **Linkerd** (mTLS, traffic management, observability)
  - Automatic TLS for pod-to-pod traffic
  - Traffic splitting (canary releases: 10% → 50% → 100%)
  - Circuit breaking, retries, timeouts

---

## Summary

**Production readiness matrix:**

| Category | Critical Items | Validation Protocol |
|----------|---------------|---------------------|
| **Security** | 21 items | Phase 4 validation (4.1-4.5) |
| **Reliability** | 12 items | Health checks, resource limits, HA |
| **Observability** | 10 items | Logging, metrics, tracing, alerting |
| **Operations** | 10 items | Backup, DR, upgrades, RBAC |
| **Scalability** | 8 items | HPA, connection pooling, load testing |
| **Compliance** | 12 items | Secrets, TLS, audit logs, RBAC |
| **Pre-Deployment** | 27 items | Phase 1-5 validation protocols |
| **Post-Deployment** | 4 sections | Smoke tests, network validation, performance, monitoring |

**Total:** 100+ validation checkpoints

---

## References

- [DEPLOYMENT.md](DEPLOYMENT.md) - Local Minikube deployment guide
- [PHASE5_VALIDATION.md](PHASE5_VALIDATION.md) - Comprehensive integration testing protocol
- [NETWORK_POLICY.md](NETWORK_POLICY.md) - Network policy documentation (800+ lines)
- [VULNERABILITY_SCAN.md](VULNERABILITY_SCAN.md) - Container vulnerability scan results
- [api/docs/VALIDATION.md](../api/docs/VALIDATION.md) - API input validation audit (600+ lines)
- [tech-to-review.md](tech-to-review.md) - Technology evaluation and future improvements
- [CHANGELOG.md](../CHANGELOG.md) - Phase 4-5 security and integration work
- [ADR-0001](adr/0001-kubernetes-native-deployment.md) - Architecture decision records

---

**Last Updated:** 2025-11-19 (Phase 6 Documentation)
