# Technologies to Review

Reference links and resources for technologies used in the project.

---

## Gateway API

**What:** Kubernetes native API for ingress, load balancing, and traffic management. Official replacement for Ingress.

**Why:** Provider-agnostic, future-proof, security-focused. Ingress NGINX retired Nov 2025.

**Status:** In use (Phase 2+)

**Resources:**
- Official docs: https://gateway-api.sigs.k8s.io/
- Getting started: https://gateway-api.sigs.k8s.io/guides/
- API reference: https://gateway-api.sigs.k8s.io/reference/spec/
- Migration from Ingress: https://gateway-api.sigs.k8s.io/guides/migrating-from-ingress/
- Rate limiting guide: https://gateway-api.sigs.k8s.io/guides/traffic-splitting/

**Key concepts to review:**
- GatewayClass (infrastructure provider)
- Gateway (load balancer instance)
- HTTPRoute (routing rules)
- ReferenceGrant (cross-namespace access)
- BackendPolicy (rate limiting, timeouts)

---

## Envoy Gateway

**What:** Gateway API implementation using Envoy Proxy. CNCF graduated project.

**Why:** Vendor-neutral, production-ready, excellent performance, rich feature set.

**Status:** Planned implementation (Phase 2+)

**Resources:**
- Official docs: https://gateway.envoyproxy.io/
- Installation: https://gateway.envoyproxy.io/latest/install/
- Quickstart: https://gateway.envoyproxy.io/latest/tasks/quickstart/
- Rate limiting: https://gateway.envoyproxy.io/latest/tasks/traffic/rate-limit/
- Security best practices: https://gateway.envoyproxy.io/latest/tasks/security/
- Helm chart: https://github.com/envoyproxy/gateway/tree/main/charts/gateway-helm

**Key features to explore:**
- Global rate limiting (Redis-backed)
- Request authentication (JWT, OIDC)
- Traffic splitting (A/B testing)
- Observability (metrics, tracing)

**Alternatives considered:**
- Traefik Gateway (simpler, batteries-included)
- Kong Gateway (enterprise features)
- NGINX Gateway Fabric (new, less mature)

---

## Template for New Technologies

```markdown
## [Technology Name]

**What:** [Brief description]

**Why:** [Rationale for adoption]

**Status:** [Planned/In use/Deprecated]

**Resources:**
- Official docs: [URL]
- Key guide: [URL]

**Key concepts to review:**
- [Concept 1]
- [Concept 2]
```
