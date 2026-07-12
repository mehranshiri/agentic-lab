---
description: "Generate an Architecture Decision Record following the project's ADR template. Run /adr with a description of the decision."
agent: "agent"
---
Generate an Architecture Decision Record following the format established in [docs/adr/README.md](../../docs/adr/README.md).

If the user hasn't provided a clear decision description, ask them to describe what architectural choice was made and why.

## Steps

1. Find the next ADR number by checking the highest numbered file in `docs/adr/` (e.g., if `008-*.md` is the latest, the new one is `009`).
2. Create `docs/adr/NNN-short-slug.md` using the template below.
3. Update the index table in `docs/adr/README.md`.

## Template

```markdown
# ADR-NNN: Short Title

**Status:** Proposed

**Date:** YYYY-MM-DD

**Sprint:** N — Sprint Name

---

## Decisions

### 1. Decision Title

Brief description of what was decided.

**Rationale**

- Why this choice over alternatives
- How it aligns with the project's patterns (SOLID, Strategy, Template Method, Dependency Inversion)

**Trade-offs**

- What we give up
- Known limitations or risks

**Future considerations**

- How this may evolve
- When to revisit or replace this decision
```

## Rules

- **Status** starts as `Proposed` — the user will change it to `Accepted` after review.
- **Rationale** must justify the choice, not just describe it. Use bullet points.
- **Trade-offs** are required — no decision is free. Be honest about downsides.
- Cross-reference related ADRs when a decision builds on or modifies a prior one.
