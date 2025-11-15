# Next Session Resume Prompt

Copy and paste this prompt at the start of your next session:

---

## Session Resume Prompt

I'm resuming work on the voting app project (Cats vs Dogs).

**Context files to review:**
- @Demo_project/docs/HANDOFF_GUIDE.md - Project handoff workflow
- @Demo_project/README.md - Project overview and architecture
- @Demo_project/todos.md - Current task tracking
- @Demo_project/docs/sessions/2025-11-15-session-04-priority4-infrastructure.md - Last session

**Current state:**
- Phase 1 (K8s Foundation): ✓ Complete (all 4 priorities)
- Validation: Manual protocol created in @Demo_project/docs/PHASE1_VALIDATION.md
- Next: Phase 2 (Backend Core) - API and consumer implementation

**Phase 2 objectives:**
1. Enhance FastAPI application:
   - POST /vote endpoint → writes to Redis Stream
   - GET /results endpoint → reads from PostgreSQL
   - Input validation (cats/dogs only)
   - Security headers, CORS, rate limiting

2. Enhance Python consumer:
   - Read from Redis Stream (XREADGROUP)
   - Process vote events
   - Write to PostgreSQL (prepared statements)

**Technical context:**
- PostgreSQL schema: Already defined in ConfigMap with increment_vote() function
- Redis Streams: Stream 'votes', consumer group 'vote-processors' configured
- Event flow: API → Redis → Consumer → PostgreSQL
- All containers run as UID 1000 (non-root)
- Images: frontend:0.1.0, api:0.1.0, consumer:0.1.0

**Important notes:**
- NO references to AI tools in any code, commits, or documentation
- Follow Conventional Commits format
- Update session logs and todos as work progresses
- Document decisions in ADRs if architectural

Ready to start Phase 2 implementation.

---

## Alternative Shorter Prompt

If you prefer a more concise version:

---

Resuming voting app project.

Context:
- Last session: @Demo_project/docs/sessions/2025-11-15-session-04-priority4-infrastructure.md
- Todos: @Demo_project/todos.md
- Handoff guide: @Demo_project/docs/HANDOFF_GUIDE.md

Phase 1 complete. Starting Phase 2: Backend Core.

Tasks:
1. Implement POST /vote endpoint (FastAPI → Redis Stream)
2. Implement GET /results endpoint (PostgreSQL → API)
3. Implement consumer (Redis Stream → PostgreSQL)
4. Add dependencies: redis>=5.0.0, asyncpg>=0.29.0

Current app status: Hello-world stubs, need real logic.

Ready to begin.

---
