# ADR-007: Sprint 7 — Tool Call Bridge

**Status:** Accepted

**Date:** 2026-07-02

**Sprint:** 7 — Tool Call Bridge

---

## Decisions

Three architectural decisions were made to bridge the LLM module and the
Tool Framework without coupling them.

---

### 1. `ProviderToolCall` as a Provider-Independent Value Object

A frozen dataclass, `ProviderToolCall` (`llm/provider_tool_call.py`),
represents a single tool call extracted from a provider response:

```python
@dataclass(frozen=True)
class ProviderToolCall:
    id: str                # e.g. "call_xxx"
    name: str              # e.g. "read_file"
    arguments: dict[str, Any]  # already JSON-decoded
```

**Rationale**

* **Decoupled from SDK types** — `ProviderToolCall` carries only the
  essential fields (`id`, `name`, `arguments` as a dict), not the full
  SDK response object. The bridge never needs to know about
  `openai.types.chat.ChatCompletionMessageToolCall` or any other vendor
  type.
* **Provider-agnostic** — any provider (DeepSeek, OpenAI, Anthropic) can
  produce `ProviderToolCall` objects. The bridge and the Tool Framework
  are completely isolated from provider-specific payload formats.
* **Provider owns parsing** — the concrete provider class (e.g.
  `DeepSeekProvider`) is responsible for extracting tool calls from its
  raw response and constructing `ProviderToolCall` instances. This is
  the provider's natural responsibility since it already knows its own
  SDK and API.
* **Immutable** — frozen dataclass guarantees the parsed tool call
  cannot be mutated after extraction.

```text
 DeepSeekProvider.send_message()
        │
        │  parses raw SDK response
        │  constructs ProviderToolCall objects
        ▼
  ProviderToolCall  (clean value object)
        │
        ▼
  ToolCallBridge.process()
```

**Trade-offs**

* **`arguments` is a plain dict** — no schema validation is performed on
  the parsed arguments. Malformed JSON is caught at parse time (returns
  empty dict), but semantically incorrect arguments are not detected
  until the tool's `validate()` hook runs.
* **`id` is carried but unused** — the provider-assigned `id` is
  preserved in case future orchestrators need to correlate tool results
  with call IDs, but the current bridge does not use it.

---

### 2. `ToolCallBridge` as a Stateless Translation Boundary

`ToolCallBridge` (`llm/tool_call_bridge.py`) lives in the LLM module and
translates `ProviderToolCall` objects into `ToolInvocation` objects,
then delegates execution to the existing `ToolInvoker`:

```python
class ToolCallBridge:
    def __init__(self, invoker: ToolInvoker) -> None:
        self._invoker = invoker

    async def process(
        self, tool_calls: list[ProviderToolCall]
    ) -> list[ToolCallResult]:
        results = []
        for tc in tool_calls:
            invocation = ToolInvocation(
                tool_name=tc.name, arguments=tc.arguments
            )
            tool_result = await self._invoker.invoke(invocation)
            results.append(
                ToolCallResult(invocation=invocation, result=tool_result)
            )
        return results
```

```text
 ProviderToolCall
        │
        ▼
 ToolCallBridge.process()
        │
        ├── translates to ToolInvocation
        ├── delegates to ToolInvoker.invoke()
        ├── collects ToolCallResult(s)
        │
        ▼
 list[ToolCallResult]
```

**Rationale**

* **Clear separation of concerns** — the provider parses SDK responses;
  the bridge translates to domain objects and invokes. Neither crosses
  into the other's territory.
* **Stateless** — the bridge holds only a reference to `ToolInvoker`.
  It carries no execution history, no retry state, no caching. It can
  be created and discarded freely.
* **Sequential execution** — tool calls are processed one at a time in
  the order they appear in the provider response. This is deliberate:
  parallel or concurrent execution belongs to a future orchestrator.
* **Reuses existing infrastructure** — the bridge depends on
  `ToolInvocation` (immutable request object), `ToolInvoker` (stateless
  execution boundary), and `ToolResult` (frozen value object), all
  introduced in Sprint 6. Zero changes to the Tool Framework.
* **Dependency Inversion** — the bridge depends on `ToolInvocation` and
  `ToolInvoker` (both in `tools/`), not the other way around. The Tool
  Framework has no knowledge of providers, provider tool calls, or the
  bridge itself.
* **No provider-specific logic in the bridge** — the bridge receives
  already-parsed `ProviderToolCall` objects. It never touches raw JSON,
  SDK types, or provider schemas. Adding a new provider only requires
  that provider to produce `ProviderToolCall` objects; the bridge
  itself is unchanged.

**Trade-offs**

* **No retry** — if a tool execution fails, the bridge returns the
  failure in the `ToolCallResult` and moves on. Retry logic belongs to a
  higher-level orchestrator.
* **No parallel execution** — multiple tool calls from a single provider
  response are processed sequentially. Fan-out or concurrent execution
  belongs to a future sprint.
* **No input validation** — the bridge does not validate that
  `ProviderToolCall.name` corresponds to a registered tool before
  constructing a `ToolInvocation`. That check happens inside
  `ToolInvoker.invoke()`, which returns a failure result for unknown
  tools.
* **No error aggregation** — results are returned as a list; the caller
  must inspect each `ToolCallResult` individually to determine success
  or failure. A future aggregation helper could summarise results.

---

### 3. `ToolCallResult` as a Frozen Value Object

`ToolCallResult` (`llm/tool_call_bridge.py`) pairs a `ToolInvocation`
with its resulting `ToolResult`:

```python
@dataclass(frozen=True)
class ToolCallResult:
    invocation: ToolInvocation
    result: ToolResult
```

**Rationale**

* **Preserves the request-response mapping** — callers can trace which
  invocation produced which result without manual bookkeeping.
* **Immutable** — consistent with the frozen dataclass pattern used
  throughout the project (`ToolInvocation`, `ToolResult`, `LLMResponse`,
  `ProviderToolCall`).
* **Self-contained** — a `ToolCallResult` carries everything needed to
  understand what was requested and what happened, without consulting
  external state.
* **Hashable and comparable** — frozen dataclasses with immutable fields
  are hashable, allowing `ToolCallResult` instances to be used in sets,
  dicts, and test assertions.

**Trade-offs**

* **No execution metadata** — `ToolCallResult` does not carry timing
  information, the provider call ID, or an execution index. These can be
  added as optional fields when needed by a future orchestrator.

---

### Architecture Summary

```
DeepSeekProvider.send_message()
        │
        │  parses raw SDK response
        │  constructs ProviderToolCall objects
        │  attaches them to LLMResponse.tool_calls
        ▼
  LLMResponse
        │
        │  .tool_calls: list[ProviderToolCall] | None
        ▼
  (caller extracts tool_calls)
        │
        ▼
  ToolCallBridge.process(tool_calls)
        │
        ├── translates ProviderToolCall → ToolInvocation
        ├── delegates to ToolInvoker.invoke()
        ├── collects ToolCallResult(s)
        │
        ▼
  list[ToolCallResult]
```

The bridge is the architectural boundary between the LLM module and the
Tool Framework. Provider-specific parsing stays inside the provider;
domain translation stays inside the bridge; tool execution stays inside
the invoker. Each layer has a single, well-defined responsibility.

---

## Files

| Action | File | Purpose |
|--------|------|---------|
| Create | `llm/provider_tool_call.py` | `ProviderToolCall` frozen dataclass |
| Create | `llm/tool_call_bridge.py` | `ToolCallResult` frozen dataclass + `ToolCallBridge` class |
| Modify | `llm/response.py` | Add optional `tool_calls` field to `LLMResponse` |
| Modify | `llm/providers/deepseek.py` | Parse tool calls from raw response into `ProviderToolCall` objects |
| Modify | `llm/__init__.py` | Export `ProviderToolCall`, `ToolCallBridge`, `ToolCallResult` |
| Create | `tests/test_tool_call_bridge.py` | 12 unit tests covering parsing, translation, execution, and edge cases |

## Related

* ADR-006: Sprint 6 — Tool Invocation (for `ToolInvocation` and
  `ToolInvoker` reused by the bridge without modification)
* ADR-005: Sprint 5 — Provider Tool Representation (for
  `ToolSchemaAdapter` which translates metadata to provider schemas;
  the bridge handles the reverse path: provider tool calls to domain
  invocations)
* ADR-003: Sprint 3 — Tool Framework (for `ToolResult`, `ToolRegistry`,
  and Template Method lifecycle all reused unchanged)
* ADR-002: Sprint 2 — LLM Infrastructure (for `LLMResponse` frozen
  dataclass extended with the `tool_calls` field)