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

## Kubernetes securityContext

**What:** Security settings for Pods and containers defining privilege and access control. Controls user/group IDs, Linux capabilities, filesystem permissions, and privilege escalation.

**Why:** Essential for production security - enforces least privilege principle, prevents container breakout attacks, ensures non-root execution, and limits attack surface.

**Status:** In use (Phase 1+)

**Resources:**
- Official docs: https://kubernetes.io/docs/tasks/configure-pod-container/security-context/
- Security best practices: https://kubernetes.io/docs/concepts/security/pod-security-standards/
- Pod Security Admission: https://kubernetes.io/docs/concepts/security/pod-security-admission/
- Linux capabilities reference: https://man7.org/linux/man-pages/man7/capabilities.7.html
- OWASP Kubernetes Security: https://cheatsheetseries.owasp.org/cheatsheets/Kubernetes_Security_Cheat_Sheet.html

**Key concepts to review:**
- **runAsNonRoot:** Prevents containers from running as root (UID 0)
- **runAsUser/runAsGroup:** Specifies UID/GID for container process
- **fsGroup:** Sets owning GID for mounted volumes
- **allowPrivilegeEscalation:** Blocks setuid binaries and privilege escalation
- **capabilities:** Controls Linux capabilities (drop ALL, add only what's needed)
- **readOnlyRootFilesystem:** Makes container filesystem read-only
- **seccompProfile:** Restricts syscalls container can make
- **seLinuxOptions:** SELinux context for the container

**Current usage in project:**
- Pod-level: `runAsNonRoot: true`, `runAsUser: 1000`, `fsGroup: 1000`
- Container-level: `allowPrivilegeEscalation: false`, `capabilities: {drop: [ALL]}`
- API (distroless): Runs as UID 65532 (nonroot user)
- Consumer: Runs as UID 1000 (appuser)
- All containers: Non-root, no privilege escalation, all capabilities dropped

**Security impact:**
- Prevents privilege escalation attacks
- Limits damage from container compromise
- Enforces defense in depth
- Meets Pod Security Standards (Restricted level)

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
