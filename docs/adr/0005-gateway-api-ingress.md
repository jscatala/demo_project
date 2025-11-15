# 5. Gateway API with Envoy Gateway for Ingress

Date: 2025-11-15

## Status

Accepted

## Context

The project requires a robust, provider-agnostic ingress solution with built-in rate limiting and security features. Initial consideration was given to the widely-used Ingress NGINX controller.

Critical developments have changed the landscape:

- **Ingress NGINX retirement**: Kubernetes SIG Network announced retirement on November 11, 2025, with maintenance ending March 2026
- **Security vulnerabilities**: CVEs discovered in March 2025 allowing cluster takeover via "snippets" annotations
- **Maintainer shortage**: Project suffered from insufficient maintainers, with only 1-2 developers maintaining it in their spare time
- **Provider-agnostic requirement**: ADR-0001 mandates deployment must work across any Kubernetes provider
- **Security-first approach**: Project principles require security built-in from the start

The Kubernetes community officially recommends migration to Gateway API as the modern replacement for Ingress.

## Decision

Adopt **Gateway API** as the standard for ingress traffic management, implemented using **Envoy Gateway**.

**Implementation:**
- Use Gateway API resources: `GatewayClass`, `Gateway`, `HTTPRoute`
- Deploy Envoy Gateway as the Gateway API implementation
- Configure rate limiting via Gateway API policies
- Leverage ReferenceGrant for cross-namespace access control

## Consequences

### Positive

- **Future-proof**: Gateway API is the official Kubernetes ingress standard going forward
- **Security-focused**: Modern design incorporates lessons learned from Ingress vulnerabilities
- **Provider-agnostic**: Works across any Kubernetes distribution (aligns with ADR-0001)
- **Active development**: Strong community support, CNCF backing
- **Rich feature set**: Native support for rate limiting, traffic splitting, header manipulation
- **Envoy maturity**: CNCF graduated project, battle-tested in production at scale
- **Vendor-neutral**: Not tied to any commercial vendor or cloud provider
- **Extensibility**: Policy attachment model allows custom extensions

### Negative

- **Newer API**: Less mature ecosystem than Ingress (fewer examples, tutorials)
- **Learning curve**: Team must learn new resource types and concepts
- **Migration path**: Future changes from legacy Ingress would require rewriting manifests
- **Tooling maturity**: Some tools may not fully support Gateway API yet
- **Documentation gaps**: Community knowledge base smaller than Ingress

### Neutral

- **Different resource model**: Gateway/HTTPRoute vs Ingress requires different thinking
- **Namespace separation**: Gateway in infra namespace, routes in app namespaces (by design)
- **Additional CRDs**: Requires installing Gateway API CRDs + Envoy Gateway
- **Configuration complexity**: More resources than simple Ingress, but more powerful

## Alternatives Considered

### Alternative 1: Continue with Ingress NGINX

**Description**: Use the traditional Ingress NGINX controller despite retirement announcement.

**Why rejected**:
- Officially retired with no security updates after March 2026
- Known critical security vulnerabilities (CVE-2025-*)
- Insufficient maintainers to address future issues
- Against project's security-first principles
- Technical debt from day one

### Alternative 2: Traefik (Ingress mode)

**Description**: Use Traefik Proxy as an Ingress controller.

**Why rejected**:
- While well-maintained, still uses legacy Ingress API
- Does not align with Kubernetes' official direction (Gateway API)
- Traefik also supports Gateway API, so prefer that mode
- Would require future migration to Gateway API anyway

### Alternative 3: Cloud Provider Controllers

**Description**: Use cloud-specific controllers (AWS ALB, GCP GCLB, Azure AppGW).

**Why rejected**:
- Violates ADR-0001 provider-agnostic requirement
- Locks deployment to specific cloud providers
- Different implementations across providers
- Cannot run locally (minikube/kind) for development

### Alternative 4: Traefik Gateway API Implementation

**Description**: Use Traefik as the Gateway API implementation instead of Envoy Gateway.

**Why not chosen** (still viable alternative):
- Envoy has stronger ecosystem and production track record
- Envoy graduated CNCF project (higher maturity bar)
- Envoy is reference implementation for many Gateway API features
- Both are good choices; Envoy selected for proven scale and community

## References

- [Ingress NGINX Retirement Announcement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/) (Nov 11, 2025)
- [Gateway API Official Documentation](https://gateway-api.sigs.k8s.io/)
- [Envoy Gateway Documentation](https://gateway.envoyproxy.io/)
- [Gateway API Migration Guide](https://gateway-api.sigs.k8s.io/guides/migrating-from-ingress/)
- Related ADRs: ADR-0001 (Kubernetes-native deployment)
- Technology review resources: `docs/tech-to-review.md`
