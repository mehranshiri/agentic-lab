# ADR-006: Sprint 6 — Tool Invocation

**Status:** Accepted

**Date:** 2026-06-28

**Sprint:** 6 — Tool Invocation

---

## Decisions

Two architectural decisions were made to introduce the first end-to-end
execution boundary without coupling the Tool Framework to any LLM provider.

---

### 1. `ToolInvocation` as an Immutable Request Object

A frozen dataclass, `ToolInvocation` (`tools/invocation.py`), captures a
provider-independent request to execute exactly one tool:

```python
@dataclass(frozen=True)
class ToolInvocation:
    tool_name: str
    arguments: dict[str, Any]
```

It carries *what* to call and *with which* arguments, nothing more.

**Rationale**

* **Provider-independent** — the invocation has no knowledge of LLM
  providers, tool-calling formats, or response parsing. Any source
  (human CLI, LLM tool-call response, test harness) can produce one.
* **Immutable** — frozen dataclass guarantees thread-safety and
  prevents accidental mutation after creation. Every `ToolInvocation`
  is a snapshot that can be logged, replayed, or compared.
* **Names match the registry** — `tool_name` maps directly to
  `Tool.metadata.name` and `ToolRegistry.get(name)`, so no translation
  layer is needed between the request and resolution.
* **Arguments are passed-through** — `arguments` is forwarded verbatim
  to `Tool.run(**arguments)`, meaning the invoker never interprets or
  validates tool-specific parameters (that's the tool's job).

**Trade-offs**

* **No input schema validation** — the invoker does not check whether
  `arguments` contain required keys or valid types. This is deferred
  to each tool's `validate()` hook. Adding invocation-level schema
  validation would couple the invoker to tool metadata details.
* **Not hashable** — `arguments` is a `dict`, which is unhashable.
  `ToolInvocation` instances cannot be used as dict keys or set
  members. This is acceptable since they are short-lived request
  objects, not long-lived identifiers.

---

### 2. `ToolInvoker` as a Stateless Execution Boundary

`ToolInvoker` (`tools/invoker.py`) receives a `ToolInvocation`, resolves
the tool through `ToolRegistry`, and returns a `ToolResult`:

```python
class ToolInvoker:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    async def invoke(self, invocation: ToolInvocation) -> ToolResult:
        tool = self._registry.get(invocation.tool_name)
        if tool is None:
            return ToolResult.fail(f"Unknown tool: '{invocation.tool_name}'")
        return await tool.run(**invocation.arguments)
```

```text
 ToolInvocation(tool_name, arguments)
        │
        ▼
 ToolInvoker.invoke()
        │
        ├── registry.get(name)
        │       │
        │       └── returns Tool or None
        │
        ├── Tool.run(**arguments)     ◄── Template Method lifecycle
        │       │                           (validate → execute)
        │       ▼
        └── ToolResult
```

**Rationale**

* **Single Responsibility** — the invoker owns exactly one concern:
  resolve a tool name and execute it. It does not discover tools
  (that's `ToolCatalog`), translate schemas (that's
  `ToolSchemaAdapter`), or decide which tool to call (that's a future
  planner/agent).
* **Stateless** — the invoker holds only a reference to the registry.
  It carries no invocation history, no retry state, no caching. This
  makes it safe to create, discard, or inject anywhere.
* **Graceful error handling** — unknown tools return a failed
  `ToolResult` rather than raising an exception. This means callers
  always get a structured outcome and never need try/except around
  invocation.
* **Template Method delegation** — the invoker calls `tool.run()`,
  which already wraps the `validate → execute` lifecycle and catches
  exceptions. The invoker never sees raw exceptions — only
  `ToolResult` instances.
* **Async-only** — `invoke()` is `async` because `Tool.run()` is
  `async`. This is forward-compatible with I/O-bound tools (file reads,
  HTTP calls, subprocess spawns) and async LLM workflows.

**Trade-offs**

* **Single-tool only** — each `invoke()` call executes exactly one
  tool. Multi-tool execution, fan-out, or chaining belong to a future
  orchestrator/planner, not the invoker.
* **No retry** — failed invocations are returned as-is. The caller
  (or a future retry decorator) owns the retry decision.
* **No timeout** — `tool.run()` runs to completion without an external
  deadline. Timeout enforcement would belong to a layer above the
  invoker (e.g. an async timeout wrapper).
* **No invocation audit trail** — the invoker does not log or store
  invocations. Observability is deferred to the caller or a future
  middleware layer.

---

## Files

| Action | File | Purpose |
|--------|------|---------|
| Create | `tools/invocation.py` | `ToolInvocation` frozen request object |
| Create | `tools/invoker.py` | `ToolInvoker` stateless execution boundary |
| Update | `tools/__init__.py` | Export `ToolInvocation` and `ToolInvoker` |
| Update | `app/main.py` | Demonstrate invocation + unknown-tool handling |

---

## Related

* ADR-005: Sprint 5 — Provider Tool Representation (for
  `ToolSchemaAdapter` which translates metadata to provider schemas;
  invocation consumes schemas, not produces them)
* ADR-004: Sprint 4 — Tool Discovery (for `ToolCatalog` which lists
  available tools; `ToolInvoker` resolves tools from the same
  `ToolRegistry`)
* ADR-003: Sprint 3 — Tool Framework (for `Tool` Template Method
  lifecycle called by `ToolInvoker.invoke()`)
