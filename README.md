# Agentic Lab

An educational project for learning agentic AI architecture by building a
production-grade AI Software Engineer from the ground up — no frameworks,
no magic, just clean architecture and deliberate design decisions.

The project explores how to design, implement, and operate an autonomous
software engineering agent through progressive sprints, each introducing
one architectural concept at a time.

## Philosophy

This is a **learning-first** project. Every sprint introduces a single
architectural concept — strategy patterns, dependency inversion, immutable
domain models, boundary enforcement — before moving to the next. The goal
is deep understanding of *why* agentic systems are designed the way they
are, not just *what* they do.

Key principles:

- **No frameworks** — no LangChain, no LangGraph, no CrewAI. Every
  abstraction is built from scratch and justified by a real need.
- **Sprint-first development** — every feature, domain concept, or
  architectural change starts with a sprint document (`docs/sprintN.md`)
  and an Architecture Decision Record (`docs/adr/`).
- **Domain-first design** — abstractions emerge from discovering real
  domain concepts, not from making the architecture look flexible.
- **Provider independence** — the agent's tools, conversations, and
  prompts never depend on a specific LLM provider.

## Capabilities

The agent operates within a designated workspace and can:

- **Read files** — inspect any file within the workspace
- **Write files** — create or overwrite files
- **Search code** — regex-based search across the codebase
- **Execute shell commands** — run tests, lint, builds, git operations
- **Reason in a loop** — the agent iterates: call tools → get results →
  decide next step → repeat until done

All file operations are **workspace-bounded** — path traversal outside the
workspace root is prevented, including symlink escapes.

## Project Status

🚧 **Sprint 10 completed** — System Prompts

## Architecture

```
app/main.py                 ◄── Composition root (thin wiring)
      │
      ├── agent/            ◄── Agent runtime
      │   ├── runtime.py         AgentRuntime (reasoning loop)
      │   └── result.py          AgentResult (frozen outcome)
      │
      ├── conversation/     ◄── Conversation domain (provider-independent)
      │   └── models.py          Conversation, Message, MessageRole, ToolCall
      │
      ├── prompts/          ◄── System prompt domain (provider-independent)
      │   ├── models.py          InstructionBlock, SystemPrompt
      │   └── assembler.py       SystemPromptAssembler
      │
      ├── llm/              ◄── LLM infrastructure (Strategy pattern)
      │   ├── base.py            LlmProvider (ABC)
      │   ├── client.py          LlmClient (facade)
      │   ├── response.py        LLMResponse (value object)
      │   ├── conversation_representation.py  ConversationRepresentation (ABC)
      │   ├── provider_tool_call.py           ProviderToolCall
      │   ├── tool_call_bridge.py             ToolCallBridge, ToolCallResult
      │   ├── providers/         DeepSeekProvider
      │   └── representations/   ToolSchemaAdapter (ABC), SystemPromptAdapter (ABC)
      │                          DeepSeekToolSchemaAdapter, DeepSeekSystemPromptAdapter
      │
      ├── tools/            ◄── Tool Framework
      │   ├── base.py            Tool (ABC — Template Method)
      │   ├── metadata.py        ToolMetadata (frozen dataclass)
      │   ├── result.py          ToolResult (frozen dataclass)
      │   ├── registry.py        ToolRegistry
      │   ├── catalog.py         ToolCatalog (discovery layer)
      │   ├── invocation.py      ToolInvocation
      │   ├── invoker.py         ToolInvoker
      │   ├── execution_context.py  ExecutionContext
      │   ├── filesystem.py      ReadFileTool, WriteFileTool
      │   ├── shell.py           ShellTool
      │   └── grep.py            GrepTool
      │
      └── core/             ◄── Configuration
          └── config.py          Settings (frozen, env-based), PROJECT_ROOT
```

**Key design decisions (see [ADRs](docs/adr/README.md) — 10 decisions recorded):**

- **Dependency Inversion** — provider-specific code lives only in `llm/`;
  the `tools/`, `conversation/`, and `prompts/` packages are decoupled
  from any LLM provider.
- **Strategy pattern** — `LlmProvider`, `ToolSchemaAdapter`,
  `ConversationRepresentation`, and `SystemPromptAdapter` are all Strategy
  interfaces, making it trivial to swap providers.
- **Template Method** — every tool follows a `validate → execute` lifecycle
  enforced by the `Tool` base class.
- **Immutable value objects** — `ToolMetadata`, `ToolResult`, `LLMResponse`,
  `Conversation`, `SystemPrompt`, `AgentResult`, and `ExecutionContext`
  are frozen dataclasses that never mutate after creation.
- **Discovery without execution** — `ToolCatalog` lists what tools exist;
  `ToolSchemaAdapter` translates metadata to provider schemas; neither
  executes a tool.
- **Workspace safety** — path resolution enforces a boundary check after
  symlink canonicalisation; tools cannot escape the workspace root.
- **Tool call ID passthrough** — `ToolCallResult` carries the provider
  call ID through the bridge so consumers never re-match by name.

## Roadmap

- [x] Sprint 1 — Project foundation
- [x] Sprint 2 — LLM infrastructure (DeepSeek provider, `LlmClient` facade)
- [x] Sprint 3 — Tool framework (Template Method, registry, `ReadFileTool`)
- [x] Sprint 4 — Tool discovery (`ToolCatalog` discovery layer)
- [x] Sprint 5 — Provider tool representation (`ToolSchemaAdapter` + DeepSeek adapter)
- [x] Sprint 6 — Tool invocation (`ToolInvocation`, `ToolInvoker`)
- [x] Sprint 7 — Tool call bridge (`ProviderToolCall`, `ToolCallBridge`)
- [x] Sprint 8 — Conversation & agent runtime (`Conversation`, `AgentRuntime`)
- [x] Sprint 9 — Tool expansion & workspace safety (`ShellTool`, `GrepTool`, boundary enforcement)
- [x] Sprint 10 — System prompts (`SystemPrompt`, `SystemPromptAdapter`, assembler)
- [ ] Error resilience (retry, graceful degradation)
- [ ] Observability & tracing
- [ ] Streaming responses
- [ ] Multi-turn conversations & persistence
- [ ] Interactive CLI
- [ ] Code review
- [ ] Browser automation
- [ ] Multi-agent collaboration
- [ ] Evaluation framework

## Getting Started

### Prerequisites

- Python 3.13+
- DeepSeek API key (set via `.env`)

### Setup

```bash
# Clone and install (editable)
git clone <repo-url>
cd agentic-lab
pip install -e .

# Configure
cp .env.example .env
# Edit .env with your DEEPSEEK_API_KEY and DEEPSEEK_BASE_URL

# Run the demo
python app/main.py

# Run tests
python -m pytest tests/ -v

# Lint and format
ruff check . && ruff format --check .
```