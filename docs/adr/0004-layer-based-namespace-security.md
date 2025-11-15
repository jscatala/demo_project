# 4. Layer-Based Namespace Architecture for Security

Date: 2025-11-15

## Status

Accepted

## Context

The application requires a deployment strategy that balances developer experience with production-grade security. Initial consideration of a single namespace approach raised security concerns:

**Security Issues with Single Namespace:**
- Frontend could access database secrets
- No enforcement of allowed communication paths
- Services can communicate freely without restrictions
- Direct frontend-to-database communication possible (violates separation of concerns)
- Large blast radius if one service is compromised
- Difficult to implement principle of least privilege

**Production Requirements:**
- Zero trust architecture
- Network segmentation between layers
- Secret isolation per service role
- Compliance readiness (SOC2, PCI-DSS)
- Defense in depth security model
- Audit trail for service-to-service communication

**Future Extensibility:**
- Room for Backend for Frontend (BFF) pattern
- Ability to scale individual layers independently
- Support for multi-tenant scenarios

## Decision

Implement **layer-based namespace architecture** with four isolated namespaces corresponding to application layers:

### Namespace Structure

**1. `voting-frontend` - Presentation Layer**
- Services: frontend (React), future BFF
- Network access: Can ONLY call voting-api
- Secrets: None (API endpoint configuration only)

**2. `voting-api` - Application/Service Layer**
- Services: api (FastAPI)
- Network access: Can call Redis in voting-data (NOT PostgreSQL)
- Secrets: Redis connection credentials only

**3. `voting-consumer` - Event Processing Layer**
- Services: consumer (K8s Job)
- Network access: Can call Redis + PostgreSQL in voting-data
- Secrets: Redis + PostgreSQL connection credentials

**4. `voting-data` - Data Layer**
- Services: PostgreSQL (StatefulSet), Redis (StatefulSet)
- Network access: Ingress only from authorized namespaces
- Secrets: Master database credentials

### Communication Flow

```
User (HTTPS)
  ↓
[voting-frontend/frontend]
  ↓ HTTP (Network Policy: ALLOW from voting-frontend to voting-api)
[voting-api/api]
  ↓ Redis XADD (Network Policy: ALLOW from voting-api to voting-data/redis)
[voting-data/redis]
  ↓ Stream consumption
[voting-consumer/consumer]
  ↓ SQL INSERT (Network Policy: ALLOW from voting-consumer to voting-data/postgres)
[voting-data/postgres]
  ↑ SQL SELECT (Network Policy: ALLOW from voting-consumer to voting-data/postgres)
[voting-api/api]
  ↓ HTTP response
[voting-frontend/frontend]
  ↓ Display
User
```

### Network Policies

Each namespace enforces explicit allow-lists:

**voting-frontend:**
```yaml
egress:
  - to: voting-api namespace (port 8000)
  - to: Internet (for CDN, external APIs)
ingress:
  - from: Ingress controller
```

**voting-api:**
```yaml
egress:
  - to: voting-data/redis (port 6379)
  # NOT allowed to voting-data/postgres
ingress:
  - from: voting-frontend namespace
```

**voting-consumer:**
```yaml
egress:
  - to: voting-data/redis (port 6379)
  - to: voting-data/postgres (port 5432)
ingress:
  - none (Job-based, no inbound traffic)
```

**voting-data:**
```yaml
egress:
  - none (databases don't initiate connections)
ingress:
  - redis: from voting-api, voting-consumer
  - postgres: from voting-consumer ONLY
```

### Service Discovery

Services use Kubernetes DNS with FQDN for cross-namespace calls:

```
<service>.<namespace>.svc.cluster.local
```

**Examples:**
- Frontend → API: `http://api.voting-api.svc.cluster.local:8000`
- API → Redis: `redis://redis.voting-data.svc.cluster.local:6379`
- Consumer → PostgreSQL: `postgresql://postgres.voting-data.svc.cluster.local:5432/votes`

## Consequences

### Positive

**Security:**
- **Zero Trust:** Explicit allow-lists enforce least privilege
- **Secret Isolation:** Services only access credentials they need
- **Attack Surface Reduction:** Compromised frontend cannot access databases
- **Defense in Depth:** Multiple security boundaries (namespace + network policy + RBAC)
- **Compliance Ready:** Clear separation supports audit requirements

**Production Readiness:**
- **Industry Best Practice:** Follows microservices security patterns
- **Scalability:** Each layer scales independently
- **Monitoring:** Namespace-level metrics and logging
- **RBAC:** Fine-grained access control per namespace

**Architectural:**
- **Clear Boundaries:** Each layer has defined responsibilities
- **Extensibility:** Easy to add services within namespaces (e.g., BFF)
- **Testability:** Can test network policies independently

### Negative

**Complexity:**
- **Service Discovery:** Requires FQDN instead of simple service names
- **Helm Chart:** More complex with multiple namespaces
- **Network Policies:** Additional manifests to manage
- **Debugging:** Cross-namespace issues harder to trace

**Development Experience:**
- **Local Setup:** More initial configuration
- **Learning Curve:** Developers need to understand network policies
- **Troubleshooting:** Network policy errors can be obscure

**Operational:**
- **Secret Management:** Need strategy for distributing secrets across namespaces
- **Monitoring:** More complex observability setup
- **Resource Overhead:** Multiple namespaces consume more K8s resources

### Neutral

**Service Communication:**
- FQDN format is more verbose but explicit
- Cross-namespace latency is negligible in-cluster

**Testing:**
- Can verify network policies enforce security
- Requires additional integration tests

## Implementation Details

### Helm Chart Structure

```
helm/templates/
├── namespaces.yaml              # Create all 4 namespaces
├── network-policies/
│   ├── frontend-netpol.yaml
│   ├── api-netpol.yaml
│   ├── consumer-netpol.yaml
│   └── data-netpol.yaml
├── frontend/
│   ├── deployment.yaml
│   └── service.yaml
├── api/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── secret.yaml              # Redis creds only
├── consumer/
│   ├── job.yaml
│   └── secret.yaml              # Redis + PostgreSQL creds
└── data/
    ├── postgres-statefulset.yaml
    ├── redis-statefulset.yaml
    └── secret.yaml              # Master DB creds
```

### Secret Distribution Strategy

**Option 1: Duplicate Secrets** (Simple, chosen for MVP)
- Create secrets in each namespace that needs them
- Helm values provide credentials once
- Templates duplicate into multiple namespaces

**Option 2: External Secrets Operator** (Future enhancement)
- Single source of truth (Vault, AWS Secrets Manager)
- Automated synchronization to namespaces
- Better secret rotation

### Network Policy Validation

```bash
# Test enforcement (should fail)
kubectl exec -n voting-frontend frontend-pod -- \
  curl postgres.voting-data:5432

# Test allowed paths (should succeed)
kubectl exec -n voting-api api-pod -- \
  redis-cli -h redis.voting-data ping
```

## Alternatives Considered

### Alternative 1: Single Namespace with Labels

**Approach:**
- All services in `voting-app` namespace
- Use labels for layer identification
- No network policies

**Pros:**
- Simplest implementation
- Easy service discovery (`http://api:8000`)
- Fastest local development

**Rejected because:**
- No security boundaries
- Cannot enforce communication rules
- Frontend can access database secrets
- Not production-ready

### Alternative 2: Hybrid (App + Data Namespaces)

**Approach:**
- `voting-app`: frontend, api, consumer
- `voting-data`: postgres, redis

**Pros:**
- Simpler than 4 namespaces
- Data layer isolated

**Rejected because:**
- Still allows frontend → consumer direct communication
- API and consumer in same namespace (both have DB access)
- Doesn't prevent frontend from accessing consumer secrets

### Alternative 3: Environment-Based Namespaces

**Approach:**
- `voting-dev`, `voting-staging`, `voting-prod`
- All services within each environment namespace

**Rejected because:**
- Environment isolation handled by minikube profiles
- Doesn't provide layer security
- Same issues as single namespace

## Migration Path

**Phase 1 (MVP):** Implement 4 namespaces with basic network policies
**Phase 2:** Add ServiceMesh (Istio/Linkerd) for mTLS and advanced policies
**Phase 3:** Integrate External Secrets Operator for secret management
**Phase 4:** Add service-level RBAC and OPA policies

## References

- Issue-0001: Namespace Security Isolation (docs/issues/0001-namespace-security-isolation.md)
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Zero Trust Architecture](https://www.nist.gov/publications/zero-trust-architecture)
- [Defense in Depth](https://csrc.nist.gov/glossary/term/defense_in_depth)
- ADR-0001: Kubernetes-Native Deployment
