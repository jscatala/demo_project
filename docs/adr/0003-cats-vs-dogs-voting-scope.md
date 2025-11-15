# 3. Cats vs Dogs as Fixed Voting Options

Date: 2025-11-15

## Status

Accepted

## Context

The voting application needs to define:
- What users are voting for
- Number of options
- Whether options are configurable or hardcoded

**Requirements:**
- MVP scope (proof of concept for event-driven architecture)
- Need concrete options to build UI/backend
- May expand to configurable options later

**Considerations:**
- Hardcoding simplifies MVP development
- Dynamic options add database complexity
- Two options sufficient to validate architecture

## Decision

**Hardcode exactly two voting options: "Cats" and "Dogs"**

**Implementation:**
- Frontend: Two buttons labeled "Cats" and "Dogs"
- API validation: Reject any vote not in `["cats", "dogs"]`
- Database schema: Simple counts table
- Results display: Two bars/percentages

**No dynamic option management in v1.0**

## Consequences

### Positive
- **Simple implementation:** No admin UI for managing options
- **Clear validation:** Easy to validate input (`if option not in ["cats", "dogs"]`)
- **Focused MVP:** Validates architecture without complexity
- **Fast development:** No need for options CRUD API
- **Known UI layout:** Fixed two-column display

### Negative
- **Not extensible:** Cannot add "Birds" without code changes
- **Hardcoded strings:** Options in multiple places (frontend, backend, tests)
- **Limited demo value:** Less impressive than configurable system

### Neutral
- **Database schema simple:** `CREATE TABLE votes (id, option VARCHAR, count INT)`
- **Future work:** Can refactor to dynamic options in v2.0

## Alternatives Considered

### Dynamic options via database
- **Pros:** Flexible, impressive demo, real-world pattern
- **Rejected:** Adds complexity (admin UI, migrations), overkill for MVP

### Three+ options
- **Pros:** Shows system handles multiple options
- **Rejected:** Two sufficient to prove concept, simpler UI

### User-submitted options
- **Pros:** Maximum flexibility, viral potential
- **Rejected:** Moderation needed, abuse risk, far beyond MVP scope

## Migration Path

Future extension to dynamic options:
1. Add `options` table: `id, name, created_at`
2. Add `votes` foreign key to `options.id`
3. Create admin API: POST/GET/DELETE `/api/options`
4. Update frontend to fetch options dynamically
5. Keep "Cats vs Dogs" as default seed data

## References

- `system_requirements.txt`: Specifies two-option UI layout
- ADR-0002: Redis Streams (works with any number of options)
