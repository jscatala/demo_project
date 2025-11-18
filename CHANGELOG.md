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

### Changed
- Updated README.md phase badge to 4.1 complete
- Enhanced CONTRIBUTING.md with pre-deployment security checklist
- Updated api/.dockerignore to allow tests/ directory for Dockerfile.test builds

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
