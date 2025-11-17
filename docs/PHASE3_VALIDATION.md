# Phase 3 Validation Protocol - Manual Checklist

**Purpose:** Verify frontend application is correctly implemented, containerized, and integrated with backend services before deployment.

**Date:** 2025-11-17
**Phase:** 3 (Frontend Implementation)
**Testing:** Phase 3.5 Complete (TDD, 100% coverage)
**Validator:** ___________

---

## Validation Checklist

### 1. Pre-Flight Checks

**1.1 Verify Docker Images Built**

```bash
# List frontend image
docker images | grep frontend | grep 0.5.0

# Expected output:
# frontend   0.5.0   [IMAGE_ID]   [TIME]   ~76MB
```

- [X] frontend:0.5.0 image exists
- [X] Image size within expected range (~76MB)

**1.2 Verify Source Files**

```bash
# Check frontend structure
ls -l frontend/src/components/
ls -l frontend/src/hooks/
ls -l frontend/src/services/
ls -l frontend/src/types/

# Expected files:
# Components: VoteButtons.tsx, VoteButtons.module.css, VoteButtons.test.tsx
#             VoteResults.tsx, VoteResults.module.css, VoteResults.test.tsx
# Hooks: useVote.ts, useResults.ts
# Services: api.ts
# Types: api.ts
```

- [X] VoteButtons component files present
- [X] VoteResults component files present
- [X] Custom hooks present (useVote, useResults)
- [X] API service and types present
- [X] All TypeScript files have .ts/.tsx extension

**1.3 Verify Build Output**

```bash
# Check Vite build configuration
cat frontend/vite.config.ts | grep -E "(build|minify)"

# Check package.json scripts
cat frontend/package.json | grep -E "(build|dev)"
```

- [X] Vite configuration exists
- [X] Build script configured (tsc && vite build)
- [X] Dev script configured (vite)

---

### 2. Frontend Container Validation

**Note:** Frontend is a static nginx container serving React build. It does NOT require backend dependencies to start, but API integration requires backend services for full functionality.

**2.1 Test Frontend Container Startup (No Dependencies)**

```bash
# Run frontend container standalone
docker run --rm -d --name frontend-test -p 8080:8080 frontend:0.5.0

# Wait for startup
sleep 2

# Check if nginx is running
docker exec frontend-test ps aux | grep nginx

# Expected output:
# appuser   1  nginx: master process
# appuser   X  nginx: worker process

# Check user ID (should be 1000, not root)
docker exec frontend-test id

# Expected output:
# uid=1000(appuser) gid=1000(appgroup) groups=1000(appgroup)

# Stop container
docker stop frontend-test
```

- [X] Frontend container starts successfully
- [X] nginx process running
- [X] Container runs as UID 1000 (non-root)
- [X] No startup errors in logs

**2.2 Test HTTP Response**

```bash
# Start frontend
docker run --rm -d --name frontend-test -p 8080:8080 frontend:0.5.0

# Test HTTP response
curl -I http://localhost:8080

# Expected output includes:
# HTTP/1.1 200 OK
# Server: nginx/1.25.5
# Content-Type: text/html
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Content-Security-Policy: ...

# Stop container
docker stop frontend-test
```

- [X] Returns HTTP 200 OK
- [X] Content-Type is text/html
- [X] Security headers present (X-Frame-Options, CSP, etc.)
- [X] Server header shows nginx/1.25.5

**2.3 Test SPA Routing**

```bash
# Start frontend
docker run --rm -d --name frontend-test -p 8080:8080 frontend:0.5.0

# Test SPA routing (should return 200, not 404)
curl -I http://localhost:8080/vote
curl -I http://localhost:8080/some-random-path

# Expected: Both return HTTP 200 (nginx try_files handles SPA routing)

# Stop container
docker stop frontend-test
```

- [X] /vote returns 200 OK (not 404)
- [X] Random paths return 200 OK (SPA fallback to index.html)
- [X] nginx correctly configured for SPA routing

**2.4 Test Static Asset Serving**

```bash
# Start frontend
docker run --rm -d --name frontend-test -p 8080:8080 frontend:0.5.0

# Fetch index.html
curl -s http://localhost:8080 | head -20

# Expected output includes:
# <!DOCTYPE html>
# <html lang="en">
# <head>
# ...
# <script type="module" crossorigin src="/assets/index-[hash].js"></script>
# <link rel="stylesheet" crossorigin href="/assets/index-[hash].css">

# Test asset loading (check for 200, not 404)
#ERROR -P not recognized
ASSET_JS=$(curl -s http://localhost:8080 | grep -oP 'src="/assets/index-\K[^"]+')
ASSET_CSS=$(curl -s http://localhost:8080 | grep -oP 'href="/assets/index-\K[^"]+')

curl -I http://localhost:8080/assets/index-${ASSET_JS}
curl -I http://localhost:8080/assets/index-${ASSET_CSS}

# Expected: Both return HTTP 200

# Stop container
docker stop frontend-test
```

- [X] index.html serves correctly
- [X] JavaScript assets return 200 OK
- [X] CSS assets return 200 OK
- [X] Asset hashes present (cache busting)

---

### 3. Component Validation (Manual Browser Testing)

**Note:** This section requires running the frontend in a browser. Backend services are NOT required for UI component testing.

**3.1 Start Frontend for Manual Testing**

```bash
# Run frontend container
docker run --rm -d --name frontend-manual -p 8080:8080 frontend:0.5.0

# Open in browser: http://localhost:8080

#ERROR: API URL not configured
```

**3.2 Test VoteButtons Component**

- [X] Two voting buttons visible (Cats, Dogs)
- [X] Buttons display side-by-side on desktop
- [X] Buttons stack vertically on mobile (<768px)
- [X] Hover effect: scale transform and color change
- [X] Click triggers loading state (button disabled)
- [X] Keyboard navigation works (Tab, Enter, Space)
- [X] ARIA labels present (inspect with screen reader or devtools)

**3.3 Test VoteResults Component**

- [ ] Results section displays at top of page
- [ ] Progress bars visible for both options
- [ ] Percentages calculated and displayed (1 decimal)
- [ ] Vote counts formatted with thousand separators
- [ ] Total votes sum displayed
- [ ] Empty state shows "No votes yet" (if no backend)
- [ ] Loading skeleton displays during fetch

**3.4 Test Responsive Design**

```bash
# Test in browser DevTools:
# 1. Desktop: 1920x1080 - side-by-side buttons
# 2. Tablet: 768x1024 - check breakpoint transition
# 3. Mobile: 375x667 - stacked buttons
```

- [ ] Desktop layout (buttons side-by-side)
- [ ] Mobile layout (buttons stacked)
- [ ] Breakpoint transition at 768px works smoothly
- [ ] No horizontal scroll on mobile
- [ ] Text readable on all screen sizes

**3.5 Test Accessibility**

```bash
# Test with keyboard:
# - Tab through all interactive elements
# - Enter/Space to activate buttons
# - Screen reader announcement (VoiceOver, NVDA)
```

- [ ] All buttons keyboard accessible
- [ ] Focus indicators visible
- [ ] ARIA live region announces result changes
- [ ] ARIA progressbar attributes present
- [ ] Screen reader announces votes correctly

**3.6 Cleanup**

```bash
# Stop manual testing container
docker stop frontend-manual
```

---

### 4. API Integration Validation

**Important:** This section requires backend services (API, Redis, PostgreSQL) running. Frontend will show errors without backend.

**Integration Testing Options:**

**Option A: Minikube Deployment (Recommended - Production-like)**
```bash
# Use automated deployment script
./scripts/deploy-local.sh --rebuild

# See docs/DEPLOYMENT.md for detailed guide
```

**Option B: Docker Containers (Quick Testing)**

**4.1 Start Backend Services**

```bash
# Start Redis
docker run -d --name redis-test -p 6379:6379 redis:7-alpine

# Start PostgreSQL
docker run -d --name postgres-test -p 5432:5432 \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=votes \
  postgres:15-alpine

# Wait for PostgreSQL
sleep 5

# Create votes table
docker exec -i postgres-test psql -U postgres -d votes <<EOF
CREATE TABLE IF NOT EXISTS votes (
  id SERIAL PRIMARY KEY,
  option VARCHAR(10) NOT NULL CHECK (option IN ('cats', 'dogs')),
  count INTEGER DEFAULT 0
);

-- Initialize with zero votes
INSERT INTO votes (option, count) VALUES ('cats', 0), ('dogs', 0)
ON CONFLICT DO NOTHING;

-- Create increment function
CREATE OR REPLACE FUNCTION increment_vote(vote_option VARCHAR) RETURNS VOID AS \$\$
BEGIN
  UPDATE votes SET count = count + 1 WHERE option = vote_option;
END;
\$\$ LANGUAGE plpgsql;
EOF

# Start API (with Redis and PostgreSQL URLs)
docker run -d --name api-test -p 8000:8000 \
  -e REDIS_URL=redis://host.docker.internal:6379 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/votes \
  -e CORS_ORIGINS=http://localhost:8080 \
  api:0.3.2

# Wait for API startup
sleep 3

# Verify API is running
curl -I http://localhost:8000/health
# Expected: HTTP 200 OK
```

- [ ] Redis started successfully
- [ ] PostgreSQL started successfully
- [ ] Votes table created
- [ ] API started and /health returns 200

**4.2 Start Frontend with API_URL**

```bash
# Create config.js with API URL
mkdir -p /tmp/frontend-config
cat > /tmp/frontend-config/config.js <<EOF
window.APP_CONFIG = {
  API_URL: 'http://localhost:8000'
};
EOF

# Start frontend with config mounted
docker run -d --name frontend-integration -p 8080:8080 \
  -v /tmp/frontend-config/config.js:/usr/share/nginx/html/config.js:ro \
  frontend:0.5.0

# Open browser: http://localhost:8080
```

- [ ] Frontend starts with API_URL configured
- [ ] Browser console shows no errors
- [ ] API URL displayed in footer

**4.3 Test Vote Submission (Browser)**

Open http://localhost:8080 in browser:

- [ ] Click "Cats" button
- [ ] Loading state displays
- [ ] Vote confirmation message appears
- [ ] Results update with new count
- [ ] Progress bars adjust percentages
- [ ] "Vote Again" button appears
- [ ] Click "Vote Again" clears state

**4.4 Test Results Fetching**

```bash
# Add votes via API
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "cats"}'

curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "dogs"}'

# Refresh browser - results should update
```

- [ ] GET /api/results called on mount
- [ ] Results display vote counts
- [ ] Percentages calculated correctly
- [ ] Manual refresh updates counts

**4.5 Test Error Handling**

```bash
# Stop API to trigger network error
docker stop api-test

# In browser:
# - Click vote button
# - Observe error message display
```

- [ ] Error message displays (red alert with icon)
- [ ] Error text: "Network error. Please check your connection."
- [ ] Vote button remains clickable after error
- [ ] "Vote Again" button clears error

**4.6 Test Invalid Vote (Optional)**

```bash
# Restart API
docker start api-test
sleep 2

# Test invalid option (should return 422)
curl -X POST http://localhost:8000/api/vote \
  -H "Content-Type: application/json" \
  -d '{"option": "birds"}'

# Expected: 422 Unprocessable Entity
```

- [ ] API returns 422 for invalid option
- [ ] Frontend displays validation error

**4.7 Cleanup Integration Test**

```bash
# Stop all containers
docker stop frontend-integration api-test redis-test postgres-test
docker rm frontend-integration api-test redis-test postgres-test

# Clean up config
rm -rf /tmp/frontend-config
```

---

### 5. Build Validation

**5.1 Verify Bundle Size**

```bash
# Check build output from docker build logs
# Or rebuild to see output:
docker build -t frontend:0.5.0 frontend/ 2>&1 | grep "dist/"

# Expected output:
# dist/index.html                   ~0.90 kB │ gzip:  ~0.51 kB
# dist/assets/index-[hash].css      ~6.31 kB │ gzip:  ~1.89 kB
# dist/assets/index-[hash].js       ~9.05 kB │ gzip:  ~3.53 kB
# dist/assets/vendor-[hash].js    ~140.86 kB │ gzip: ~45.26 kB
```

- [ ] Bundle size acceptable (<10KB for app code, <150KB for vendor)
- [ ] gzip compression applied
- [ ] Assets include content hashes

**5.2 Verify Security Settings**

```bash
# Check nginx config
docker run --rm frontend:0.5.0 cat /etc/nginx/nginx.conf | grep -A5 "add_header"

# Expected headers:
# X-Frame-Options: DENY
# X-Content-Type-Options: nosniff
# X-XSS-Protection: 1; mode=block
# Referrer-Policy: strict-origin-when-cross-origin
# Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; ...
```

- [ ] Security headers configured
- [ ] CSP policy restricts resources
- [ ] DENY clickjacking (X-Frame-Options)

---

## Validation Summary

**Phase 3 Complete When:**
- [ ] All Pre-Flight checks pass
- [ ] Frontend container validation passes (Section 2)
- [ ] Component validation passes (Section 3)
- [ ] API integration validation passes (Section 4)
- [ ] Build validation passes (Section 5)
- [ ] **Unit tests passing** (27/27 component tests) - See Phase 3.5
- [ ] **TDD followed** for all components (tests written first)

**Sign-off:**

- Validator: ___________
- Date: ___________
- Status: [ ] PASS / [ ] FAIL

**Notes:**

---

## Testing Requirements (Phase 3.5)

**Before proceeding, verify Phase 3.5 completion:**

```bash
# Run unit tests
./scripts/run-unit-tests.sh frontend

# Verify coverage
docker run --rm frontend-test:latest npm run test:coverage -- --run

# Expected:
# - 27/27 tests passing
# - 100% component coverage
```

**Phase 3.5 Status:** ✅ COMPLETE
- Testing infrastructure established
- 27 tests passing (VoteButtons: 10, VoteResults: 17)
- 100% component coverage
- TDD workflow documented

See: `docs/sessions/2025-11-17-session-phase3.5-testing.md`

---

## Next Steps

After Phase 3 validation passes:
1. **Phase 4:** Security & Hardening (network policies, scanning, validation)
2. **Phase 5:** Integration Testing (full stack with Helm on Minikube)
3. **Phase 6:** Documentation and production readiness

**Deployment:**
- Local testing: See [DEPLOYMENT.md](DEPLOYMENT.md) for Minikube setup
- Integration tests: Run `./scripts/run-integration-tests.sh`
- Production: Follow DEPLOYMENT.md production section
