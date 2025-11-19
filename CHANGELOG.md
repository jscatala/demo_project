# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Non-root container validation script (`scripts/verify-nonroot.sh`)
- Trivy container security scanner integration (Docker-based, no local install)
- Helm template helper for standard securityContext (`voting.securityContext`)
- Security validation documentation in CONTRIBUTING.md
- Policy-as-Code documentation (OPA Gatekeeper/Kyverno) in tech-to-review.md
- Trivy documentation in tech-to-review.md
- API input validation audit documentation (`api/docs/VALIDATION.md`, 600+ lines)
- Docker-based test infrastructure for API (`api/Dockerfile.test`)
- pytest-cov for test coverage reporting
- API test fixtures with lifespan mocking (`api/tests/conftest.py`)
- High-priority security validation tests (SQL injection, XSS, oversized payload, malformed JSON)
- Property-based testing documentation (Hypothesis/Schemathesis) in tech-to-review.md
- SQL injection prevention audit documentation in `api/docs/VALIDATION.md`
- Calico CNI v3.27.0 for NetworkPolicy enforcement
- NetworkPolicy templates for 4-namespace isolation (default deny-all with explicit allow)
- Network traffic flow documentation (`docs/NETWORK_POLICY.md`, 800+ lines)
- Cilium CNI evaluation documentation for future L7 policy migration (tech-to-review.md)

### Security
- Validated all containers run as non-root (frontend: UID 1000, api: UID 65532, consumer: UID 1000)
- Automated security scanning with Trivy (misconfiguration detection)
- Zero HIGH/CRITICAL security findings in all images
- Comprehensive API input validation audit completed (18-scenario matrix, 56% test coverage)
- SQL injection protection validated (Pydantic Literal type validation)
- XSS protection validated (Pydantic rejects script tags)
- Request size limits validated (1MB middleware protection)
- Malformed JSON handling validated (FastAPI 422 responses)
- SQL injection prevention audit complete (Phase 4.3):
  - All 4 database queries audited and verified safe
  - 100% use asyncpg parameterized queries ($1 placeholders) or stored procedures
  - Zero unsafe SQL patterns (f-strings, % formatting, concatenation) found
  - Triple-layer defense: Pydantic validation → asyncpg parameterization → application logic
  - Automated scan verified no SQL injection vulnerabilities
- Container vulnerability scanning complete (Phase 4.4):
  - Scanned all 3 production images with Trivy (frontend, api, consumer)
  - Frontend (Alpine 3.19.1): 18 HIGH/CRITICAL vulnerabilities - OS end-of-life, requires upgrade
  - API (Debian 12.12): 7 HIGH/CRITICAL vulnerabilities - 2 Python packages fixable (python-multipart, starlette)
  - Consumer (Debian 13.1): 0 HIGH/CRITICAL vulnerabilities - clean baseline
  - Comprehensive vulnerability report created (`docs/VULNERABILITY_SCAN.md`)
  - Remediation plan documented for all findings
- Network policy implementation complete (Phase 4.5):
  - 12 NetworkPolicy resources implementing default deny-all with explicit allow
  - Calico CNI v3.27.0 installed and verified (calico-node, calico-kube-controllers running)
  - 4 namespaces isolated: voting-frontend, voting-api, voting-consumer, voting-data
  - 7 legitimate traffic flows documented and allowed (Gateway→Frontend, Frontend→API, API/Consumer→PostgreSQL/Redis, All→DNS)
  - 6 security boundaries enforced (Frontend blocked from data layer, Consumer blocked from presentation layer, external access restricted)
  - DNS egress policies enabled for Service discovery (kube-dns on port 53 TCP/UDP)
  - Namespace labels added for NetworkPolicy selectors (`name: voting-*`)
  - Helm values configuration for NetworkPolicy feature flag (`networkPolicies.enabled: false` by default)
  - Comprehensive NetworkPolicy documentation created (`docs/NETWORK_POLICY.md`, 800+ lines with traffic matrix, troubleshooting, CNI compatibility)
  - Cilium CNI evaluation documented for future L7 policy migration (Post-Phase 6)
  - Network policies deployed to minikube (demo-project--dev profile)
  - End-to-end vote flow verified with policies enabled (0 errors, all traffic allowed as expected)
  - Network connectivity validation script created (`scripts/test-network-policies.sh`)
- Integration testing complete (Phase 5.1-5.2):
  - Helm deployment to minikube with internal StatefulSets (PostgreSQL, Redis)
  - All images loaded: frontend:0.5.0, api:0.3.2, consumer:0.3.1
  - Local configuration created (`helm/values-local.yaml`)
  - End-to-end vote flow verified: Vote → Redis Stream → Consumer → PostgreSQL → Results
  - Network policies enabled and validated (12 policies active)
  - Phase 4 validation checklist created (`docs/PHASE4_VALIDATION.md`, 881 lines)
- Load testing baseline established (Phase 5.3):
  - metrics-server enabled for lightweight observability (kubectl top)
  - Apache Bench load testing executed (10 concurrent users, 100 requests)
  - Performance metrics captured: P50 528ms, P95 1300ms, 15.94 req/sec
  - Resource usage monitored: API 16m CPU, Consumer 40m CPU under load
  - Vote accuracy verified: 100% (112/112 votes processed correctly)
  - Consumer lag verified: 0 pending messages (real-time processing)
  - Technology documentation added to `tech-to-review.md`: observability (metrics-server vs Prometheus/Grafana) and load testing tools (Apache Bench, k6, Locust)
  - Session documentation created (`docs/sessions/2025-11-19-session-13-phase5.3-load-testing.md`)
- Documentation enhancements (Phase 6):
  - README.md architecture diagrams: Network Policy Topology and Security Boundaries (148 lines)
  - DEPLOYMENT.md verification and troubleshooting enhancements (consumer v0.3.1, port-forward 8081, network policy validation)
  - Production readiness checklist (`docs/PRODUCTION_READINESS.md`, 1100+ lines, 100+ validation checkpoints)

### Changed
- Updated README.md phase badge to 6 complete
- Enhanced CONTRIBUTING.md with pre-deployment security checklist
- Updated api/.dockerignore to allow tests/ directory for Dockerfile.test builds
- Consumer version bumped from v0.3.0 to v0.3.1

### Fixed
- Fixed Helm templates using hardcoded values instead of template variables (api/deployment.yaml)
  - Image tag now uses `{{ .Values.images.api.tag }}` instead of hardcoded `api:0.1.0`
  - Environment variables now use values (REDIS_URL, DATABASE_URL, CORS_ORIGINS)
  - Image pull policy now configurable via values
- Fixed API security context UID mismatch (1000 → 65532) for distroless compatibility
  - Resolved CrashLoopBackOff caused by permission errors
  - All pods now run with correct non-root UIDs
- Fixed consumer field name mismatch (expected "vote", API sent "option")
  - Updated consumer/main.py to read "option" field from Redis Stream messages
  - Resolved vote processing failures (all votes were rejected as malformed)

## [0.1.0-dev] - 2025-11-15

### Added
- Project initialization
- Technical stack selection (K8s, Helm, FastAPI, TypeScript, Redis Streams, PostgreSQL)
- Architecture decisions documented in ADRs
- Conventional Commits and Semantic Versioning adoption

### Decisions
- Kubernetes-native deployment from day 0
- Redis Streams for event-driven architecture
- Cats vs Dogs as initial voting options
- Security-first approach with multistage Docker builds

[Unreleased]: https://github.com/your-org/voting-app/compare/v0.1.0-dev...HEAD
[0.1.0-dev]: https://github.com/your-org/voting-app/releases/tag/v0.1.0-dev
