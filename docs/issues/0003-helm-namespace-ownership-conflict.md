# 0003. Helm Namespace Ownership Conflict

Date: 2025-11-15

## Problem

Helm installation fails when namespaces are pre-created manually with `kubectl apply`, causing validation workflow to break.

**Error message:**
```
Error: INSTALLATION FAILED: Unable to continue with install: Namespace "voting-api"
in namespace "" exists and cannot be imported into the current release: invalid
ownership metadata; label validation error: key "app.kubernetes.io/managed-by"
must equal "Helm": current value is "helm"; annotation validation error: missing
key "meta.helm.sh/release-name": must be set to "voting-app"; annotation validation
error: missing key "meta.helm.sh/release-namespace": must be set to "default"
```

**Impact:**
- Validation workflow section 11.1 creates namespaces manually
- Section 11.2 Helm install fails due to ownership conflict
- Breaks automated deployment workflows
- Creates confusion about resource ownership

## Context

Phase 1 validation protocol (section 11.1) instructs users to manually create namespaces before Helm installation to verify namespace manifests:

```bash
kubectl apply -f helm/templates/namespaces/
```

However, when Helm attempts to install the chart, it cannot adopt these pre-existing namespaces because they lack proper Helm ownership metadata:
- **Manual creation adds:** `managed-by: "helm"` (lowercase, wrong key)
- **Helm expects:** `app.kubernetes.io/managed-by: "Helm"` (proper key + capitalized)
- **Missing annotations:** `meta.helm.sh/release-name`, `meta.helm.sh/release-namespace`

This is a workflow design issue - the validation process tests namespace creation in isolation, then conflicts with Helm's resource management.

## Alternatives Considered

### Alternative 1: Add Helm Labels/Annotations to Namespace Manifests

**Description:**
Pre-populate namespace manifests with Helm ownership labels and annotations using templating.

**Pros:**
- Allows pre-creation of namespaces
- Maintains current validation workflow
- Namespaces properly labeled from start

**Cons:**
- Requires hardcoding release name/namespace in templates
- Breaks Helm's dynamic metadata injection
- Creates tight coupling between manifests and release name
- Non-portable across different release names

**Why not chosen:**
Violates Helm best practices - ownership metadata should be injected at install time, not hardcoded.

---

### Alternative 2: Use `--adopt-resources` Flag (Helm 3.13+)

**Description:**
Use Helm's resource adoption feature to import existing resources.

**Pros:**
- Allows pre-existing resources
- Helm adds ownership metadata automatically
- Maintains validation workflow

**Cons:**
- Requires Helm 3.13+ (not universally available)
- Adds complexity to installation instructions
- Not all resource types support adoption
- Still experimental feature

**Why not chosen:**
Version dependency and experimental status make this unreliable for production workflows.

---

### Alternative 3: Delete and Recreate via Helm

**Description:**
Remove manually created namespaces before Helm installation, let Helm manage all resources.

**Pros:**
- Clean ownership chain
- No metadata conflicts
- Follows Helm best practices
- Works with all Helm versions

**Cons:**
- Requires extra cleanup step
- Cannot validate namespace creation independently

**Why chosen:**
- Simplest and most reliable solution
- Follows Helm's intended resource management model
- No version dependencies
- Clear ownership boundaries

## Solution

**Update validation workflow to delete manually created namespaces before Helm install.**

**Description:**
Modify PHASE1_VALIDATION.md section 11.2 to include namespace cleanup before installation.

**Implementation:**

Updated section 11.2:
```bash
# Delete manually created namespaces (if section 11.1 was executed)
kubectl delete namespace voting-frontend voting-api voting-consumer voting-data 2>/dev/null || true

# Install the chart (Helm will create and manage namespaces)
helm install voting-app helm/

# Watch deployment
kubectl get pods --all-namespaces | grep voting
```

**Why chosen:**
- Simplest solution with no dependencies
- Maintains clean resource ownership
- Works across all Helm versions
- Follows Helm best practices

**Trade-offs accepted:**
- Cannot validate namespace creation independently from Helm install
- Adds extra step to validation workflow

## Outcome

**What changed:**
- Updated `docs/PHASE1_VALIDATION.md` section 11.2
- Added cleanup step before Helm install
- Added explanatory comment in validation script
- Documented in validation error log (line 585)

**Validation results:**
- Helm installation succeeds after namespace deletion
- All resources created with proper ownership metadata
- Clean uninstall/reinstall workflow

**Follow-up actions:**
- [X] Document issue in validation checklist
- [X] Update PHASE1_VALIDATION.md with solution
- [ ] Consider creating pre-flight check script that detects conflicting namespaces
- [ ] Add warning in HANDOFF_GUIDE.md about manual resource creation

**Lessons learned:**
1. **Helm ownership is strict** - Resources must be created by Helm or properly adopted
2. **Validation isolation creates conflicts** - Testing individual manifests separately from chart installation can cause ownership issues
3. **Let Helm manage Helm resources** - Don't manually create resources that Helm templates define unless using adoption mechanisms
4. **Document workflow order** - Clear sequence of operations prevents conflicts

## References

- Validation document: `docs/PHASE1_VALIDATION.md` (section 11.2, line 584-585)
- Helm ownership documentation: https://helm.sh/docs/topics/charts/#helm-and-kubernetes-resources
- Related session: `docs/sessions/2025-11-15-session-05-validation-prep.md`
