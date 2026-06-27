# ADR-003: Sprint 3 — Tool Framework

**Status:** Accepted

**Date:** 2026-06-27

**Sprint:** 3 — Tool Framework

---

## Decisions

Three architectural decisions were made to implement the Tool Framework.

---

### 1. Tool Registry Stores Tool Instances

The `ToolRegistry` stores initialized tool instances, not classes.

```python
registry = ToolRegistry()
registry.register(ReadFileTool())  # instance, not class
tool = registry.get("read_file")
```

**Rationale**

* **Tools are stateless** — the sprint constrains tools to be stateless,
  so a single instance can be safely reused across all call-sites.
* **Avoids repeated construction** — registering instances eliminates
  repeated object creation on every lookup.
* **Simplifies dependency injection** — if a tool needs an injected
  dependency, the caller constructs the instance once and hands it to
  the registry. The registry does not need to know about constructor
  signatures.

**Trade-offs**

* Tools requiring runtime state are not supported.
* Registry owns object lifecycle with no explicit disposal mechanism.

**Future:** If tools need scoped state, the registry may evolve to store
factories (`lambda: ReadFileTool()`) instead of instances.

---

### 2. Template Method Pattern for Tool Lifecycle

The abstract `Tool` base class uses the Template Method pattern. The
public entry point `run()` orchestrates the lifecycle while subclasses
fill in only the business logic:

```
run(**kwargs)
  ├── validate(**kwargs)   ← optional hook (no-op default)
  └── execute(**kwargs)    ← mandatory (abstract)
```

Subclasses are required to implement **only** `execute()`.

```python
class Tool(ABC):
    async def validate(self, **kwargs: Any) -> None:
        return  # no-op default

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult: ...

    async def run(self, **kwargs: Any) -> ToolResult:
        try:
            await self.validate(**kwargs)
            return await self.execute(**kwargs)
        except Exception as exc:
            return ToolResult.fail(str(exc))
```

**Rationale**

* **Single responsibility** — subclasses focus solely on business logic.
* **Consistent error handling** — `run()` catches all exceptions and
  wraps them in `ToolResult.fail()`, so callers never see raw exceptions.
* **Extension without modification** — new lifecycle hooks can be added
  to the base class without touching any concrete tool.
* **Optional validation** — simple tools skip `validate()` entirely
  while complex tools override it for pre-condition checks.
* **Matches existing patterns** — the `LlmProvider` ABC in `llm/base.py`
  uses the same Strategy style, keeping architectural idioms consistent.

**Trade-offs**

* `**kwargs` is loosely typed — callers must know what parameters each
  tool expects. A Pydantic model could be introduced later.
* The `validate` / `execute` split may feel artificial for tools that
  need combined validation and execution (e.g., write file validates
  path + content together). The `validate` hook can still access all
  kwargs.

**Future:** Add `setup()` / `teardown()` hooks for resourceful tools;
introduce typed `ToolInput` via Pydantic.

---

### 3. ToolResult as a Frozen Value Object

`ToolResult` is a frozen `@dataclass` with named convenience
constructors.

```python
@dataclass(frozen=True)
class ToolResult:
    success: bool
    content: str
    error: str | None = None

    @classmethod
    def ok(cls, content: str) -> ToolResult: ...
    @classmethod
    def fail(cls, error: str) -> ToolResult: ...
```

**Rationale**

* **Predictability** — callers can inspect `result.success` without
  worrying about mutation downstream.
* **Safe to cache and compare** — immutable objects are hashable.
* **Consistent with `LLMResponse`** — the project already uses frozen
  dataclasses for value objects (`llm/response.py`).
* **Named constructors reduce ambiguity** — `ToolResult.ok("...")` and
  `ToolResult.fail("...")` are self-documenting.
* **Default `error=None`** — successful results omit the error field
  rather than carrying an empty string.

**Trade-offs**

* No mutation — metadata enrichment (e.g., execution time) must create a
  new object, which is by design.
* String-only content — structured data would need encoding as text.

**Future:** Add `execution_time_ms` set by the lifecycle orchestrator;
add a `data: Any` field for structured returns.

---

## Related

* ADR-002: Sprint 2 — LLM Infrastructure (for `LLMResponse` frozen
  dataclass pattern)