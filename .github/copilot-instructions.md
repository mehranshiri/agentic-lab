# Project Guidelines

## Code Style

- **Python 3.13+** with `from __future__ import annotations` at the top of every module.
- Use **frozen dataclasses** for value objects and configuration (see `core/config.py`, `tools/result.py`, `tools/metadata.py`).
- All public functions, classes, and methods must have **docstrings**.
- Type hints on all public signatures; use `|` syntax for unions (`str | None`, not `Optional[str]`).
- Exported symbols declared in `__all__` for every `__init__.py`.

## Architecture

This project follows **SOLID** principles and clean architecture:

- **Dependency Inversion**: The `tools/` package is decoupled from any LLM provider. Provider-specific code lives only in `llm/`.
- **Strategy pattern**: `LlmProvider` and `ToolSchemaAdapter` are Strategy interfaces — swap providers without touching core logic.
- **Template Method**: Every tool follows a `validate → execute` lifecycle (see `tools/base.py`).
- **ADR required**: Any architectural decision that changes module boundaries, introduces a new pattern, or adds a dependency must be documented in `docs/adr/`. Reference the ADR in commit messages.
- **Simplicity over cleverness**: Prefer the simplest abstraction that solves the immediate need. Don't add extensibility points until they have a second consumer.

## Conventions

- **Never duplicate code**: If logic appears in two places, extract it to a shared location. Check `core/`, `llm/base.py`, and `tools/base.py` before adding helper functions.
- **Never modify unrelated files**: Each change should touch only the minimum set of modules needed for the task.
- **Keep commits small**: One logical change per commit. If the commit message needs "and" to describe it, split it.
- **Explain architectural decisions**: Every non-obvious design choice gets a brief rationale comment (`# NOTE: ...` or `# DESIGN: ...`) in the code, plus an ADR if it affects module boundaries.

## Build and Test

```bash
# Install dependencies (editable)
pip install -e .

# Lint and format (ruff, configured in pyproject.toml)
ruff check . && ruff format --check .

# Auto-fix lint issues and format
ruff check --fix . && ruff format .

# Run tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_invoker.py -v
```

Tests live in `tests/` mirroring the source structure. Every tool, provider, and adapter must have corresponding tests. Use `pytest` with plain `assert` statements — no unittest.TestCase.
