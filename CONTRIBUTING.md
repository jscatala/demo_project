# Contributing Guide

## Conventional Commits

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification.

### Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

### Types

- **feat:** New feature
- **fix:** Bug fix
- **docs:** Documentation only
- **style:** Code style changes (formatting, no logic change)
- **refactor:** Code refactoring (no feature/fix)
- **perf:** Performance improvements
- **test:** Adding/updating tests
- **build:** Build system changes (Docker, Helm, dependencies)
- **ci:** CI/CD configuration changes
- **chore:** Other changes (maintenance, tooling)

### Examples

```bash
feat(api): add vote validation for cats/dogs options
fix(consumer): prevent duplicate vote processing
docs(adr): add decision record for Redis Streams choice
build(helm): update ingress rate limiting config
```

### Breaking Changes

Append `!` after type or add `BREAKING CHANGE:` in footer:

```bash
feat(api)!: change vote endpoint from POST to PUT

BREAKING CHANGE: Vote endpoint now requires PUT instead of POST
```

## Branch Naming

- `feature/short-description` - New features
- `bugfix/short-description` - Bug fixes
- `hotfix/short-description` - Critical production fixes
- `docs/short-description` - Documentation updates

**Examples:**
- `feature/sse-live-updates`
- `bugfix/redis-connection-leak`
- `docs/update-deployment-guide`

## Development Workflow

1. **Create branch** from `main`
   ```bash
   git checkout -b feature/your-feature
   ```

2. **Make changes** following conventions in [CONVENTIONS.md](docs/CONVENTIONS.md)

3. **Commit** using conventional commits
   ```bash
   git commit -m "feat(frontend): add live results via SSE"
   ```

4. **Test locally**
   ```bash
   helm install test-release ./helm
   # Run integration tests
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature
   ```

6. **PR Requirements:**
   - Descriptive title (conventional commit format)
   - Description of changes
   - Tests passing
   - No security vulnerabilities
   - Code review approval

## Pull Request Process

1. Update CHANGELOG.md under "Unreleased" section
2. Update documentation if needed
3. Ensure all tests pass
4. Obtain at least one approval
5. Squash and merge with conventional commit message

## Code Review Guidelines

**Reviewers should check:**
- Code follows conventions (CONVENTIONS.md)
- Security best practices applied
- Tests cover new functionality
- Documentation updated
- No hardcoded secrets
- Docker images are minimal and non-root

## Questions?

Open an issue or discussion for clarification.
