# 1. Namespace Security Isolation Strategy

Date: 2025-11-15

## Problem

Initial architecture proposed single Kubernetes namespace (`voting-app`) for all services, which creates security vulnerabilities:

- Frontend could access database secrets
- No enforcement preventing frontend from directly calling PostgreSQL
- Services can communicate freely without restrictions
- Large blast radius if one service is compromised
- Difficult to implement principle of least privilege
- Not production-ready security posture

## Context

While planning Phase 1 (K8s Foundation), we needed to decide namespace strategy. Initial recommendation was single namespace for simplicity, suitable for quick MVPs but insufficient for:

**Security requirements:**
- Zero trust architecture
- Network segmentation
- Secret isolation
- Compliance (SOC2, PCI-DSS)

**Production readiness:**
- Defense in depth
- Least privilege access
- Audit trail

**Future extensibility:**
- Backend for Frontend (BFF) pattern
- Independent layer scaling

**Development approach:**
- Building production patterns from day 0
- Learning industry best practices
- Minikube profiles handle environment isolation (dev/staging/prod)

## Alternatives Considered

### Alternative 1: Single Namespace with Labels

**Description:**
All services in `voting` namespace, use labels to identify layers.

```yaml
namespace: voting
services:
  - frontend (label: layer=presentation)
  - api (label: layer=application)
  - consumer (label: layer=processing)
  - postgres (label: layer=data)
  - redis (label: layer=data)
```

**Pros:**
- Simplest implementation
- Easy service discovery: `http://api:8000`
- Fastest local development
- Less Helm complexity

**Cons:**
- No security boundaries
- Cannot enforce communication rules
- Frontend can access database secrets
- All services can communicate freely
- Not production-ready
- Large blast radius

**Why not chosen:**
Fails security requirements. Labels alone don't provide isolation or enforce policies.

---

### Alternative 2: Hybrid (App + Data Namespaces)

**Description:**
Two namespaces: application layer and data layer.

```yaml
namespace: voting-app
  - frontend
  - api
  - consumer

namespace: voting-data
  - postgres
  - redis
```

**Pros:**
- Simpler than 4 namespaces
- Data layer isolated
- Some security improvement

**Cons:**
- Frontend and API in same namespace (frontend could access API secrets)
- API and consumer in same namespace (both get DB credentials)
- Doesn't prevent inappropriate service communication
- Partial solution to security problem

**Why not chosen:**
Insufficient security boundaries. Doesn't fully solve the problem of service-to-service communication control.

---

### Alternative 3: Environment-Based Namespaces

**Description:**
Separate namespaces per environment.

```yaml
namespace: voting-dev
namespace: voting-staging
namespace: voting-prod
```

**Pros:**
- Environment isolation
- Common pattern

**Cons:**
- Environment already handled by minikube profiles
- Doesn't address layer security
- Same security issues as single namespace
- Wrong axis of separation for our needs

**Why not chosen:**
Solves different problem (environment isolation vs layer isolation). Minikube profiles already handle environments.

---

### Alternative 4: Layer-Based Namespaces (CHOSEN)

**Description:**
Four namespaces corresponding to application layers.

```yaml
namespace: voting-frontend
  - frontend
  - (future: bff)

namespace: voting-api
  - api

namespace: voting-consumer
  - consumer

namespace: voting-data
  - postgres
  - redis
```

**Pros:**
- **Security:** Network policies enforce allowed communication
- **Secret isolation:** Each layer only gets needed credentials
- **Zero trust:** Explicit allow-lists
- **Defense in depth:** Multiple security boundaries
- **Production-ready:** Industry best practice
- **Extensibility:** Easy to add services per layer
- **Compliance:** Clear separation for audits

**Cons:**
- More complex Helm chart
- FQDN service discovery required
- Additional network policy manifests
- Higher learning curve

**Why chosen:**
Best matches security requirements, production readiness goals, and industry best practices. Complexity trade-off is acceptable for security benefits.

## Solution

Implement **layer-based namespace architecture** with network policies.

### Namespaces Created

1. **voting-frontend** - Presentation layer
2. **voting-api** - Application/service layer
3. **voting-consumer** - Event processing layer
4. **voting-data** - Data layer

### Network Policies

Each namespace enforces explicit communication rules:

**Frontend:**
- Egress: ONLY to voting-api namespace
- Ingress: From Ingress controller only
- Secrets: None (API URL config only)

**API:**
- Egress: ONLY to voting-data/redis (NOT postgres)
- Ingress: From voting-frontend only
- Secrets: Redis credentials only

**Consumer:**
- Egress: To voting-data/redis AND voting-data/postgres
- Ingress: None (Job-based)
- Secrets: Redis + PostgreSQL credentials

**Data:**
- Egress: None
- Ingress: Redis (from api + consumer), Postgres (from consumer only)
- Secrets: Master database credentials

### Communication Flow

```
User → Frontend (voting-frontend)
       ↓ (Network Policy: ALLOW)
     API (voting-api)
       ↓ (Network Policy: ALLOW to Redis)
     Redis (voting-data)
       ↓ Stream
     Consumer (voting-consumer)
       ↓ (Network Policy: ALLOW to both)
     PostgreSQL (voting-data)
       ↑ (Network Policy: ALLOW from consumer)
     API (voting-api)
       ↓
     Frontend → User
```

### Service Discovery

FQDN format for cross-namespace calls:
```
<service>.<namespace>.svc.cluster.local
```

Examples:
- `api.voting-api.svc.cluster.local:8000`
- `redis.voting-data.svc.cluster.local:6379`
- `postgres.voting-data.svc.cluster.local:5432`

## Outcome

**What changed:**
- Created ADR-0004 documenting layer-based namespace architecture
- Updated Phase 1 tasks to include:
  - Create 4 namespaces
  - Define network policies per namespace
  - Setup ServiceAccounts per namespace
  - Configure secret distribution strategy

**Architecture benefits:**
- Production-ready security from day 0
- Clear separation of concerns
- Enforceable communication paths
- Secret isolation per layer

**Follow-up actions:**
- [ ] Implement Helm templates for namespaces
- [ ] Define all network policies
- [ ] Test network policy enforcement
- [ ] Document service discovery patterns

**Lessons learned:**
- Security should drive architecture decisions, not just convenience
- Namespace boundaries are powerful security controls
- Single namespace is anti-pattern for production
- Learning curve of network policies is worth the security benefits
- Production patterns from day 0 avoids costly refactoring later

## References

- ADR-0004: Layer-Based Namespace Security (docs/adr/0004-layer-based-namespace-security.md)
- Session: docs/sessions/2025-11-15-session-01-project-planning.md
- [Kubernetes Network Policies](https://kubernetes.io/docs/concepts/services-networking/network-policies/)
- [Zero Trust Security](https://www.nist.gov/publications/zero-trust-architecture)
