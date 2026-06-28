# Agentic Lab

An educational project for building a production-grade AI Software Engineer from scratch.

Instead of relying on existing coding agents, this project explores how to design, implement, and operate an autonomous software engineering agent capable of:

- Repository understanding
- Tool usage
- Code generation
- Code review
- Test execution
- Browser automation
- Multi-agent collaboration

## Project Status

🚧 Sprint 5 completed — Provider Tool Representation

## Architecture

```
app/main.py                 ◄── Composition root
      │
      ├── llm/              ◄── LLM infrastructure (Strategy pattern)
      │   ├── base.py            LlmProvider (ABC)
      │   ├── client.py          LlmClient (facade)
      │   ├── response.py        LLMResponse (value object)
      │   ├── providers/         DeepSeekProvider
      │   └── representations/   ToolSchemaAdapter (ABC)
      │                          DeepSeekToolSchemaAdapter
      │
      ├── tools/            ◄── Tool Framework
      │   ├── base.py            Tool (ABC — Template Method)
      │   ├── metadata.py        ToolMetadata (frozen dataclass)
      │   ├── result.py          ToolResult (frozen dataclass)
      │   ├── registry.py        ToolRegistry
      │   ├── catalog.py         ToolCatalog (discovery layer)
      │   └── filesystem.py      ReadFileTool
      │
      └── core/             ◄── Configuration
          └── config.py          Settings (frozen, env-based)
```

**Key design decisions (see [ADRs](docs/adr/README.md)):**

- **Dependency Inversion** — provider-specific code lives only in `llm/`;
  the `tools/` package is decoupled from any LLM provider.
- **Strategy pattern** — `LlmProvider` and `ToolSchemaAdapter` are both
  Strategy interfaces, making it trivial to swap providers.
- **Template Method** — every tool follows a `validate → execute` lifecycle
  enforced by the `Tool` base class.
- **Value objects** — `ToolMetadata`, `ToolResult`, and `LLMResponse` are
  frozen dataclasses that never mutate after creation.
- **Discovery without execution** — `ToolCatalog` lists what tools exist;
  `ToolSchemaAdapter` translates metadata to provider schemas; neither
  executes a tool.

## Roadmap

- [x] Sprint 1 — Project foundation
- [x] Sprint 2 — LLM infrastructure (DeepSeek provider, `LlmClient` facade)
- [x] Sprint 3 — Tool framework (Template Method, registry, `ReadFileTool`)
- [x] Sprint 4 — Tool discovery (`ToolCatalog` discovery layer)
- [x] Sprint 5 — Provider tool representation (`ToolSchemaAdapter` + DeepSeek adapter)
- [ ] Tool calling (LLM-driven tool execution)
- [ ] Repository explorer
- [ ] LangGraph workflow
- [ ] Code editing
- [ ] Browser automation
- [ ] Multi-agent orchestration
- [ ] Evaluation framework

## Getting Started

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- DeepSeek API key (set via `.env`)

### Setup

```bash
# Clone and install
git clone <repo-url>
cd agentic-lab
uv sync

# Configure
cp .env.example .env
# Edit .env with your DEEPSEEK_API_KEY and DEEPSEEK_BASE_URL

# Run the demo
uv run python -m app.main

# Run tests
uv run python -m pytest tests/ -v
```