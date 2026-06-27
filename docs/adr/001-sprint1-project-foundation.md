# ADR-001: Sprint 1 — Project Foundation

**Status:** Accepted

**Date:** 2026-06-27 (backfilled)

**Sprint:** 1 — Project Foundation

---

## Decisions

Four architectural decisions were made in establishing the project
skeleton.

---

### 1. Use `uv` for Dependency Management

The project uses **`uv`** (by Astral) for all dependency management:
project creation, virtual environment handling, package resolution, and
locking.

**Rationale**

* **Speed** — `uv` resolves and installs packages significantly faster
  than `pip` and `poetry` due to its Rust implementation.
* **Single tool** — handles venvs, pip-install, locking, and Python
  version management in one binary.
* **PEP 621 compliant** — writes standard `pyproject.toml` metadata,
  reducing vendor lock-in compared to the non-standard `[tool.poetry]`
  section.
* **Growing ecosystem** — same team as `ruff`; rapid community adoption.

**Trade-off:** `uv.lock` format is specific to `uv`. If the team
switches tools, the lock file must be regenerated from `pyproject.toml`.

---

### 2. Hatchling as Build Backend

`hatchling` is selected as the PEP 517 build backend.

**Rationale**

* **Fast and lightweight** — no heavy plugin system or bootstrapping
  overhead.
* **Native PEP 621 support** — reads metadata directly from
  `pyproject.toml` without translation layers.
* **Explicit package list** — `tool.hatch.build.targets.wheel.packages`
  makes the wheel contents obvious and auditable.
* **Batteries included** — version inference from VCS, editable
  installs, and source distribution support without extra dependencies.

**Trade-off:** Fewer plugins than `setuptools` or `poetry` for complex
C-extension builds, which this project does not need.

---

### 3. Monorepo-Style Flat Package Layout

The project distributes 5 top-level packages (`app`, `agent`, `llm`,
`tools`, `core`) in a flat layout under the project root rather than
nesting them under a `src/` directory or a unified namespace package.

**Rationale**

* **Independent deployment units** — each package can be extracted into
  its own repository or distribution later without restructuring imports.
* **Clear domain separation** — opening the project root immediately
  surfaces the bounded contexts.
* **Simpler imports** — `from llm import LlmClient` vs.
  `from src.agentic_lab.llm import LlmClient`.

**Trade-off:** No single namespace prefix; potential for name collisions
if the project is installed alongside other flat packages with the same
names. This is acceptable because the project is a standalone
application, not a library installed alongside others.

---

### 4. Frozen `Settings` Dataclass with Lazy Validation

Configuration is loaded at module level into a frozen `Settings`
dataclass singleton. Required env vars are validated at import time via
a `_require()` helper that raises a custom `ConfigurationError`.

```python
@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = field(default_factory=lambda: _require("DEEPSEEK_API_KEY"))
    deepseek_base_url: str = field(default_factory=lambda: _require("DEEPSEEK_BASE_URL"))

settings = Settings()
```

**Rationale**

* **Fail-fast** — missing configuration is caught at import time, not
  deep inside a provider during a request.
* **Immutable by default** — prevents configuration from being mutated
  after initialization.
* **No framework dependency** — uses the standard library and
  `python-dotenv` only; no Pydantic or config library lock-in.
* **Field-level lazy default** — individual fields can use different
  strategies (`_require` vs. `os.getenv` with fallback) without
  changing the Settings class structure.

**Trade-off:** Import-time side effects (loading `.env`, raising on
missing vars) make the module less suitable for re-import in test
contexts. A future refactor may introduce a builder function that tests
can call explicitly.

---

## Related

* ADR-002: Sprint 2 — LLM Infrastructure (for Strategy pattern with
  dependency injection)
* ADR-003: Sprint 3 — Tool Framework (for continued use of frozen
  dataclasses as value objects)