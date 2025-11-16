# Git Tagging Strategy

This document defines the strategy for creating and managing Git tags for component versions.

## Tag Naming Convention

**Format:** `<component>-v<semver>`

**Examples:**
- `api-v0.3.0`
- `consumer-v0.2.0`
- `frontend-v0.1.0`

**Components:**
- `api` - FastAPI backend service
- `consumer` - Event consumer service
- `frontend` - TypeScript/React frontend application

## When to Create Tags

Create an annotated tag when:

1. **Version bump in commit message** - Commit includes "Version bump: component:X.Y.Z"
2. **Docker image built** - New Docker image created with version tag
3. **Helm values updated** - Component version updated in `helm/values.yaml`

**Trigger point:** After committing code that bumps the version, immediately create the tag.

## Tag Format

### Annotated Tags (Required)

Always use annotated tags (never lightweight tags) for version tracking.

```bash
git tag -a <component>-v<version> <commit-hash> -m "Message"
```

### Tag Message Structure

**Format:**
```
Component vX.Y.Z - Brief Title

Brief description of what this version delivers.

Features:
- Feature 1
- Feature 2
- Feature 3

Image: component:X.Y.Z (size)
Date: YYYY-MM-DD
```

**Example:**
```
API v0.3.0 - POST /vote Endpoint

First production API endpoint implementing vote submission.

Features:
- POST /api/vote endpoint with Pydantic validation
- Redis Streams integration (XADD)
- 6 unit tests with mocked Redis

Image: api:0.3.0 (274MB)
Date: 2025-11-15
```

## Creating Tags

### For Current Commit

```bash
# Tag the current HEAD commit
git tag -a api-v0.3.0 -m "$(cat <<'EOF'
API v0.3.0 - POST /vote Endpoint

Features:
- POST /api/vote endpoint
- Redis Streams integration
- Unit tests

Image: api:0.3.0
Date: 2025-11-15
EOF
)"
```

### For Historical Commit

```bash
# Tag a specific commit by hash
git tag -a consumer-v0.2.0 fe2aded -m "Message here"
```

### Using Heredoc for Multi-line Messages

```bash
git tag -a <tag-name> <commit> -m "$(cat <<'EOF'
Component vX.Y.Z - Title

Description line 1
Description line 2

Features:
- Feature A
- Feature B

Image: component:X.Y.Z
Date: YYYY-MM-DD
EOF
)"
```

## Listing Tags

```bash
# List all tags
git tag

# List tags with first 3 lines of annotation
git tag -l -n3

# Show full annotation for specific tag
git show api-v0.3.0
```

## Pushing Tags

### Push Specific Tag

```bash
git push origin api-v0.3.0
```

### Push All Tags

```bash
git push --tags
```

**Note:** Only push tags after verifying they're correct. Tags are harder to change once pushed.

## Deleting Tags

### Delete Local Tag

```bash
git tag -d api-v0.3.0
```

### Delete Remote Tag

```bash
git push origin :refs/tags/api-v0.3.0
```

**Warning:** Only delete tags that haven't been used in production.

## Workflow Example

### Scenario: Implementing a New Feature

1. **Develop feature** in working directory
2. **Update version** in component (e.g., main.py: version="0.4.0")
3. **Update helm/values.yaml** with new image tag
4. **Build Docker image** with new version tag
5. **Test Docker image** locally
6. **Commit changes** with conventional commit message including "Version bump: component:X.Y.Z"
7. **Create annotated tag** immediately after commit:
   ```bash
   git tag -a api-v0.4.0 -m "$(cat <<'EOF'
   API v0.4.0 - New Feature

   Description of what changed.

   Features:
   - New feature X
   - Enhancement Y

   Image: api:0.4.0 (size)
   Date: YYYY-MM-DD
   EOF
   )"
   ```
8. **Push commit and tag** to remote

## Semantic Versioning

Follow [Semantic Versioning](https://semver.org/) for component versions:

- **MAJOR (X.0.0):** Breaking changes, incompatible API changes
- **MINOR (0.X.0):** New features, backwards-compatible
- **PATCH (0.0.X):** Bug fixes, backwards-compatible

**Examples:**
- `0.3.0` → `0.4.0` - New endpoint added (minor)
- `0.3.0` → `0.3.1` - Bug fix (patch)
- `0.3.0` → `1.0.0` - Breaking API change (major)

## Version Independence

Each component maintains its own version number independently:

- API can be at v0.5.0
- Consumer can be at v0.3.0
- Frontend can be at v0.2.0

This allows components to evolve at different rates.

## Current Tags

### API Tags

- `api-v0.3.0` (c8a6a31) - POST /vote endpoint
- `api-v0.3.1` (96957f0) - GET /results endpoint
- `api-v0.3.2` (7be956b) - Security hardening

### Consumer Tags

- `consumer-v0.2.0` (fe2aded) - Production Dockerfile
- `consumer-v0.3.0` (00bd2d2) - Redis Streams processor

### Frontend Tags

- (None yet - pending Phase 3 implementation)

## Best Practices

1. **Always use annotated tags** - Include descriptive messages
2. **Tag immediately after version bump commit** - Don't delay tagging
3. **Include feature list** - What's new in this version
4. **Reference image size** - Track Docker image optimization
5. **Date stamp** - Know when version was created
6. **Verify before pushing** - Check tag annotation is correct
7. **Never force-push tags** - Tags should be immutable
8. **Document in CHANGELOG** - Cross-reference tags in CHANGELOG.md

## References

- Git tagging: https://git-scm.com/book/en/v2/Git-Basics-Tagging
- Semantic Versioning: https://semver.org/
- Conventional Commits: https://www.conventionalcommits.org/
