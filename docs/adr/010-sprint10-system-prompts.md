# ADR-010: Sprint 10 — System Prompts

**Status:** Proposed

**Date:** 2026-07-15

**Sprint:** 10 — System Prompts

---

## Decisions

Six architectural decisions were made to introduce a provider-independent
system prompt domain and integrate it into the existing agent runtime.

---

### 1. System Prompt as a Separate Top-Level `prompts/` Package

The system prompt domain lives in a new `prompts/` package at the project
root — a sibling to `tools/`, `llm/`, `conversation/`, and `agent/`.

```
prompts/
├── __init__.py
├── models.py        # InstructionBlock, SystemPrompt
└── assembler.py     # SystemPromptAssembler
```

**Rationale**

* **System prompts are a domain concept** — they describe *what* the agent
  is and how it should behave. This is independent of tools (execution),
  LLMs (provider communication), and conversations (message history).
* **Mirrors existing package structure** — `tools/` owns tool execution,
  `conversation/` owns message history, `prompts/` owns agent identity.
  Each package has exactly one domain responsibility.
* **No dependency on providers** — `prompts/` imports nothing from `llm/`.
  Provider-specific formatting is handled by the `SystemPromptAdapter`
  strategy in `llm/representations/`, following the same DIP as
  `ToolSchemaAdapter`.

**Trade-offs**

* **New top-level package** — adds a module to the project root. However,
  the alternative (placing prompt models in `agent/` or `conversation/`)
  would violate single responsibility — neither the runtime nor the
  conversation history should own the agent's identity.
* **Naming proximity to `.github/prompts/`** — the `.github/prompts/`
  directory contains VS Code Copilot prompt templates (developer-facing).
  The `prompts/` package is a Python domain package (agent-facing).
  They serve entirely different purposes and are at different directory
  levels, so the risk of confusion is low.

---

### 2. `SystemPromptAdapter` Strategy Pattern

The `SystemPromptAdapter` abstract base class (in `llm/representations/base.py`)
follows the same Strategy pattern as `ToolSchemaAdapter`.

```python
class SystemPromptAdapter(ABC):
    @abstractmethod
    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]: ...

class DeepSeekSystemPromptAdapter(SystemPromptAdapter):
    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]:
        return {"role": "system", "content": prompt.text}
```

**Rationale**

* **Consistent pattern** — the project already uses Strategy for tool
  schemas (`ToolSchemaAdapter`). Using the same pattern for system
  prompts reduces cognitive overhead and keeps the codebase predictable.
* **Provider isolation** — DeepSeek/OpenAI use `{"role": "system", ...}`
  in the messages list. Anthropic uses a separate `system` parameter.
  Future providers may not support system prompts at all. The strategy
  encapsulates these differences behind a single interface.
* **Testable in isolation** — each adapter can be unit-tested with a
  `SystemPrompt` fixture without involving any provider infrastructure.

**Trade-offs**

* **Two strategies instead of one** — an alternative was to fold system
  prompt formatting into `ConversationRepresentation`. This was rejected
  because it would give that class two responsibilities (converting
  conversation history AND formatting system prompts), violating SRP.

---

### 3. Assembler Is Stateless and Runs Once Per `run()` Call

`SystemPromptAssembler` is stateless. `AgentRuntime.run()` calls
`assembler.assemble()` exactly once — before entering the reasoning loop.

```python
async def run(self, prompt: str) -> AgentResult:
    system_prompt = self._assembler.assemble(context, catalog)
    system_msg = self._prompt_adapter.to_provider_format(system_prompt)
    conversation = Conversation().add_user_message(prompt)

    for iteration in range(1, self._max_iterations + 1):
        provider_messages = self._conversation_representation.to_provider_messages(
            conversation, system_prompt=system_msg
        )
        # ... rest of loop
```

**Rationale**

* **Tools don't change mid-interaction** — the set of available tools is
  fixed for the duration of a `run()` call. Re-assembling every iteration
  would waste CPU cycles and produce identical output.
* **Workspace context doesn't change mid-interaction** — the workspace
  root, timeouts, and limits are immutable within a single run.
* **Stateless assembler** — no caching, no mutation. Every `assemble()`
  call produces a fresh `SystemPrompt` from the current inputs. This
  keeps the assembler trivially testable and thread-safe.

**Trade-offs**

* **Cannot adapt to tools added mid-run** — but this capability does not
  exist yet (tools are registered at startup). If dynamic tool registration
  is added in a future sprint, the assembler can be called per-iteration
  without changing its interface.

---

### 4. `ConversationRepresentation` Receives a Pre-Formatted Dict, Not a Domain Object

`to_provider_messages()` accepts `system_prompt: dict[str, Any] | None`
— a provider-ready message dict already processed by `SystemPromptAdapter`.

```python
def to_provider_messages(
    self,
    conversation: Conversation,
    *,
    system_prompt: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if system_prompt is not None:
        messages.append(system_prompt)
    # ... existing conversion logic
```

**Rationale**

* **Single responsibility** — `ConversationRepresentation` converts
  `Conversation` → provider messages. It should not also convert
  `SystemPrompt` → provider dict. That is `SystemPromptAdapter`'s job.
* **Avoids coupling** — if `ConversationRepresentation` accepted a
  `SystemPrompt` domain object, it would depend on the `prompts/` package.
  By accepting a plain dict, the representation strategy stays focused
  on message formatting.
* **Orchestration lives in `AgentRuntime`** — the runtime coordinates the
  two strategies (assembler → adapter → representation) rather than
  pushing composition into a single strategy.

**Trade-offs**

* **`to_provider_messages` signature gains a parameter** — the method now
  accepts an optional `system_prompt` keyword argument. This is a minimal
  change that preserves backward compatibility (the parameter defaults to
  `None`).

---

### 5. System Prompt Is Runtime Configuration, Not Conversation History

`Conversation` does not gain a `system_prompt` field. The system prompt
is held and managed by `AgentRuntime` and injected at the message-formatting
boundary.

**Rationale**

* **Different semantics** — conversation messages represent an exchange
  between user, assistant, and tools. The system prompt is not part of
  that exchange — it is the agent's constitution, set before any
  interaction begins.
* **Immutability** — `Conversation` is immutable and grows with each
  interaction turn. Embedding the system prompt in `Conversation` would
  either make it mutable (it would need to be set after construction) or
  require it to be passed at construction time (coupling conversation
  creation to prompt assembly).
* **Reusability** — the same `Conversation` could theoretically be
  replayed with different system prompts for A/B testing, without
  modifying the conversation history.

**Trade-offs**

* **System prompt not serialized with conversation** — if conversation
  persistence is added in a future sprint, the system prompt would need
  to be stored separately or reconstructed. This is acceptable because
  the system prompt is deterministic given the same tools and context.

---

### 6. `InstructionBlock.source` Provenance Tracking

Each `InstructionBlock` carries a `source: str` tag indicating where the
instruction originated (`"builtin"`, `"tools"`, `"workspace"`, `"user"`).

**Rationale**

* **Debugging** — when the agent behaves unexpectedly, knowing which
  instruction block came from where helps diagnose prompt engineering
  issues.
* **Future auditing** — a future sprint could add prompt logging that
  groups blocks by source, or allow users to override specific sources
  without replacing the entire prompt.
* **Minimal cost** — a single string field adds negligible complexity.

**Trade-offs**

* **No enum** — `source` is a free-form string rather than an enum.
  This was a deliberate choice: new sources may be added by external
  consumers (e.g. `"project_conventions"`, `"git_history"`), and an
  enum would require modifying the domain model for each new source.
  A string is open for extension.
