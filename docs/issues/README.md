# Issues & Solutions Log

Record of problems encountered during development with alternatives considered and solutions implemented.

## Purpose

This log tracks:
- **Problems/Issues** discovered during development
- **Alternatives** evaluated
- **Solutions** chosen and implemented
- **Outcomes** and follow-up actions

**Difference from ADRs:**
- **ADRs:** Architectural decisions (what to build)
- **Issues:** Problems encountered (what went wrong, how we solved it)

## Format

Each issue follows the template in `template.md`:
- Problem description
- Context and impact
- Alternatives considered
- Solution implemented
- Outcome and references

## Issue Index

### 2025-11-15

**Issue 0001 - Namespace Security Isolation**
- File: `0001-namespace-security-isolation.md`
- Problem: Single namespace approach lacks security boundaries
- Solution: Layer-based namespaces with network policies
- Status: ✓ Resolved (see ADR-0004)

---

## How to Use

**When encountering a problem:**

1. Create new issue file: `NNNN-brief-description.md`
2. Use template from `template.md`
3. Document problem, alternatives, and solution
4. Update this README index
5. Reference in session log
6. Link related ADRs if applicable

**Numbering:** Sequential starting from 0001

## Quick Reference

**Latest issue:** `0001-namespace-security-isolation.md`

**Common problem categories:**
- Security
- Performance
- Architecture
- Development workflow
- Integration
- Deployment
