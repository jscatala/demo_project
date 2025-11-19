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

## Trivy

**What:** Open-source container security scanner that detects vulnerabilities (CVEs), misconfigurations, secrets, and license issues in container images, filesystems, and Kubernetes manifests.

**Why:** Automated security validation for container images. Catches security issues before deployment, integrates into CI/CD pipelines, provides actionable remediation guidance.

**Status:** In use (Phase 4+)

**Resources:**
- Official docs: https://aquasecurity.github.io/trivy/
- Installation: https://aquasecurity.github.io/trivy/latest/getting-started/installation/
- CI/CD integration: https://aquasecurity.github.io/trivy/latest/tutorials/integrations/
- Docker Hub: https://hub.docker.com/r/aquasec/trivy

**Key features:**
- **Vulnerability scanning:** Detects CVEs in OS packages and application dependencies
- **Misconfiguration detection:** Validates container/K8s security settings (UID 0, capabilities, etc.)
- **Secret detection:** Finds hardcoded credentials, API keys, tokens
- **License scanning:** Identifies license compliance issues in dependencies
- **SBOM generation:** Creates Software Bill of Materials for supply chain security

**Current usage in project:**
- Docker-based execution (no local installation required)
- Scans all 3 service images: frontend, api, consumer
- Focus: Misconfiguration detection (non-root validation)
- Severity filter: HIGH and CRITICAL only
- Exit code 1 on findings (fails CI pipeline)
- Integrated in `scripts/verify-nonroot.sh`

**Scan types:**
```bash
# Misconfiguration scan (used in Phase 4.1)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image \
  --scanners misconfig \
  --severity HIGH,CRITICAL \
  frontend:0.5.0

# Vulnerability scan (CVEs in dependencies)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image \
  --scanners vuln \
  --severity HIGH,CRITICAL \
  frontend:0.5.0

# Combined scan (misconfig + vulnerabilities + secrets)
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy:latest image \
  --severity HIGH,CRITICAL \
  frontend:0.5.0
```

**Alternatives considered:**
- **Snyk:** Commercial, excellent vulnerability DB, better developer UX, requires account
- **Grype (Anchore):** Open-source, fast, good vulnerability detection, less feature-rich
- **Clair:** CoreOS project, good for registry integration, complex setup
- **Docker Scout:** Docker native, easy to use, limited to Docker Hub images

**Why Trivy:**
- ✅ 100% open-source (Apache 2.0)
- ✅ Zero configuration (works out of box)
- ✅ Comprehensive (vulns + misconfig + secrets + SBOM)
- ✅ Fast scanning (parallel processing)
- ✅ No external service required (runs locally)
- ✅ Docker-based (no local install needed)
- ✅ CI/CD friendly (exit codes, JSON output)
- ✅ Active maintenance (Aqua Security)

**Trade-offs:**
- ➕ Free and open-source
- ➕ No account/registration required
- ➕ Offline mode supported (download vulnerability DB once)
- ➕ Multiple output formats (table, JSON, SARIF, CycloneDX)
- ➕ K8s manifest scanning (detect issues before apply)
- ➖ Vulnerability DB requires periodic updates (auto-updates by default)
- ➖ False positives possible (can suppress with .trivyignore)
- ➖ Larger image size vs specialized tools (~400MB)

**Integration points:**
- **Pre-commit hooks:** Scan images before git push
- **GitHub Actions:** `aquasecurity/trivy-action@master`
- **GitLab CI:** Native integration via Docker
- **Kubernetes admission controller:** Trivy Operator scans workloads at runtime
- **Docker registry:** Scan on push (Harbor, ECR, ACR, GCR)

**Example output:**
```
frontend:0.5.0 (alpine 3.19.1)
===================================
Total: 0 (HIGH: 0, CRITICAL: 0)
```

**Decision context:**
- Adopted in Phase 4.1 for non-root container validation
- Chosen over Snyk for zero-cost, no-account requirement
- Docker-based execution aligns with project's "no local install" philosophy
- Can expand to vulnerability scanning in Phase 4.4 (same tool)
- Consider Trivy Operator for runtime K8s scanning in production

**Future enhancements:**
- Expand to vulnerability scanning (CVE detection)
- Add secret scanning (detect hardcoded credentials)
- Integrate in CI/CD pipeline (GitHub Actions)
- Generate SBOM for supply chain security compliance
- Deploy Trivy Operator in K8s for runtime protection

---

## Policy-as-Code (OPA Gatekeeper / Kyverno)

**What:** Kubernetes admission controllers that enforce security and operational policies declaratively. Intercepts resource creation/updates before admission, validates against policies, rejects violations automatically.

**Why:** Automates security enforcement at cluster level. Eliminates manual reviews, prevents misconfigurations, provides zero-trust validation, scales policy compliance across all deployments.

**Status:** Future improvement (Post-Phase 4)

**Current approach:**
- Manual Dockerfile audits for security settings
- Manual `docker run` tests to verify non-root execution
- No enforcement mechanism - relies on developer diligence
- Reactive detection (find issues after merge/deploy)

**Benefits of Policy-as-Code:**
- **Proactive prevention:** Blocks insecure configs before deployment (not after)
- **Zero-trust enforcement:** Every deployment validated, no human review needed
- **Self-documenting:** Policy definitions = security standards in code
- **Audit mode:** Can warn without blocking (good for gradual adoption)
- **Git-versioned:** Policies in version control, reviewed like code
- **Compliance:** Enforces Pod Security Standards, CIS benchmarks, custom org rules

**Policy examples for this project:**
- Block containers running as root (runAsNonRoot: true required)
- Require all Linux capabilities dropped
- Enforce read-only root filesystem
- Mandate resource limits (prevent resource exhaustion)
- Registry whitelist (only pull from approved registries)
- Required labels (app, component, version)
- Network policies required for each namespace

**Implementation options:**

### OPA Gatekeeper (Recommended for complex policies)
- **Language:** Rego (declarative, expressive, reusable)
- **CNCF status:** Graduated (production-ready)
- **Strengths:** Complex logic, constraint templates, audit mode, custom violations
- **Learning curve:** Moderate (new language)

**Resources:**
- Official docs: https://open-policy-agent.github.io/gatekeeper/
- Policy library: https://github.com/open-policy-agent/gatekeeper-library
- Rego playground: https://play.openpolicyagent.org/
- OPA docs: https://www.openpolicyagent.org/docs/latest/

**Key concepts:**
- ConstraintTemplate (reusable policy definition)
- Constraint (policy instance with parameters)
- Audit mode (dry-run, log violations without blocking)
- Mutation (auto-fix non-compliant configs)

### Kyverno (Alternative for YAML-native teams)
- **Language:** YAML (no new syntax to learn)
- **CNCF status:** Incubating
- **Strengths:** K8s-native, easy adoption, mutation rules, policy reports
- **Learning curve:** Low (if familiar with K8s YAML)

**Resources:**
- Official docs: https://kyverno.io/docs/
- Policy library: https://kyverno.io/policies/
- Installation: https://kyverno.io/docs/installation/
- Best practices: https://kyverno.io/docs/writing-policies/best-practices/

**Key concepts:**
- ClusterPolicy vs Policy (cluster-wide vs namespaced)
- Validate, Mutate, Generate rules
- ValidationFailureAction (Enforce vs Audit)
- Policy reports (compliance dashboard)

**Trade-offs:**
- ➕ Zero-trust security enforcement
- ➕ Eliminates manual security reviews
- ➕ Prevents regressions (future deployments auto-validated)
- ➕ Enables self-service deployments safely
- ➕ Documents security requirements as code
- ➖ Additional cluster component (resource overhead)
- ➖ Learning curve (Rego for OPA, policies for Kyverno)
- ➖ Can block legitimate deployments if too strict
- ➖ Debugging policy violations requires understanding policy language

**Decision context:**
- Deferred until Phase 4 validation proves manual approach doesn't scale
- Current 3 services manageable with script-based validation
- Revisit when:
  - Team grows (multiple developers, less security expertise)
  - Service count increases (5+ microservices)
  - Compliance audit required (automated evidence needed)
  - CI/CD maturity increases (policy-as-code fits GitOps workflow)

**Recommended starting point:**
1. Install Gatekeeper in audit mode (log violations, don't block)
2. Deploy 2-3 policies from library (non-root, no privilege escalation)
3. Review violations for 1 week, adjust policies
4. Switch to enforce mode after validation
5. Expand policy coverage incrementally

---

## Property-Based Testing (Hypothesis / Schemathesis)

**What:** Testing methodology that generates hundreds/thousands of test inputs automatically based on property specifications, rather than writing explicit test cases. Discovers edge cases humans miss.

**Why:** Dramatically increases test coverage with less code. Finds unexpected bugs, edge cases, and validation gaps automatically. Complements example-based testing.

**Status:** Future improvement (Post-Phase 4.2)

**Current approach:**
- Example-based tests (explicit test cases like `test_submit_vote_cats_success`)
- Manual edge case enumeration (SQL injection, XSS, null, empty string)
- ~30% validation coverage (6/18 scenarios in VALIDATION.md)
- Human-identified edge cases only

**Benefits of property-based testing:**
- **Automatic edge case discovery:** Generates thousands of inputs (random strings, special chars, boundary values)
- **Regression prevention:** Shrinks failing inputs to minimal reproducible example
- **Less test code:** One property test = hundreds of example tests
- **Finds unexpected bugs:** Discovers cases developers didn't think of
- **Complements existing tests:** Works alongside example-based tests

**Implementation options:**

### Hypothesis (General property-based testing)
- **Language:** Python
- **Use case:** Unit test property validation (any Python code)
- **Strengths:** Mature, excellent shrinking, integrates with pytest

**Resources:**
- Official docs: https://hypothesis.readthedocs.io/
- Quickstart: https://hypothesis.readthedocs.io/en/latest/quickstart.html
- Strategies: https://hypothesis.readthedocs.io/en/latest/data.html
- FastAPI integration: https://hypothesis.readthedocs.io/en/latest/numpy.html

**Example for this project:**
```python
from hypothesis import given, strategies as st
import pytest

@given(option=st.text())
def test_vote_rejects_non_literal_values(option):
    """Property: Any string except 'cats'/'dogs' should return 422."""
    if option not in ["cats", "dogs"]:
        response = client.post("/api/vote", json={"option": option})
        assert response.status_code == 422
```

**Key concepts:**
- `@given` decorator: Defines input generators
- Strategies: `st.text()`, `st.integers()`, `st.lists()`, etc.
- Shrinking: Automatically finds minimal failing input
- Stateful testing: Test sequences of operations

### Schemathesis (API-specific fuzzing)
- **Language:** Python (CLI + library)
- **Use case:** API fuzzing from OpenAPI schema
- **Strengths:** Auto-generates tests from spec, finds contract violations

**Resources:**
- Official docs: https://schemathesis.readthedocs.io/
- Getting started: https://schemathesis.readthedocs.io/en/stable/getting-started.html
- FastAPI integration: https://schemathesis.readthedocs.io/en/stable/integration.html#fastapi
- CLI usage: https://schemathesis.readthedocs.io/en/stable/cli.html

**Example for this project:**
```bash
# Generate OpenAPI schema from FastAPI
python -c "import json; from main import app; print(json.dumps(app.openapi()))" > openapi.json

# Fuzz API with 1000 test cases
schemathesis run openapi.json \
  --base-url http://localhost:8000 \
  --checks all \
  --hypothesis-max-examples=1000
```

**Checks performed:**
- `not_a_server_error`: No 500 errors
- `status_code_conformance`: Responses match OpenAPI spec
- `content_type_conformance`: Correct Content-Type headers
- `response_schema_conformance`: Response bodies valid
- `response_headers_conformance`: Headers match spec

**Key concepts:**
- Schema-driven testing: Uses OpenAPI/Swagger spec
- Hypothesis-powered: Built on top of Hypothesis
- Stateful API testing: Test operation sequences
- CI/CD integration: Exit codes for pass/fail

**Trade-offs:**
- ➕ Finds edge cases humans miss (unicode, special chars, boundary values)
- ➕ Less test code (one property = 1000s of examples)
- ➕ Automatic shrinking (minimal failing input)
- ➕ Great for regression testing (reproduces known failures)
- ➕ Discovers undocumented behavior
- ➖ Non-deterministic (can fail randomly, requires seeding for CI)
- ➖ Slower execution (generates many inputs)
- ➖ Harder to debug (failing input may be obscure)
- ➖ Requires learning property-thinking (different from example-based)
- ➖ Can't replace all example tests (some scenarios too specific)

**Current project fit:**

**Good candidates for property-based testing:**
1. **Vote validation** (Hypothesis)
   - Property: "Any string except 'cats'/'dogs' returns 422"
   - Generates: random strings, unicode, special chars, SQL/XSS payloads
   - Current: 6 manual example tests → 1 property test (1000+ examples)

2. **API fuzzing** (Schemathesis)
   - Test all endpoints against OpenAPI schema
   - Discovers: malformed requests, missing validation, contract violations
   - Current: Manual test writing → Automatic from schema

3. **Results calculation** (Hypothesis)
   - Property: "Percentages always sum to 100 (or 0 if empty)"
   - Generates: random vote counts, edge cases (0, MAX_INT, negatives)
   - Current: 2 manual example tests → 1 property test

**Not good for:**
- Business logic (too specific, example tests better)
- Integration tests (deterministic flows preferred)
- UI tests (user interactions are sequential, not random)

**Adoption path:**
1. **Phase 4.2 completion:** Add Hypothesis to requirements-test.txt
2. **Convert existing edge cases:** Rewrite manual tests as properties
3. **Add Schemathesis CLI:** Run in CI for regression detection
4. **Measure impact:** Track bugs found vs maintenance cost
5. **Expand gradually:** Add properties for new endpoints

**Example: Convert manual tests to property-based**

**Before (manual):**
```python
def test_sql_injection():
    assert client.post("/api/vote", json={"option": "cats' OR 1=1"}).status_code == 422

def test_xss():
    assert client.post("/api/vote", json={"option": "<script>alert(1)</script>"}).status_code == 422

def test_empty_string():
    assert client.post("/api/vote", json={"option": ""}).status_code == 422
```

**After (property-based):**
```python
@given(option=st.text())
def test_non_literal_vote_rejected(option):
    assume(option not in ["cats", "dogs"])  # Exclude valid inputs
    response = client.post("/api/vote", json={"option": option})
    assert response.status_code == 422
    assert "Input should be 'cats' or 'dogs'" in response.text
```

**Result:** 3 manual tests → 1 property test generating 100+ examples (including SQL/XSS/empty/unicode/etc.)

**Alternatives:**
- **Manual fuzzing:** Write custom input generators (reinventing Hypothesis)
- **API contract testing (Pact):** Consumer-driven contracts (different use case)
- **Mutation testing (mutmut):** Tests code coverage quality, not input validation

**Decision context:**
- Deferred from Phase 4.2 to keep focus on audit + manual edge cases
- Current: 67% validation gap (12 untested scenarios)
- Hypothesis could cover all 12 gaps with 1-2 property tests
- Revisit after Phase 4.2 lifespan mocking fixed (test infrastructure ready)
- Evaluate ROI: bugs found vs learning curve + maintenance

**Recommended starting point:**
```bash
# 1. Install Hypothesis
pip install hypothesis

# 2. Write first property test (5 min)
@given(option=st.text(min_size=1, max_size=100))
def test_vote_validation_property(option):
    assume(option not in ["cats", "dogs"])
    response = client.post("/api/vote", json={"option": option})
    assert response.status_code == 422

# 3. Run with pytest
pytest tests/test_vote.py::test_vote_validation_property -v

# 4. Observe edge cases found
# Hypothesis will generate: unicode, null bytes, SQL, XSS, etc.
```

---

## Calico (CNI)

**What:** Kubernetes CNI (Container Network Interface) plugin providing networking and network security for containerized applications.

**Why:** Industry-standard CNI with full NetworkPolicy support. Required for enforcing network isolation policies between pods and namespaces.

**Status:** ✅ In use (Phase 4.5+)

**Installed version:** v3.27.0

---

### Getting Started with Calico

**Prerequisites:**
- Kubernetes cluster (v1.19+)
- kubectl configured with cluster access
- No existing CNI installed (or plan to migrate)

**Installation (what we did in Phase 4.5):**

```bash
# 1. Install Calico CNI v3.27.0
kubectl apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/calico.yaml

# 2. Wait for all Calico pods to be ready
kubectl wait --for=condition=ready pod -l k8s-app=calico-node -n kube-system --timeout=300s
kubectl wait --for=condition=ready pod -l k8s-app=calico-kube-controllers -n kube-system --timeout=300s

# 3. Verify installation
kubectl get pods -n kube-system -l k8s-app=calico-node
kubectl get pods -n kube-system -l k8s-app=calico-kube-controllers

# Expected output:
# calico-node-xxxxx              1/1     Running
# calico-kube-controllers-xxxxx  1/1     Running
```

**Verify NetworkPolicy support:**
```bash
# Check NetworkPolicy API is available
kubectl api-resources | grep networkpolicies

# Expected output:
# networkpolicies    netpol    networking.k8s.io/v1    true    NetworkPolicy
```

---

### What We Implemented in This Project

**Phase 4.5 NetworkPolicy Infrastructure:**

1. **CNI Installation:**
   - Installed Calico v3.27.0 for NetworkPolicy enforcement
   - Verified calico-node and calico-kube-controllers running
   - Confirmed NetworkPolicy CRD available

2. **Namespace Configuration:**
   - Added `name:` labels to all 4 namespaces for NetworkPolicy selectors:
     - `voting-frontend` (name: voting-frontend)
     - `voting-api` (name: voting-api)
     - `voting-consumer` (name: voting-consumer)
     - `voting-data` (name: voting-data)
   - Files: `helm/templates/namespaces/*.yaml`

3. **NetworkPolicy Resources (12 total):**
   - **Default deny-all** (4 policies): One per namespace, blocks all ingress by default
   - **DNS egress** (4 policies): Allow all pods to reach kube-dns for Service discovery
   - **Frontend ingress** (1 policy): Allow Gateway/Ingress → Frontend :80
   - **API ingress** (1 policy): Allow Frontend → API :8000
   - **PostgreSQL ingress** (1 policy): Allow API + Consumer → PostgreSQL :5432
   - **Redis ingress** (1 policy): Allow API + Consumer → Redis :6379
   - Files: `helm/templates/network-policies/*.yaml`

4. **Helm Integration:**
   - Added `networkPolicies` configuration to `helm/values.yaml`
   - Feature flag: `networkPolicies.enabled: false` (disabled by default for safety)
   - CNI selection: `networkPolicies.cni: calico`
   - Conditional rendering: All policies wrapped in `{{- if .Values.networkPolicies.enabled }}`

5. **Documentation:**
   - Comprehensive NetworkPolicy documentation: `docs/NETWORK_POLICY.md` (823 lines)
   - Traffic flow matrix: 7 allowed flows, 6 blocked security boundaries
   - Troubleshooting guide: 5 common issues with debug commands
   - Deployment strategy: Gradual rollout, rollback plan
   - Testing plan: Deferred to Phase 5 (requires application deployment)

**Security Model:**
- Default deny-all ingress (fail-secure)
- Explicit allow rules for documented traffic only
- DNS egress enabled for Service discovery
- No egress restrictions (allows internet access if needed)
- Layer-based isolation (presentation → application → data)

---

### Key Calico Concepts to Learn

**1. CNI Architecture:**
- **calico-node**: DaemonSet running on each node, enforces policies via iptables/eBPF
- **calico-kube-controllers**: Deployment watching Kubernetes resources, syncs policies
- **IPAM (IP Address Management)**: Automatic pod IP allocation from configured pools
- **BGP routing**: Optional Layer 3 routing for pod-to-pod communication across nodes

**2. NetworkPolicy vs Calico NetworkPolicy:**
- **Kubernetes NetworkPolicy**: Standard API, supported by all CNIs (Calico, Cilium, Weave)
- **Calico NetworkPolicy**: Extended CRD with additional features:
  - GlobalNetworkPolicy (cluster-wide, not namespaced)
  - ServiceAccountSelector (fine-grained RBAC integration)
  - Deny rules (explicit deny, not just default deny)
  - HTTP/ICMP protocol matching
  - More flexible ordering and precedence

**3. Policy Selectors:**
- **podSelector**: Matches pods in the same namespace
- **namespaceSelector**: Matches pods in other namespaces by label
- **Combined selectors**: Require BOTH namespace AND pod labels to match
- **Empty podSelector** (`{}`): Matches ALL pods in namespace

**4. Policy Types:**
- **Ingress**: Controls inbound traffic TO pods
- **Egress**: Controls outbound traffic FROM pods
- **Default behavior**: If no policy exists, all traffic allowed (fail-open)
- **With policy**: Only specified traffic allowed (fail-secure)

---

### Learning Path

**Beginner (understand fundamentals):**
1. Read Kubernetes NetworkPolicy docs: https://kubernetes.io/docs/concepts/services-networking/network-policies/
2. Review our implementation: `docs/NETWORK_POLICY.md` (complete traffic matrix)
3. Understand selectors: https://kubernetes.io/docs/concepts/overview/working-with-objects/labels/
4. Try NetworkPolicy editor (visual tool): https://editor.networkpolicy.io/

**Intermediate (hands-on practice):**
1. Deploy our policies: `helm upgrade voting-app ./helm --set networkPolicies.enabled=true`
2. Test connectivity: Use `kubectl exec` to verify allowed/denied connections
3. Debug policy violations: `kubectl logs -n kube-system -l k8s-app=calico-node`
4. Read Calico NetworkPolicy guide: https://docs.tigera.io/calico/latest/network-policy/

**Advanced (deep dive):**
1. Install calicoctl CLI: https://docs.tigera.io/calico/latest/operations/calicoctl/install
2. Inspect policy rules: `calicoctl get networkpolicy -o yaml`
3. View iptables rules: `calicoctl node status` (see how policies translate to iptables)
4. Explore Calico NetworkPolicy CRDs: https://docs.tigera.io/calico/latest/reference/resources/
5. Consider Cilium migration (eBPF-based, L7 policies): See Cilium section below

---

### Resources

**Official Documentation:**
- Getting started: https://docs.tigera.io/calico/latest/getting-started/kubernetes/
- NetworkPolicy guide: https://docs.tigera.io/calico/latest/network-policy/
- Troubleshooting: https://docs.tigera.io/calico/latest/operations/troubleshoot/
- calicoctl CLI: https://docs.tigera.io/calico/latest/operations/calicoctl/

**Tutorials:**
- Calico NetworkPolicy tutorial: https://docs.tigera.io/calico/latest/network-policy/get-started/kubernetes-policy/kubernetes-network-policy
- Advanced policy tutorial: https://docs.tigera.io/calico/latest/network-policy/get-started/kubernetes-policy/kubernetes-demo
- Security best practices: https://docs.tigera.io/calico/latest/network-policy/get-started/kubernetes-policy/kubernetes-policy-advanced

**Debugging Tools:**
- NetworkPolicy editor (visual): https://editor.networkpolicy.io/
- calicoctl: https://docs.tigera.io/calico/latest/operations/calicoctl/install
- Kubernetes Network Policy Recipes: https://github.com/ahmetb/kubernetes-network-policy-recipes

---

### Common Tasks

**Check Calico status:**
```bash
# View Calico pods
kubectl get pods -n kube-system -l k8s-app=calico-node
kubectl get pods -n kube-system -l k8s-app=calico-kube-controllers

# Check logs (troubleshooting)
kubectl logs -n kube-system -l k8s-app=calico-node --tail=100
kubectl logs -n kube-system -l k8s-app=calico-kube-controllers --tail=100
```

**List NetworkPolicies:**
```bash
# All namespaces
kubectl get networkpolicy -A

# Specific namespace
kubectl get networkpolicy -n voting-api

# Detailed view
kubectl describe networkpolicy -n voting-api api-allow-frontend
```

**Test connectivity (Phase 5+):**
```bash
# Test allowed connection: Frontend → API
kubectl exec -n voting-frontend deploy/frontend -- curl -s http://api.voting-api.svc.cluster.local:8000/health

# Test denied connection: Frontend → PostgreSQL (should timeout)
kubectl exec -n voting-frontend deploy/frontend -- timeout 5 curl -s http://postgres.voting-data.svc.cluster.local:5432
```

**Debug policy violations:**
```bash
# Check Calico logs for policy denials
kubectl logs -n kube-system -l k8s-app=calico-node | grep -i "deny\|drop"

# View effective policies for a pod
kubectl get networkpolicy -n voting-api -o yaml
```

---

### Tips for Learning Calico

1. **Start simple**: Test with 1-2 namespaces before scaling to full architecture
2. **Visualize first**: Use https://editor.networkpolicy.io/ to understand selectors
3. **Audit mode**: Deploy policies without enforcement first, review logs for violations
4. **Test systematically**: Our script `scripts/test-network-policies.sh` (Phase 5) validates all flows
5. **Read logs**: Calico logs show why traffic is denied (look for "dropped" or "denied")
6. **Use labels consistently**: Our project uses `app.kubernetes.io/component` for pod selectors
7. **Default deny-all first**: Always create default deny before allow rules (fail-secure)
8. **DNS is critical**: Forgetting DNS egress breaks Service discovery (we include it)
9. **Gradual rollout**: Enable policies per namespace incrementally (not all at once)
10. **Keep documentation updated**: Our `docs/NETWORK_POLICY.md` serves as single source of truth

---

### Troubleshooting

**Issue: Pods can't resolve DNS**
```bash
# Solution: Check DNS egress policy exists
kubectl get networkpolicy -n voting-api allow-dns-access

# Verify kube-dns pods have correct labels
kubectl get pods -n kube-system -l k8s-app=kube-dns --show-labels
```

**Issue: Policy not enforced**
```bash
# 1. Verify Calico is running
kubectl get pods -n kube-system -l k8s-app=calico-node

# 2. Check NetworkPolicy exists
kubectl get networkpolicy -A

# 3. Verify namespace labels match policy selectors
kubectl get ns voting-frontend --show-labels
```

**Issue: Unexpected connection blocked**
```bash
# 1. Check all policies in namespace
kubectl get networkpolicy -n voting-api -o yaml

# 2. Review Calico logs
kubectl logs -n kube-system -l k8s-app=calico-node --tail=100 | grep voting-api

# 3. Verify pod labels match policy podSelector
kubectl get pods -n voting-api --show-labels
```

---

### Next Steps After Calico Mastery

1. **Deploy our policies**: Enable `networkPolicies.enabled: true` in Phase 5
2. **Run validation tests**: Use `scripts/test-network-policies.sh` to verify all flows
3. **Monitor metrics**: Set up Prometheus to track policy denials
4. **Explore Calico NetworkPolicy CRDs**: More powerful than Kubernetes NetworkPolicy
5. **Consider Cilium migration**: eBPF-based, L7 policies, Hubble UI (see Cilium section)

---

## Cilium (Future CNI Migration)

**What:** Next-generation CNI powered by eBPF (extended Berkeley Packet Filter), providing advanced networking, observability, and security.

**Why:** Superior performance, L7 network policies, built-in observability (Hubble), and service mesh capabilities without sidecars.

**Status:** 🔮 Future improvement (Post-Phase 6)

**Resources:**
- Official docs: https://docs.cilium.io/en/stable/
- Getting started: https://docs.cilium.io/en/stable/gettingstarted/
- Hubble observability: https://docs.cilium.io/en/stable/observability/
- L7 policies: https://docs.cilium.io/en/stable/security/policy/language/#layer-7-examples
- Migration from Calico: https://docs.cilium.io/en/stable/installation/cni-chaining/

**Key advantages over Calico:**
- **eBPF-based**: Kernel-level networking (faster, lower overhead)
- **Hubble UI**: Visual network traffic observability (see all pod-to-pod flows in real-time)
- **L7 NetworkPolicy**: HTTP/gRPC method/path filtering (e.g., allow only `GET /api/results`)
- **Service Mesh**: Built-in without sidecars (vs Istio's proxy overhead)
- **Cluster Mesh**: Multi-cluster networking without VPN
- **Advanced telemetry**: Prometheus metrics, distributed tracing integration

**Migration considerations:**
- **Complexity**: More moving parts than Calico (requires learning eBPF concepts)
- **Kubernetes version**: Requires kernel 4.9+ with eBPF support
- **Downtime**: Migration requires pod restart (drain nodes gradually)
- **Monitoring**: Hubble adds observability value for complex microservices (future benefit)

**Recommended migration timeline:**
- **Phase 6+**: After basic NetworkPolicy validation with Calico
- **Trigger**: When need L7 policies (HTTP path filtering) or advanced observability
- **ROI**: Higher for production clusters with >10 microservices

**Example L7 Policy (Cilium-specific):**
```yaml
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: api-l7-policy
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8000"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/results"
        - method: "POST"
          path: "/api/vote"
```

**Next steps for migration:**
1. Complete Phase 4.5 NetworkPolicy testing with Calico
2. Validate all policies work as expected
3. Research Cilium Hubble UI for observability value
4. Decide if L7 policies needed (HTTP path filtering)
5. Plan migration during low-traffic window

---

## Kubernetes Observability (Prometheus + Grafana)

**What:** Monitoring and visualization stack for Kubernetes metrics. Prometheus collects and stores time-series metrics, Grafana provides dashboards and visualizations.

**Why:** Essential for understanding system performance, identifying bottlenecks, and setting SLOs. Enables data-driven decisions for optimization and capacity planning.

**Status:** 🔮 Future improvement (Post-Phase 5.3)

**Current approach:**
- No metrics collection (blind to performance)
- Manual kubectl inspection (pod CPU/memory at a point in time)
- No historical data for trend analysis
- metrics-server addon for kubectl top (basic resource usage)

**Benefits of Prometheus + Grafana:**
- **Historical metrics:** Track performance trends over time (not just snapshots)
- **Custom dashboards:** Visualize vote rate, API latency, consumer lag, pod resources
- **Alerting:** Notify when metrics exceed thresholds (high CPU, slow response times)
- **Query language (PromQL):** Flexible metric aggregation and analysis
- **Service discovery:** Auto-discovers Kubernetes services and pods
- **Industry standard:** Wide ecosystem, extensive documentation

---

### Implementation Options

#### Option A: metrics-server (Lightweight)
**Status:** ⚡ In use for Phase 5.3 load testing

**What:** Cluster-wide metrics aggregator for resource utilization (CPU, memory). Powers `kubectl top` command.

**Installation:**
```bash
# Minikube addon (recommended for local)
minikube addons enable metrics-server -p demo-project--dev

# Verify installation
kubectl top nodes
kubectl top pods --all-namespaces
```

**Pros:**
- ✅ Minimal overhead (~10MB memory)
- ✅ Built-in kubectl integration
- ✅ Sufficient for basic load testing
- ✅ No external dependencies

**Cons:**
- ❌ No historical data (current state only)
- ❌ Limited metrics (CPU/memory, no custom metrics)
- ❌ No visualization (command-line only)
- ❌ No alerting capabilities

**Use case:** Phase 5.3 load testing baseline (quick iteration, no complex setup)

---

#### Option B: kube-prometheus-stack (Production-grade)
**Status:** Recommended for Phase 6+ or production

**What:** Complete observability stack with Prometheus, Grafana, Alertmanager, and pre-configured dashboards for Kubernetes.

**Installation:**
```bash
# Add Prometheus community Helm repo
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

# Install stack with sensible defaults
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --create-namespace \
  --set prometheus.prometheusSpec.retention=7d \
  --set prometheus.prometheusSpec.storageSpec.volumeClaimTemplate.spec.resources.requests.storage=10Gi \
  --set grafana.enabled=true \
  --set grafana.adminPassword=admin

# Access Grafana dashboard
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
# Open http://localhost:3000 (admin/admin)
```

**What's included:**
- **Prometheus:** Metrics collection and storage
- **Grafana:** Visualization dashboards
- **Alertmanager:** Alert routing and notification
- **Node Exporter:** Host-level metrics (CPU, disk, network per node)
- **kube-state-metrics:** Kubernetes object metrics (deployments, pods, services)
- **Pre-built dashboards:** 15+ dashboards (Kubernetes capacity, pod resources, node stats)

**Pros:**
- ✅ Complete observability solution (one install)
- ✅ Pre-configured dashboards (immediate value)
- ✅ Historical data with retention policy
- ✅ Custom metrics support (instrument application code)
- ✅ Alerting (Slack, PagerDuty, email integration)
- ✅ Industry standard (production-ready)

**Cons:**
- ❌ Higher resource usage (~500MB memory)
- ❌ More complex (multiple components)
- ❌ Longer setup time (~10 minutes)
- ❌ Storage requirements for time-series data

**Use case:** Production deployments, long-term monitoring, SLO tracking, capacity planning

---

### Key Metrics to Track

**API Performance:**
- Request rate (requests/second)
- P50/P95/P99 latency (milliseconds)
- Error rate (5xx responses)
- HTTP status code distribution

**Consumer Performance:**
- Consumer lag (messages behind in stream)
- Processing rate (messages/second)
- Processing latency (time from XADD to database insert)
- Failed message count

**Infrastructure:**
- Pod CPU usage (millicores)
- Pod memory usage (MB)
- Pod restart count
- Node resource utilization

**Application-specific:**
- Vote submission rate (votes/second)
- Total votes processed
- Redis Stream length (backlog size)
- Database connection pool usage

---

### Prometheus Query Examples

**API latency P95:**
```promql
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket[5m])
)
```

**Vote submission rate:**
```promql
rate(votes_total[1m])
```

**Consumer lag:**
```promql
redis_stream_length{stream="votes"} - redis_stream_consumer_pending{stream="votes", group="votes-group"}
```

**Pod memory usage:**
```promql
container_memory_usage_bytes{pod=~"api-.*", namespace="voting-api"}
```

---

### Resources

**Prometheus:**
- Official docs: https://prometheus.io/docs/introduction/overview/
- Getting started: https://prometheus.io/docs/prometheus/latest/getting_started/
- PromQL guide: https://prometheus.io/docs/prometheus/latest/querying/basics/
- Best practices: https://prometheus.io/docs/practices/

**Grafana:**
- Official docs: https://grafana.com/docs/grafana/latest/
- Dashboard gallery: https://grafana.com/grafana/dashboards/
- Prometheus integration: https://grafana.com/docs/grafana/latest/datasources/prometheus/

**kube-prometheus-stack:**
- Helm chart: https://github.com/prometheus-community/helm-charts/tree/main/charts/kube-prometheus-stack
- Configuration: https://github.com/prometheus-community/helm-charts/blob/main/charts/kube-prometheus-stack/values.yaml
- Pre-built dashboards: https://grafana.com/grafana/dashboards/?search=kubernetes

**metrics-server:**
- GitHub: https://github.com/kubernetes-sigs/metrics-server
- Design docs: https://github.com/kubernetes/design-proposals-archive/blob/main/instrumentation/resource-metrics-api.md

---

### Trade-offs

**metrics-server:**
- ➕ Minimal resource footprint
- ➕ Fast setup (1 command)
- ➕ Good enough for basic load testing
- ➖ No persistence (restart loses data)
- ➖ No custom metrics
- ➖ No visualization

**kube-prometheus-stack:**
- ➕ Production-ready observability
- ➕ Historical data and trend analysis
- ➕ Custom application metrics (instrument code)
- ➕ Alerting and notification
- ➖ Higher resource requirements
- ➖ More complex configuration
- ➖ Storage needs for time-series data

---

### Decision Context

**Phase 5.3 (current):** Use metrics-server for load testing
- Need: Basic CPU/memory visibility during load tests
- Goal: Identify obvious bottlenecks (CPU/memory exhaustion)
- Duration: Short-lived tests (< 5 minutes each)
- Decision: metrics-server sufficient, avoid complexity

**Phase 6+ (future):** Upgrade to kube-prometheus-stack
- Need: Production observability, SLO tracking
- Goal: Continuous monitoring, trend analysis, alerting
- Duration: Always-on monitoring
- Decision: Full stack worth the investment

**Trigger for upgrade:**
- Production deployment planned
- Need to establish SLOs with data
- Want to track performance over time
- Team needs dashboards for visibility

---

### Recommended Path

**Phase 5.3 (now):**
1. Enable metrics-server: `minikube addons enable metrics-server -p demo-project--dev`
2. Run load tests with `kubectl top` monitoring
3. Document baseline metrics in load test results
4. Identify bottleneck component (API/consumer/database)

**Phase 6 (later):**
1. Install kube-prometheus-stack when needed
2. Configure retention and storage
3. Import pre-built Kubernetes dashboards
4. Add custom application metrics (FastAPI middleware)
5. Set up alerting rules (P95 latency, error rate)

---

## Load Testing Tools (k6, Locust, Apache Bench)

**What:** Tools for generating synthetic load to measure system performance under concurrent user traffic.

**Why:** Validates system capacity, identifies bottlenecks, establishes performance baselines, prevents production incidents from unexpected traffic spikes.

**Status:** ⚡ Apache Bench in use for Phase 5.3, k6/Locust for future

---

### Implementation Options

#### Option A: Apache Bench (ab) - Lightweight
**Status:** ⚡ In use for Phase 5.3 load testing

**What:** Simple HTTP benchmarking tool. Pre-installed on most systems (Apache HTTP server utilities).

**Use case:** Quick baseline tests, simple load patterns, minimal setup

**Example:**
```bash
# 100 requests, 10 concurrent
ab -n 100 -c 10 -p vote.json -T application/json \
  http://localhost:8000/api/vote

# vote.json content:
{"option": "cats"}
```

**Pros:**
- ✅ Zero installation (usually pre-installed)
- ✅ Simple CLI interface
- ✅ Fast execution
- ✅ Good for quick tests

**Cons:**
- ❌ No scripting (can't randomize payloads)
- ❌ Limited metrics (basic only)
- ❌ No ramp-up strategy (immediate load)
- ❌ No distributed load generation

**Best for:** Phase 5.3 baseline tests (10-100 concurrent users)

---

#### Option B: k6 - Modern & Kubernetes-native
**Status:** Recommended for Phase 6+ or complex load testing

**What:** Modern load testing tool with JavaScript scripting, designed for developers and CI/CD pipelines. Kubernetes-native with operator support.

**Use case:** Realistic user scenarios, progressive load, distributed testing, CI/CD integration

**Installation:**
```bash
# macOS
brew install k6

# Docker
docker pull grafana/k6

# Kubernetes operator
kubectl apply -f https://github.com/grafana/k6-operator/releases/latest/download/bundle.yaml
```

**Example script:**
```javascript
// vote-load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 10 },  // Ramp up to 10 users
    { duration: '1m', target: 50 },   // Ramp up to 50 users
    { duration: '1m', target: 50 },   // Stay at 50 users
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(95)<200'],  // 95% of requests < 200ms
    'http_req_failed': ['rate<0.01'],    // < 1% error rate
  },
};

export default function () {
  const options_list = ['cats', 'dogs'];
  const option = options_list[Math.floor(Math.random() * options_list.length)];

  const payload = JSON.stringify({ option });
  const params = { headers: { 'Content-Type': 'application/json' } };

  const res = http.post('http://localhost:8000/api/vote', payload, params);

  check(res, {
    'status is 201': (r) => r.status === 201,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);  // 1 second between requests per user
}
```

**Run:**
```bash
k6 run vote-load-test.js
```

**Pros:**
- ✅ JavaScript scripting (familiar for web devs)
- ✅ Realistic user scenarios (random payloads, delays)
- ✅ Progressive load (ramp-up/ramp-down)
- ✅ Built-in metrics (P50/P95/P99, requests/sec)
- ✅ Threshold assertions (SLO validation)
- ✅ Kubernetes operator (run as CronJob)
- ✅ Cloud execution support (k6 Cloud, Grafana Cloud)

**Cons:**
- ❌ Requires installation
- ❌ JavaScript knowledge needed
- ❌ More complex than Apache Bench

**Best for:** Progressive load tests, SLO validation, production-like scenarios

---

#### Option C: Locust - Python-based distributed testing
**Status:** Alternative to k6, Python-focused teams

**What:** Python-based load testing tool with web UI. Designed for distributed load generation across multiple machines.

**Use case:** Python teams, distributed testing, web UI for monitoring, complex user behavior

**Installation:**
```bash
pip install locust
```

**Example:**
```python
# locustfile.py
from locust import HttpUser, task, between
import random

class VotingUser(HttpUser):
    wait_time = between(1, 3)  # 1-3 seconds between requests

    @task
    def submit_vote(self):
        option = random.choice(['cats', 'dogs'])
        self.client.post("/api/vote", json={"option": option})

    @task(2)  # 2x more frequent than vote
    def get_results(self):
        self.client.get("/api/results")
```

**Run:**
```bash
# Web UI
locust -f locustfile.py --host=http://localhost:8000

# Headless
locust -f locustfile.py --host=http://localhost:8000 \
  --users 50 --spawn-rate 5 --run-time 2m --headless
```

**Pros:**
- ✅ Python-based (familiar for backend teams)
- ✅ Web UI for monitoring (real-time charts)
- ✅ Distributed mode (master/worker architecture)
- ✅ Task weighting (realistic user behavior)
- ✅ Flexible scripting (any Python library)

**Cons:**
- ❌ Requires Python environment
- ❌ Higher resource usage (Python overhead)
- ❌ No built-in Kubernetes operator

**Best for:** Python-centric teams, distributed testing, complex user flows

---

### Comparison Matrix

| Feature | Apache Bench | k6 | Locust |
|---------|-------------|-----|--------|
| **Installation** | Pre-installed | brew/docker | pip install |
| **Scripting** | None | JavaScript | Python |
| **Ramp-up** | No | Yes | Yes |
| **Metrics** | Basic | Advanced (P95/P99) | Advanced |
| **UI** | CLI only | CLI only | Web UI |
| **Distributed** | No | Yes (k6 Cloud) | Yes (master/worker) |
| **K8s native** | No | Yes (operator) | No |
| **Learning curve** | Low | Medium | Medium |
| **Best for** | Quick tests | Modern CI/CD | Python teams |

---

### Resources

**Apache Bench:**
- Manual: https://httpd.apache.org/docs/2.4/programs/ab.html
- Tutorial: https://www.tutorialspoint.com/apache_bench/index.htm

**k6:**
- Official docs: https://k6.io/docs/
- Getting started: https://k6.io/docs/get-started/running-k6/
- Examples: https://k6.io/docs/examples/
- k6 operator: https://github.com/grafana/k6-operator
- Test scripts library: https://github.com/grafana/k6-learn

**Locust:**
- Official docs: https://docs.locust.io/
- Quickstart: https://docs.locust.io/en/stable/quickstart.html
- Distributed mode: https://docs.locust.io/en/stable/running-distributed.html

---

### Trade-offs

**Apache Bench:**
- ➕ Instant start (no setup)
- ➕ Simple and fast
- ➕ Good for quick validation
- ➖ No realistic scenarios
- ➖ Limited metrics

**k6:**
- ➕ Modern developer experience
- ➕ Advanced metrics (P95/P99)
- ➕ Kubernetes-native
- ➕ SLO validation (thresholds)
- ➖ Requires JavaScript knowledge
- ➖ Extra installation step

**Locust:**
- ➕ Python ecosystem integration
- ➕ Web UI for monitoring
- ➕ Distributed testing
- ➖ Higher resource usage
- ➖ Python dependency

---

### Decision Context

**Phase 5.3 (current):** Use Apache Bench
- Need: Quick baseline performance measurement
- Goal: Identify obvious bottlenecks (not production SLO validation)
- Complexity: Simple POST /api/vote tests
- Decision: Apache Bench sufficient for initial iteration

**Phase 6+ (future):** Upgrade to k6
- Need: Realistic load testing with progressive ramp-up
- Goal: Validate SLOs, test failure modes, stress testing
- Complexity: Multiple endpoints, randomized payloads, think time
- Decision: k6 provides better metrics and scripting

**Trigger for k6 adoption:**
- Need to establish formal SLOs (P95 < 200ms)
- Production deployment imminent
- Want CI/CD load testing automation
- Team comfortable with JavaScript

---

### Recommended Path

**Phase 5.3 (now):**
1. Use Apache Bench for quick baseline tests
2. Test with 10, 50, 100 concurrent users
3. Document P50/P95 latencies (use -g flag for TSV output)
4. Monitor with kubectl top during tests

**Phase 6 (later):**
1. Install k6 when need realistic scenarios
2. Write progressive load test script (ramp-up strategy)
3. Define SLO thresholds in k6 options
4. Integrate into CI/CD pipeline
5. Consider k6 operator for scheduled tests in Kubernetes

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
