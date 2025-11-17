# Working with AI Assistants - Handoff Guide

Quick reference for resuming work with AI assistants on this project.

## Starting a New Session

### Quick Start Template

```
I'm resuming work on the voting app project. Here's where we left off:

Last session: @docs/sessions/[latest-session].md
Current todos: @Demo_project/todos.md
System requirements: @Demo_project/system_requirements.txt

Ready to continue with [next task from todos].
```

### Essential Context Files

Reference these files using `@` syntax to provide context:

**Always include:**
- `@Demo_project/todos.md` - Current task list and priorities
- `@docs/sessions/[latest-session].md` - Last session summary

**Include when relevant:**
- `@Demo_project/system_requirements.txt` - Original requirements
- `@docs/TESTING.md` - Testing guide (TDD workflow, examples)
- `@docs/adr/` - Architectural decisions
- `@docs/issues/` - Problems encountered and solutions
- `@Demo_project/CONVENTIONS.md` - Code standards and TDD principles
- `@Demo_project/README.md` - Project overview

## Session Workflow

### 1. Resume Context
```
Last session: @docs/sessions/2025-11-15-session-05-validation-prep.md
Next task: Starting Phase 2
```

### 2. Work on Tasks
- **TDD Required:** Write tests BEFORE implementation (Red-Green-Refactor)
- Reference current phase in `@todos.md`
- Follow conventions in `@CONVENTIONS.md` (includes TDD principles)
- Use Conventional Commits (see `@CONTRIBUTING.md`)
- Run tests: `./scripts/run-unit-tests.sh` (Docker-based)

### 3. End Session
Ask the AI to:
```
Create a session log for today's work in docs/sessions/
Update todos.md with completed tasks
```

## File Navigation Map

```
Demo_project/
├── README.md                           # Start here for overview
├── system_requirements.txt             # Original requirements
├── todos.md                           # ⭐ Current task tracking
├── CHANGELOG.md                       # Version releases only
├── CONTRIBUTING.md                    # Git workflow, commits
│
├── docs/
│   ├── HANDOFF_GUIDE.md              # ⭐ This file (resuming work)
│   ├── CONVENTIONS.md                # Code standards
│   │
│   ├── sessions/                      # ⭐ Session history
│   │   ├── README.md                  # Session index
│   │   └── YYYY-MM-DD-session-NN.md  # Daily logs
│   │
│   ├── adr/                           # Architectural decisions
│   │   ├── 0001-*.md
│   │   └── 0002-*.md
│   │
│   └── issues/                        # ⭐ Problems & solutions
│       ├── README.md                  # Issue index
│       └── NNNN-*.md                  # Problem logs
│
├── helm/                              # K8s manifests
├── frontend/                          # TypeScript UI
├── api/                               # FastAPI service
└── consumer/                          # Python event processor
```

## Common Resume Scenarios

### Scenario 1: Continuing Implementation
```
Resuming work on Phase 2 (Backend Core).

Context:
- Last session: @docs/sessions/[latest].md
- Current todos: @Demo_project/todos.md
- Next task: Implement POST /vote endpoint

Ready to continue.
```

### Scenario 2: Debugging/Fixing Issues
```
Found an issue with [component].

Context:
- Error logs: [paste logs]
- Relevant file: @path/to/file.py
- Last session: @docs/sessions/[latest].md
- Conventions: @docs/CONVENTIONS.md

Need help debugging.
```

### Scenario 3: New Feature
```
Adding new feature: [description]

Context:
- Requirements: @system_requirements.txt
- ADRs: @docs/adr/
- Conventions: @docs/CONVENTIONS.md

Should I create an ADR for this?
```

### Scenario 4: Code Review
```
Review this implementation:

Context:
- File: @path/to/implementation.py
- Conventions: @docs/CONVENTIONS.md
- Requirements: @system_requirements.txt

Check for security issues and standards compliance.
```

## Context Efficiency Tips

### ✅ DO:
- Use `@` syntax to reference files directly
- Reference latest session log for continuity
- Point to specific phases in todos.md
- Mention relevant ADRs by number

### ❌ DON'T:
- Paste entire file contents (use `@` instead)
- Re-explain architecture (ADRs have it)
- Repeat standards (reference CONVENTIONS.md)
- Lose session history (always log before ending)

## Decision Tracking

**When we make decisions:**

| Type | Document In | Example |
|------|-------------|---------|
| Architectural | ADR (docs/adr/) | "Why Redis Streams?" |
| Problem/Issue | Issue log (docs/issues/) | "Namespace security approach" |
| Daily/Minor | Session log | "Used asyncpg over SQLAlchemy" |
| Code standard | CONVENTIONS.md | "Line length: 88 chars" |
| Version change | CHANGELOG.md | "v1.0.0: Added feature X" |

## Quick Reference Commands

### Finding Information

```bash
# Last session
ls -lt docs/sessions/*.md | head -1

# Current phase
grep "## Phase" todos.md

# Recent decisions
ls -lt docs/adr/*.md
```

### Starting Session (Template)

```
Resuming work on the voting app.

Last session: @docs/sessions/[latest].md
Todos: @Demo_project/todos.md

Next up: [task description from todos.md]

Let's continue.
```

### Ending Session (Template)

```
Please:
1. Create session log for today in docs/sessions/
2. Update todos.md with completed tasks
3. Note any decisions made
4. List next steps for next session
```

## Session Log Format

Each session should capture:
- **Date and title**
- **What was done** (completed tasks)
- **Decisions made** (link to ADRs if major)
- **Files created/modified**
- **Next steps** (for easy resume)
- **Context summary** (quick reference)

See `docs/sessions/README.md` for session index.

## Getting Help

**If context is unclear:**
```
More context needed. Please reference:
- @docs/sessions/[specific-session].md
- @specific/file/path
```

**If decisions were made offline:**
```
We decided to [decision]. Please update:
- Create ADR if architectural
- Update session log
- Update todos.md if scope changed
```

## Version Control

**AI Assistant Rules:**
- ❌ NO "Generated with Claude Code" or similar AI attribution in commits
- ❌ NO "Co-Authored-By: Claude" footers
- ❌ NO "Modified by Claude" or AI references in file comments
- ✅ Clean code only, standard Conventional Commits format

**Before committing:**
1. Ensure CHANGELOG.md updated (if releasing)
2. Session log created for work done
3. Todos.md reflects current state
4. Conventional commit message

**Example commit:**
```bash
git commit -m "feat(api): implement POST /vote endpoint

- Validates cats/dogs input
- Writes to Redis Stream
- Includes rate limiting

Session: docs/sessions/2025-11-15-session-02.md"
```

## Testing

**TDD is mandatory for all new features.**

### Quick Test Commands

```bash
# Unit tests (Docker-based)
./scripts/run-unit-tests.sh [frontend|api|consumer|all]

# Integration tests (Minikube)
./scripts/run-integration-tests.sh

# Coverage report
docker run --rm frontend-test:latest npm run test:coverage -- --run
```

### TDD Workflow

1. **🔴 Red:** Write failing test first
2. **🟢 Green:** Write minimal code to pass
3. **🔵 Refactor:** Improve while tests pass

See `@docs/TESTING.md` for detailed examples.

## Questions?

See:
- Testing guide: `@docs/TESTING.md`
- Project overview: `@README.md`
- Contributing guide: `@CONTRIBUTING.md` (includes TDD workflow)
- Conventions: `@docs/CONVENTIONS.md` (includes TDD principles)
- Architecture: `@docs/adr/`
