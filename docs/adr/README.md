# Architecture Decision Records

This directory records architecture decisions made during each sprint
so that the team and future contributors can understand **what** was
decided, **why**, and what **trade-offs** were considered.

## Index

| ADR | Sprint | Title |
|-----|--------|-------|
| [001](001-sprint1-project-foundation.md) | 1 — Project Foundation | `uv`, `hatchling`, flat package layout, frozen `Settings` |
| [002](002-sprint2-llm-infrastructure.md) | 2 — LLM Infrastructure | Strategy pattern for providers, `LlmClient` facade, frozen `LLMResponse` |
| [003](003-sprint3-tool-framework.md) | 3 — Tool Framework | Instance-based `ToolRegistry`, Template Method lifecycle, frozen `ToolResult` |

## Format

Each ADR follows a consistent structure:

- **Status** — `Proposed`, `Accepted`, `Deprecated`, or `Superseded`
- **Date** — when the decision was recorded
- **Sprint** — which sprint introduced the decision
- **Decisions** — one or more decisions with:
  - Rationale (why this choice)
  - Trade-offs (what we give up)
  - Future considerations (how it may evolve)

## Usage

When preparing for interviews or onboarding new contributors, these ADRs
provide a direct answer to "Why did you design it this way?" — saving
time and reducing ambiguity.