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
| [004](004-sprint4-tool-discovery.md) | 4 — Tool Discovery | Stateless `ToolCatalog` discovery layer, no caching, queries registry live |
| [005](005-sprint5-provider-tool-representation.md) | 5 — Provider Tool Representation | `ToolSchemaAdapter` ABC, `DeepSeekToolSchemaAdapter`, DIP between tools and LLM |
| [006](006-sprint6-tool-invocation.md) | 6 — Tool Invocation | `ToolInvocation` frozen request, `ToolInvoker` stateless execution boundary |
| [007](007-sprint7-tool-call-bridge.md) | 7 — Tool Call Bridge | `ProviderToolCall` value object, `ToolCallBridge` translation boundary, `ToolCallResult` pairing |
| [008](008-sprint8-conversation-agent-runtime.md) | 8 — Conversation & Agent Runtime | `Conversation` immutable domain, `ConversationRepresentation` strategy, `AgentRuntime` reasoning loop, `AgentResult` |
| [009](009-sprint9-tool-expansion-workspace-safety.md) | 9 — Tool Expansion & Workspace Safety | `ShellTool`, `GrepTool`, workspace boundary enforcement, mandatory `ExecutionContext` in `_resolve`, symlink escape protection |

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