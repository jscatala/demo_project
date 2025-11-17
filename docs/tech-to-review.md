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

## Configuration Management Server

**What:** Centralized configuration service for microservices (e.g., Spring Cloud Config Server, Consul, etcd, custom service)

**Why:** Enables hot reload of configuration without pod restarts, centralized config management, environment-agnostic deployments, versioned configuration history

**Status:** Future improvement (Phase 3+)

**Current approach:**
- Using K8s ConfigMap mounted as runtime config.js
- Frontend fetches `/config.js` before React initialization
- Updates require ConfigMap edit + pod restart

**Benefits of configuration server:**
- Hot reload without pod restart (frontend polls for changes)
- Centralized dashboard for all service configs
- Configuration versioning and rollback
- Environment promotion (dev → staging → prod)
- Audit trail of configuration changes
- Dynamic feature flags

**Potential implementations:**
- **Consul:** Full service mesh + config + service discovery
- **Spring Cloud Config Server:** Config-focused, Git-backed
- **etcd:** Lightweight, K8s-native (already used by K8s)
- **Custom service:** Lightweight Go/Python service with API + UI

**Trade-offs:**
- ➕ Better developer experience
- ➕ No pod restarts for config changes
- ➕ Centralized management
- ➖ Additional infrastructure component
- ➖ New point of failure (needs HA)
- ➖ Increased complexity

**Resources:**
- Spring Cloud Config: https://spring.io/projects/spring-cloud-config
- Consul: https://www.consul.io/docs/dynamic-app-config
- etcd: https://etcd.io/docs/
- 12-Factor Config: https://12factor.net/config

**Decision context:**
- Deferred to keep Phase 3 focused on MVP
- ConfigMap + runtime config.js sufficient for current scale
- Revisit when managing 5+ microservices or need hot reload

---

## Server-Sent Events (SSE)

**What:** HTTP-based server push protocol for real-time one-way updates (server → client). Native browser API via EventSource.

**Why:** Enables real-time vote updates without polling. Simpler than WebSockets for one-way communication, automatic reconnection, HTTP/2 compatible.

**Status:** Future improvement (Post-Phase 3)

**Current approach:**
- Results fetched once on mount via `useResults` hook
- Manual refetch after voting
- No live updates from other users' votes

**Benefits of SSE:**
- Real-time vote updates from all users (live leaderboard)
- Lower network overhead vs polling (1 connection vs repeated requests)
- Built-in reconnection handling
- Better user engagement
- Server push eliminates polling latency

**Implementation requirements:**
- **Backend:** FastAPI SSE endpoint (`GET /api/events`)
  - Stream vote events from Redis Streams
  - Connection pool management
  - Graceful shutdown handling
- **Frontend:** EventSource client in `useResults` hook
  - Auto-reconnect on connection drop
  - Fallback to polling if SSE unavailable
  - Error boundary for connection failures

**Trade-offs:**
- ➕ Real-time UX without polling waste
- ➕ Simpler than WebSockets for one-way data
- ➕ Built-in reconnection
- ➖ Backend holds open connections (memory cost)
- ➖ Browser limit: 6 SSE per domain
- ➖ Scalability concerns (10k users = 10k connections)
- ➖ Requires sticky sessions or Redis pub/sub for multi-pod
- ➖ Some proxies/firewalls block SSE
- ➖ One-way only (can't send from client without separate request)

**Alternatives:**
- **Short polling (5s interval):** Simpler, works everywhere, higher latency
- **Long polling:** Middle ground, more complex than SSE
- **WebSockets:** Two-way, overkill for read-only updates
- **GraphQL subscriptions:** Too heavy for this use case

**Resources:**
- MDN EventSource: https://developer.mozilla.org/en-US/docs/Web/API/EventSource
- FastAPI SSE: https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse
- SSE specification: https://html.spec.whatwg.org/multipage/server-sent-events.html
- Best practices: https://www.smashingmagazine.com/2018/02/sse-websockets-data-flow-http2/

**Decision context:**
- Deferred to keep Phase 3 MVP focused
- Current refetch-on-vote is acceptable for demo
- Revisit if users demand live leaderboard
- Consider for portfolio showcase of real-time patterns

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
