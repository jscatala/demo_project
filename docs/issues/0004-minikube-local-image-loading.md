# 0004. Minikube Local Image Loading Requirement

Date: 2025-11-15

## Problem

Kubernetes pods enter `ImagePullBackOff` state when deploying locally-built Docker images to Minikube cluster.

**Symptoms:**
- Pods stuck in `ImagePullBackOff` or `ErrImagePull` status
- Helm installation succeeds but pods never reach `Running` state
- Error logs show: `Failed to pull image "frontend:0.1.0": rpc error: code = Unknown desc = Error response from daemon: pull access denied`

**Root cause:**
Minikube runs in isolated VM/container environment with its own Docker daemon, separate from host Docker daemon. Images built on host are not automatically available to Minikube.

**Impact:**
- Phase 1 validation fails at deployment test (section 11.2)
- Confusing for developers expecting Docker images to "just work"
- Blocks local development/testing workflow

## Context

**Setup:**
- Docker images built locally: `frontend:0.1.0`, `api:0.1.0`, `consumer:0.1.0`
- Minikube cluster with dedicated profile for project
- Helm chart references local image tags (no registry)

**What we tried:**
1. Built images on host with `docker build -t frontend:0.1.0`
2. Verified images exist with `docker images | grep frontend`
3. Deployed via Helm: `helm install voting-app helm/`
4. **Result:** Pods fail to pull images

**Why this happens:**
Minikube uses one of these drivers, each with isolated Docker daemon:
- Docker driver: Container-in-container, separate Docker socket
- VirtualBox/VMware: Separate VM with own Docker
- Hyperkit: Isolated hypervisor instance

Kubernetes tries to pull images from Minikube's daemon, which doesn't have our locally-built images.

## Alternatives Considered

### Alternative 1: Use imagePullPolicy: Never

**Description:**
Set `imagePullPolicy: Never` in all Deployments/StatefulSets/Jobs to prevent pull attempts.

**Pros:**
- Forces Kubernetes to use only local images
- Fails fast if image missing

**Cons:**
- Still requires loading images into Minikube
- Doesn't solve the core problem
- Brittle - fails silently if image missing from node

**Why not chosen:**
Doesn't transfer images to Minikube daemon - pods still can't find images.

---

### Alternative 2: Push to Local Registry (Harbor/Registry:2)

**Description:**
Run local container registry, push images, configure Minikube to pull from it.

**Pros:**
- Mimics production workflow
- Supports multi-node clusters
- Works with image pull policies

**Cons:**
- Complex setup (registry deployment, TLS/auth config)
- Requires network configuration
- Overkill for simple local dev
- Extra infrastructure to maintain

**Why not chosen:**
Too much complexity for local development testing. Better suited for integration/staging environments.

---

### Alternative 3: Use `minikube image load`

**Description:**
Directly load Docker images from host into Minikube's Docker daemon.

```bash
minikube image load frontend:0.1.0 --profile=voting-demo
minikube image load api:0.1.0 --profile=voting-demo
minikube image load consumer:0.1.0 --profile=voting-demo
```

**Pros:**
- Simple, single command per image
- No configuration changes needed
- Works with all Minikube drivers
- Fast transfer (uses Docker save/load internally)
- Images immediately available to Kubernetes

**Cons:**
- Manual step after each image rebuild
- Must remember to reload on changes
- Profile-specific (must specify correct profile)

**Why chosen:**
- **Simplest solution** for local development
- **No Helm changes** - keeps charts portable
- **Fast workflow** - quick iteration cycle
- **Clear mental model** - explicit image transfer

---

### Alternative 4: Use `minikube docker-env`

**Description:**
Point host Docker CLI to Minikube's Docker daemon, build images directly inside Minikube.

```bash
eval $(minikube docker-env --profile=voting-demo)
docker build -t frontend:0.1.0 frontend/
```

**Pros:**
- Images built directly in Minikube daemon
- No separate load step needed
- Automatic availability to Kubernetes

**Cons:**
- Pollutes Minikube daemon with build layers/cache
- Confusing - host Docker state differs from Minikube state
- Must remember to set/unset env vars
- Breaks host Docker workflows while active
- Build artifacts persist in Minikube (fills disk)

**Why not chosen:**
Confusing developer experience - easy to forget which Docker daemon you're using, leading to "missing image" confusion.

## Solution

**Use `minikube image load` to explicitly transfer images to Minikube daemon.**

**Description:**
After building images locally, load them into Minikube's Docker daemon before Helm install.

**Implementation:**

Updated PHASE1_VALIDATION.md section 11.2 to include image loading:

```bash
# Load locally-built images into Minikube (required for local development)
minikube image load frontend:0.1.0 --profile=voting-demo
minikube image load api:0.1.0 --profile=voting-demo
minikube image load consumer:0.1.0 --profile=voting-demo

# Verify images loaded
minikube ssh --profile=voting-demo "docker images | grep -E '(frontend|api|consumer)'"

# Install the chart
helm install voting-app helm/
```

**Why chosen:**
- Clear separation: build on host, load to Minikube
- Explicit transfer step - developer knows what's happening
- No Helm chart modifications needed
- Works consistently across Minikube drivers
- Easy to script/automate

**Trade-offs accepted:**
- Manual step after image rebuilds (could be scripted)
- Must remember profile name

## Outcome

**What changed:**
- Added image loading step to validation workflow
- Documented requirement in PHASE1_VALIDATION.md (line 587 note)
- Added verification command to confirm images loaded

**Validation results:**
- All pods reach `Running` state after image load
- No `ImagePullBackOff` errors
- Successful end-to-end deployment

**Follow-up actions:**
- [X] Document in validation checklist
- [ ] Create helper script: `scripts/load-images-to-minikube.sh`
- [ ] Add to HANDOFF_GUIDE.md "Local Development" section
- [ ] Consider Makefile target: `make minikube-load-images`

**Lessons learned:**
1. **Minikube isolation is strict** - No automatic image sharing with host Docker
2. **Explicit > Implicit** - `minikube image load` makes transfer obvious
3. **Profile awareness matters** - Always specify `--profile` for multi-cluster setups
4. **Verify before deploy** - Check images exist in Minikube before Helm install
5. **Local != Production** - Accept different workflows for local dev vs. production (local: load images; prod: pull from registry)

## References

- Minikube image docs: https://minikube.sigs.k8s.io/docs/handbook/pushing/#4-pushing-directly-to-the-in-cluster-docker-daemon-docker-env
- Validation document: `docs/PHASE1_VALIDATION.md` (line 587)
- System requirements: `system_requirements.txt` (minikube setup assumption)
