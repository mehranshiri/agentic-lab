# ADR-008: Sprint 8 — Conversation & Agent Runtime

**Status:** Accepted

**Date:** 2026-07-07

**Sprint:** 8 — Conversation & Agent Runtime

---

## Decisions

Five architectural decisions were made to introduce a provider-independent
Conversation domain and an AgentRuntime that owns the full reasoning loop.

---

### 1. `Conversation` as a Standalone Domain Module (`conversation/`)

The Conversation domain lives in its own top-level package (`conversation/`)
rather than inside `agent/`, `llm/`, or `tools/`. It contains four frozen
dataclasses:

```python
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"

@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]

@dataclass(frozen=True)
class Message:
    role: MessageRole
    content: str | None = None
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None

@dataclass(frozen=True)
class Conversation:
    messages: list[Message] = field(default_factory=list)
```

**Rationale**

* **Provider-independent by construction** — `conversation/` has zero
  imports from `llm/`, `agent/`, or any provider module. It depends only
  on Python's standard library. This guarantees that the conversation
  history is never polluted with provider-specific types, schemas, or
  formatting logic.
* **Separate package, not a sub-package** — placing `conversation/` at
  the project root (sibling to `agent/`, `llm/`, `tools/`) ensures no
  module owns it. The conversation is a shared domain concept consumed by
  multiple modules, not a subordinate of any single one.
* **Immutable** — every mutation method (`add_user_message`,
  `add_assistant_message`, `add_tool_message`) returns a **new**
  `Conversation` instance. The original is never modified. This
  eliminates an entire class of bugs related to shared mutable state and
  makes the conversation safe to pass across architectural boundaries.
* **Single source of truth** — the `Conversation` is the canonical
  representation of every interaction. There is no secondary log,
  separate history array, or parallel tracking elsewhere.

```text
 conversation/
     │
     │  (zero imports from llm/, agent/, or tools/)
     │
     ├── MessageRole   (enum)
     ├── ToolCall      (frozen dataclass)
     ├── Message       (frozen dataclass)
     └── Conversation  (frozen dataclass, immutable collection)
```

**Trade-offs**

* **Copy-on-write overhead** — every message addition creates a new list
  and a new `Conversation` instance. For conversations with hundreds of
  messages this could become a performance concern. When it does, an
  immutable persistent data structure (e.g. `pyrsistent.PVector`) can
  replace `list` without changing the public API.
* **No message indexing** — `Conversation` is a flat list. Filtering by
  role or finding the last assistant message requires a linear scan.
  Helper methods can be added when needed without breaking immutability.
* **`ToolCall` vs `ProviderToolCall`** — `conversation.models.ToolCall`
  is deliberately distinct from `llm.provider_tool_call.ProviderToolCall`.
  The domain `ToolCall` has no knowledge of where it came from;
  `ProviderToolCall` is the LLM module's representation with the same
  fields but a different semantic role (provider output vs. domain
  history). The two could be unified in a future refactor but keeping
  them separate preserves the architectural boundary.

---

### 2. `ConversationRepresentation` as a Provider-Specific Translation Strategy

An abstract base class `ConversationRepresentation`
(`llm/conversation_representation.py`) defines the contract for
translating a domain `Conversation` into provider-compatible message
dicts:

```python
class ConversationRepresentation(ABC):
    @abstractmethod
    def to_provider_messages(
        self, conversation: Conversation
    ) -> list[dict[str, Any]]:
        ...
```

`DeepSeekConversationRepresentation` is the first concrete implementation,
producing message dicts compatible with the OpenAI/DeepSeek Chat
Completions format.

**Rationale**

* **Follows the established ToolSchemaAdapter pattern** — Sprint 5
  introduced `ToolSchemaAdapter` to translate `ToolMetadata` into
  provider tool definitions. `ConversationRepresentation` applies the
  same Strategy pattern in the opposite direction: domain objects →
  provider wire format. The naming (`Representation` vs `Adapter`)
  reflects this subtle difference: schemas are "adapted", conversations
  are "represented".
* **Provider-specific formatting stays in `llm/`** — the Conversation
  domain has no knowledge of role strings (`"user"`, `"assistant"`,
  `"tool"`), message dict structure, or how tool calls are nested inside
  assistant messages. All of that is isolated in the concrete
  representation class.
* **New providers require zero domain changes** — adding an OpenAI,
  Anthropic, or Gemini provider only requires a new
  `ConversationRepresentation` subclass. The `Conversation`, `Message`,
  and `ToolCall` domain objects are untouched.
* **Stateless** — the representation holds no cache, no conversation
  state, no configuration. It is a pure function from `Conversation` to
  `list[dict]`.

```text
 Conversation (domain)
         │
         ▼
 ConversationRepresentation.to_provider_messages()
         │
         ▼
 list[dict]  (provider-compatible messages)
```

**Trade-offs**

* **No streaming awareness** — the representation always produces a
  complete list of message dicts. Streaming responses (SSE, chunked
  completions) are out of scope for this sprint.
* **One representation per provider** — unlike `ToolSchemaAdapter` which
  can theoretically be reused across OpenAI-compatible providers,
  `DeepSeekConversationRepresentation` is explicitly tied to DeepSeek's
  format. If OpenAI adopts a different format in the future, a separate
  representation class would be needed.

---

### 3. `AgentRuntime` as the Only Public Entry Point for Agent Interaction

`AgentRuntime` (`agent/runtime.py`) encapsulates the complete reasoning
loop behind a single `async run(prompt: str) -> AgentResult` method:

```python
class AgentRuntime:
    def __init__(
        self,
        provider: LlmProvider,
        conversation_representation: ConversationRepresentation,
        tool_schema_adapter: ToolSchemaAdapter,
        tool_catalog: ToolCatalog,
        tool_call_bridge: ToolCallBridge,
        *,
        max_iterations: int = 10,
    ) -> None:
        ...

    async def run(self, prompt: str) -> AgentResult:
        ...
```

The reasoning loop:

1. Creates a `Conversation` with the user prompt.
2. Discovers available tools via `ToolCatalog` (once, before the loop).
3. Enters a loop (up to `max_iterations`):
   a. Converts the `Conversation` to provider messages via
      `ConversationRepresentation`.
   b. Sends messages to the LLM provider.
   c. If no tool calls are returned, returns the final answer as an
      `AgentResult`.
   d. Otherwise, appends the assistant message (with tool calls) to the
      conversation, executes tools via `ToolCallBridge`, and appends
      each tool result as a tool message.
4. If the loop reaches `max_iterations` without a final answer, returns
   a failure `AgentResult`.

**Rationale**

* **Single public API** — `main.py` and any future caller only interact
  with `AgentRuntime.run()`. They never orchestrate providers, tool
  execution, or conversation updates themselves. This is the key
  constraint from the sprint definition.
* **Dependency injection** — all dependencies (`LlmProvider`,
  `ConversationRepresentation`, `ToolSchemaAdapter`, `ToolCatalog`,
  `ToolCallBridge`) are injected via the constructor. The runtime does
  not instantiate any of them and does not reach for global config. This
  makes it fully testable with mocks and swappable for different
  configurations.
* **Reuses existing infrastructure without modification** — the runtime
  depends on `ToolCallBridge`, `ToolInvoker`, `ToolCatalog`, and
  `ToolSchemaAdapter` exactly as they were designed. Zero architectural
  changes to the Tool Framework or the LLM module were required.
* **`max_iterations` guard** — a configurable limit (default 10)
  protects against infinite reasoning loops where the LLM perpetually
  requests tool calls without ever producing a final answer. When the
  limit is exceeded, the runtime returns a failure `AgentResult` rather
  than hanging or crashing.
* **Stateless between runs** — each `run()` call creates a fresh
  `Conversation`. The runtime retains no history, no memory, no session
  state. Multi-turn conversations (where the user asks follow-up
  questions) can be built on top of the runtime in a future sprint.

```text
 main.py
     │
     │  wires dependencies, calls runtime.run(prompt)
     ▼
 AgentRuntime.run()
     │
     ├── Conversation().add_user_message(prompt)
     ├── ToolCatalog.list_tools()   (once)
     │
     └── loop (max_iterations):
           ├── ConversationRepresentation.to_provider_messages()
           ├── LlmProvider.send_message()
           ├── if no tool_calls → return AgentResult
           ├── Conversation.add_assistant_message()
           ├── ToolCallBridge.process()
           └── Conversation.add_tool_message()  (per result)
```

**Trade-offs**

* **Sequential tool execution** — the runtime processes tool calls one at
  a time through `ToolCallBridge.process()`, which itself executes tools
  sequentially. Parallel tool execution belongs to a future sprint.
* **No retry** — if the LLM call fails (network error, rate limit), the
  exception propagates to the caller. The runtime does not catch or retry
  provider errors. A retry decorator or middleware layer can be added in
  a future sprint.
* **No conversation persistence** — the `Conversation` lives only in
  memory during the `run()` call. Persisting conversations to a database
  or file is explicitly out of scope (Sprint 8 constraint).
* **No tool call ID matching guarantees** — when appending tool results
  to the conversation, the runtime matches `ToolCallResult.invocation.tool_name`
  against `ProviderToolCall.name` to find the corresponding call ID.
  This works correctly for the current sequential execution model but
  would need refinement if parallel execution or multiple calls to the
  same tool are introduced.

---

### 4. `AgentResult` as a Minimal Immutable Outcome

```python
@dataclass(frozen=True)
class AgentResult:
    success: bool
    answer: str
```

**Rationale**

* **Minimal by design** — Sprint 8 explicitly states the result should
  contain only `success` and `answer`. Execution traces, metrics,
  diagnostics, usage, and timing belong to future sprints.
* **Immutable** — consistent with the frozen dataclass pattern used
  throughout the project (`ToolResult`, `LLMResponse`, `ToolInvocation`,
  `ProviderToolCall`).
* **Extensible** — adding fields (e.g. `iterations`, `tool_calls_made`,
  `usage`) is backward-compatible since the dataclass can gain optional
  fields with defaults without breaking existing callers.

---

### 5. `main.py` as a Thin Bootstrap Layer

`main.py` was rewritten to only:

1. Instantiate tool infrastructure (`ToolRegistry`, `ToolCatalog`,
   `ExecutionContext`, `ToolInvoker`).
2. Instantiate LLM infrastructure (`DeepSeekProvider`,
   `DeepSeekConversationRepresentation`, `DeepSeekToolSchemaAdapter`).
3. Wire the bridge (`ToolCallBridge`).
4. Create the `AgentRuntime` with all dependencies.
5. Call `runtime.run(prompt)` and print the result.

**Rationale**

* **`main.py` does not orchestrate providers or tool execution** — this
  was an explicit constraint from Sprint 8. All orchestration logic lives
  inside `AgentRuntime.run()`. `main.py` is purely a composition root.
* **Single responsibility** — `main.py` is the dependency injection
  container. If the project eventually adopts a DI framework
  (`dependency-injector`, `punq`, etc.), the wiring can be extracted
  without changing the runtime's API.

---

### Architecture Summary

```
 main.py  (composition root — wires dependencies)
     │
     ▼
 AgentRuntime.run(prompt)
     │
     ├─► Conversation (domain, immutable)
     │       │
     │       ▼
     ├─► ConversationRepresentation.to_provider_messages()
     │       │
     │       ▼
     ├─► LlmProvider.send_message(messages, tools)
     │       │
     │       ▼
     │   LLMResponse (.text, .tool_calls)
     │       │
     │       ├── no tool_calls → AgentResult(success=True, answer=...)
     │       │
     │       └── has tool_calls:
     │               │
     │               ├─► Conversation.add_assistant_message(tool_calls)
     │               ├─► ToolCallBridge.process(tool_calls)
     │               │       │
     │               │       ▼
     │               │   ToolInvoker.invoke(ToolInvocation)
     │               │
     │               └─► Conversation.add_tool_message(...)
     │                       │
     │                       └── (loop continues)
     │
     ▼
 AgentResult  (success, answer)
```

---

## Files

| Action | File | Purpose |
|--------|------|---------|
| Create | `conversation/__init__.py` | Package init, exports `Conversation`, `Message`, `MessageRole`, `ToolCall` |
| Create | `conversation/models.py` | `MessageRole` enum, `ToolCall`, `Message`, `Conversation` frozen dataclasses |
| Create | `llm/conversation_representation.py` | `ConversationRepresentation` ABC + `DeepSeekConversationRepresentation` |
| Create | `agent/result.py` | `AgentResult` frozen dataclass (`success`, `answer`) |
| Create | `agent/runtime.py` | `AgentRuntime` with full reasoning loop |
| Modify | `agent/__init__.py` | Export `AgentResult`, `AgentRuntime` |
| Modify | `llm/__init__.py` | Export `ConversationRepresentation`, `DeepSeekConversationRepresentation` |
| Rewrite | `app/main.py` | Thin bootstrap — wires deps and calls `AgentRuntime.run()` |
| Create | `tests/test_conversation.py` | 24 tests: `MessageRole`, `ToolCall`, `Message`, `Conversation` |
| Create | `tests/test_conversation_representation.py` | 10 tests: `DeepSeekConversationRepresentation` |
| Create | `tests/test_runtime.py` | 12 tests: `AgentResult` + `AgentRuntime` with mocked dependencies |

## Related

* ADR-007: Sprint 7 — Tool Call Bridge (for `ToolCallBridge`, `ToolCallResult`, and
  `ProviderToolCall` all reused by the runtime without modification)
* ADR-006: Sprint 6 — Tool Invocation (for `ToolInvoker` and `ToolInvocation`
  reused by the bridge which the runtime calls)
* ADR-005: Sprint 5 — Provider Tool Representation (for `ToolSchemaAdapter` reused
  by the runtime to produce provider tool definitions)
* ADR-004: Sprint 4 — Tool Discovery (for `ToolCatalog` reused by the runtime to
  discover available tools)
* ADR-002: Sprint 2 — LLM Infrastructure (for `LlmProvider` and `LLMResponse`
  reused by the runtime for all LLM communication)