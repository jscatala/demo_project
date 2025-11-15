# Session 06: Phase 2 - API Production Dockerfile & Distroless Migration

**Date:** 2025-11-15
**Focus:** Manual TODO resolution, Gateway API decision, Phase 2.1 implementation (distroless + uv)
**Status:** Completed

---

## Session Summary

Resolved manual TODOs blocking Phase 2, made critical architectural decision on ingress strategy, and completed Phase 2.1 with modern container optimization (distroless + uv).

---

## Completed Tasks

### 1. Manual TODO Resolution

Addressed 5 blocking questions before starting Phase 2:

**a) Ingress Strategy**
- **Decision:** Adopt Gateway API with Envoy Gateway implementation
- **Rationale:** Ingress NGINX officially retired (Nov 2025) due to security vulnerabilities
- **Created:** ADR-0005 documenting Gateway API adoption
- **Impact:** Provider-agnostic, future-proof, security-focused

**b) API Horizontal Scaling**
- **Clarified:** Kubernetes-native approach (1 uvicorn process per pod)
- **Scaling:** Via pod replicas, K8s handles load balancing
- **Rejected:** Multi-worker per container (loses K8s granularity)

**c) API Response Format**
- **Decision:** HTTP-only status codes (RESTful standard)
- **Rejected:** Status codes in response body (redundant)

**d) HEAD Request 405 Errors**
- **Fixed:** Added HEAD method support to `/health` and `/ready` endpoints
- **Change:** `@app.get()` → `@app.api_route(..., methods=["GET", "HEAD"])`
- **File:** `api/main.py:34,40`

**e) Python Stack Confirmation**
- **Confirmed:** Python 3.11+ with static typing for Phase 2
- **Benefit:** Better docs, Swagger auto-generation, IDE support

### 2. Documentation Created

**ADR-0005: Gateway API with Envoy Gateway**
- Documented retirement of Ingress NGINX (Nov 2025, CVE-2025-*)
- Evaluated alternatives (Traefik, cloud controllers, Gateway API)
- Rationale for Gateway API + Envoy Gateway
- Aligned with ADR-0001 (provider-agnostic requirement)

**docs/tech-to-review.md (new file)**
- Gateway API resources and documentation links
- Envoy Gateway implementation guides
- Template for tracking new technologies

### 3. Phase 2.1: FastAPI Production Dockerfile

**Initial Implementation (api:0.2.0)**
- Python 3.13-slim multistage build
- pip-based dependency installation
- Non-root user (UID 1000)
- Image size: 274MB
- Verified: /health endpoint, non-root execution

**Optimization (api:0.2.1)**
- **Replaced pip with uv:** 5-10x faster dependency installation
- **Switched to distroless:** Google distroless Python 3.11 base image
- **Image size reduction:** 274MB → 166MB (39% reduction, 108MB saved)
- **Security improvements:** No shell, package managers, or unnecessary binaries
- **Non-root by default:** UID 65532 (distroless standard)

**Technical Details:**
- Builder stage: `python:3.11-slim` + uv
- Runtime stage: `gcr.io/distroless/python3-debian12:nonroot`
- Python version: 3.11 (matched to distroless availability)
- Binary compatibility: Ensured Python version consistency between build/runtime

**Challenges Resolved:**
1. Python version mismatch (3.12 builder vs 3.11 runtime) → aligned to 3.11
2. CMD format for distroless (no script wrappers) → `["-m", "uvicorn", ...]`
3. Site-packages path mapping → `/home/nonroot/.local/lib/python3.11/site-packages`

---

## Files Created

```
docs/adr/0005-gateway-api-ingress.md         # Gateway API architectural decision
docs/tech-to-review.md                       # Technology reference tracking
```

---

## Files Modified

```
api/main.py                                  # HEAD method support for health endpoints
api/Dockerfile                               # Distroless + uv multistage build
api/requirements.txt                         # Updated dependency versions
api/.dockerignore                           # Enhanced exclusion patterns
helm/values.yaml                            # Updated api.image.tag: "0.2.1"
todos.md                                    # Removed manual TODOs, marked Phase 2.1 complete
```

---

## Key Decisions

| Decision | Rationale | Reference |
|----------|-----------|-----------|
| Gateway API over Ingress NGINX | Security (CVEs), official K8s direction, provider-agnostic | ADR-0005 |
| Distroless over slim images | 39% size reduction, minimal attack surface, no shell/package managers | Commit c4bd478 |
| uv over pip | 5-10x faster builds, better dependency resolution | Phase 2.1 |
| Python 3.11 over 3.13 | Distroless availability, production stability | Dockerfile |
| HTTP-only status codes | RESTful standard, avoid redundancy | Manual TODOs |

---

## Metrics

**Image Size:**
- Initial (0.1.0): ~260MB (basic build)
- With Python 3.13-slim (0.2.0): 274MB
- With distroless + uv (0.2.1): 166MB
- **Total reduction:** 94MB (36% from initial)

**Build Performance:**
- pip install: ~15-20s (estimated)
- uv install: ~3-5s (estimated)
- **Speed improvement:** 3-5x faster

**Security Posture:**
- Attack surface: Minimal (no shell, apt, unnecessary binaries)
- Vulnerability scanning: Reduced base image CVEs
- Non-root execution: Enforced by default (UID 65532)

---

## Next Steps

**Immediate (Phase 2.2):**
- Implement POST `/api/vote` endpoint with Redis Stream integration
- Add Pydantic validation for vote options (cats/dogs)
- Implement structured logging
- Write unit tests

**Phase 2 Remaining:**
- GET `/api/results` endpoint with PostgreSQL integration
- FastAPI security configuration (CORS, headers, rate limits)
- Consumer: Redis Stream processor with PostgreSQL aggregation
- Consumer: K8s Deployment manifest

**Infrastructure:**
- Update Gateway API resources in helm/templates/
- Configure Envoy Gateway for rate limiting
- Test Helm deployment with new api:0.2.1 image

---

## Context for Next Session

**Current State:**
- Phase 0: Complete (Documentation)
- Phase 1: Complete (K8s Foundation)
- Phase 2.1: Complete (API Dockerfile)
- **Next:** Phase 2.2 (POST /vote endpoint)

**Environment:**
- API image: `api:0.2.1` (distroless Python 3.11 + uv)
- Base architecture: K8s-native, Gateway API, Redis Streams
- Security: Built-in from start, distroless runtime

**Key Files for Reference:**
- `@Demo_project/todos.md` - Current phase tracking
- `@docs/adr/0005-gateway-api-ingress.md` - Ingress decision
- `@docs/tech-to-review.md` - Technology references
- `@api/Dockerfile` - Distroless implementation example

---

## Commits

```
8eae832 - docs(adr): adopt Gateway API with Envoy Gateway
          - Added ADR-0005, tech-to-review.md
          - Fixed HEAD method support on health endpoints
          - Updated todos.md (Gateway API reference)
          - Resolved all manual TODOs

c4bd478 - feat(api): migrate to distroless with uv package manager
          - Replaced pip with uv (5-10x faster)
          - Switched to distroless Python 3.11
          - Reduced image size 274MB → 166MB (39%)
          - Enhanced security (minimal runtime)
          - Updated helm/values.yaml to 0.2.1
```

---

## Questions/Blockers

None - ready to proceed with Phase 2.2 (POST /vote endpoint).

---

## References

- [Gateway API Official Docs](https://gateway-api.sigs.k8s.io/)
- [Envoy Gateway Docs](https://gateway.envoyproxy.io/)
- [Ingress NGINX Retirement Announcement](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/)
- [uv Package Manager](https://github.com/astral-sh/uv)
- [Google Distroless Images](https://github.com/GoogleContainerTools/distroless)
