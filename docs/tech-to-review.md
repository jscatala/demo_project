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
