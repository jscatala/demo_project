# Issue 0002: Dockerfile Non-Root User Permission Errors

**Status:** ✓ Resolved
**Date Opened:** 2025-11-15
**Date Resolved:** 2025-11-15
**Severity:** High (blocking container execution)
**Category:** Security / Container Build

## Problem Statement

Containers for `api` and `consumer` services failed to start due to permission errors when running as non-root user (UID 1000). The error occurred because Python dependencies were installed to `/root/.local` in the builder stage but the production container ran as a non-root user who couldn't access root-owned directories.

### Error Message

```
/usr/local/bin/python3.11: can't open file '/root/.local/bin/uvicorn': [Errno 13] Permission denied
```

### Affected Services

- `api/` - FastAPI application
- `consumer/` - Python event processor

## Root Cause

**Dockerfile anti-pattern identified:**

1. Builder stage installed packages as root → `/root/.local`
2. Production stage copied `/root/.local` (owned by root)
3. Created non-root user `appuser` (UID 1000)
4. Switched to `USER 1000`
5. User 1000 couldn't access root-owned `/root/.local/bin`

**Problematic code:**
```dockerfile
# Build stage
RUN pip install --user --no-cache-dir -r requirements.txt

# Production stage
COPY --from=builder /root/.local /root/.local  # ← Root-owned
RUN useradd -m -u 1000 appuser
ENV PATH=/root/.local/bin:$PATH  # ← User can't access
USER 1000  # ← Permission denied!
```

## Security Implications

- **Good:** Non-root execution prevents container breakout escalation
- **Bad:** Broken implementation blocked legitimate application startup
- **Risk:** Could lead to developers running as root (worse security)

## Solution Implemented

**Pattern: Create user before copying, copy to user's home with ownership**

```dockerfile
# Production stage
FROM python:3.11-slim

WORKDIR /app

# Create non-root user first
RUN useradd -m -u 1000 appuser

# Copy dependencies to appuser's home with proper ownership
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Copy application code with ownership
COPY --chown=appuser:appuser main.py .

# Update PATH to user's local bin
ENV PATH=/home/appuser/.local/bin:$PATH

# Switch to non-root user
USER 1000
```

**Key changes:**
1. ✓ Create user **before** copying files
2. ✓ Use `--chown=appuser:appuser` when copying
3. ✓ Copy to `/home/appuser/.local` (user-owned directory)
4. ✓ Update PATH to `/home/appuser/.local/bin`

## Files Modified

```
api/Dockerfile (lines 10-28)
consumer/Dockerfile (lines 12-28)
```

## Testing Performed

### Before Fix
```bash
docker run --rm api:0.1.0
# Error: Permission denied accessing /root/.local/bin/uvicorn
```

### After Fix
```bash
docker run --rm -d --name api-test api:0.1.0
docker logs api-test
# Success: INFO: Uvicorn running on http://0.0.0.0:8000
docker stop api-test
```

**Test results:**
- ✓ API container starts successfully
- ✓ Consumer container runs continuously
- ✓ No permission errors
- ✓ Processes run as UID 1000 (verified with `ps aux` in container)

## Best Practices Established

### For Future Dockerfiles

**Pattern for non-root multistage builds:**
```dockerfile
# 1. Build stage (as root is fine)
FROM base AS builder
RUN pip install --user -r requirements.txt  # → /root/.local

# 2. Production stage
FROM base
WORKDIR /app

# 3. Create user FIRST
RUN useradd -m -u 1000 appuser

# 4. Copy WITH ownership
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser app/ .

# 5. PATH points to user's bin
ENV PATH=/home/appuser/.local/bin:$PATH

# 6. Switch to user
USER 1000
```

**Checklist:**
- [ ] User created before copying files
- [ ] All COPY uses `--chown=appuser:appuser`
- [ ] Dependencies copied to `/home/appuser/.local`
- [ ] PATH includes `/home/appuser/.local/bin`
- [ ] Tested with `docker run` (not just build)

## Related Documentation

- **Convention:** Non-root containers (`docs/CONVENTIONS.md`)
- **Session:** Session 02 (`docs/sessions/2025-11-15-session-02-phase1-implementation.md`)
- **Commit:** fix(docker): correct non-root user permissions in Dockerfiles

## Lessons Learned

1. **Test execution, not just builds** - Images built successfully but failed at runtime
2. **Ownership matters** - File permissions critical for non-root containers
3. **PATH configuration** - Must point to user-accessible directories
4. **Order of operations** - Create user before copying files ensures correct ownership

## Prevention

- Add to PR review checklist: "Non-root Dockerfiles tested with `docker run`"
- Document pattern in `docs/CONVENTIONS.md` Docker section
- Use this issue as reference for future container security work

---

**Resolution:** Fixed in commit `fix(docker): correct non-root user permissions in Dockerfiles`

**Impact:** Unblocks Phase 1 Priority 2 completion, enables Deployment testing in Priority 3.
