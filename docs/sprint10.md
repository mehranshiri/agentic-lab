# Sprint 10 — System Prompts

## Goal

Introduce a provider-independent system prompt domain that defines the agent's identity, behavioral rules, and contextual instructions. The system prompt is dynamically assembled from multiple sources (builtin identity, available tools, workspace context) and injected as the first message in every LLM interaction.

This sprint establishes the system prompt as a first-class architectural concept — distinct from user messages, tool definitions, and file-based instructions.

---

# Why this sprint exists

After Sprint 9:

- The agent has four tools (read, write, shell, grep) and a complete reasoning loop.
- The agent can execute multi-step tasks within the workspace.
- The architecture is cleanly separated across all boundaries.

However, the agent has no identity:

- The LLM receives raw user messages with no framing — it does not know it is an agent, what tools are available, or how to behave.
- There is no mechanism to inject guardrails, conventions, or workspace context before the first user message.
- Without a system prompt, the LLM treats tool availability as optional and may ignore tools entirely.

Sprint 10 closes this gap by introducing a system prompt domain and integration, while maintaining the Dependency Inversion Principle between the prompt domain and LLM providers.

---

# Responsibilities

## 1. System Prompt Domain Models

Introduce provider-independent value objects in a new top-level `prompts/` package.

### `InstructionBlock`

A single, self-contained block of system-prompt content with provenance tracking.

- Immutable frozen dataclass.
- `content: str` — the instruction text.
- `source: str` — provenance tag (`"builtin"`, `"tools"`, `"workspace"`, `"user"`).

```python
block = InstructionBlock(content="You are an expert AI coding agent.", source="builtin")
```

### `SystemPrompt`

An assembled, provider-independent system prompt composed of ordered `InstructionBlock` objects.

- Immutable frozen dataclass.
- `blocks: tuple[InstructionBlock, ...]` — ordered instruction blocks.
- `text: str` — property that joins all blocks with double newlines.

```python
prompt = SystemPrompt(blocks=(identity_block, tools_block, workspace_block))
print(prompt.text)  # Full assembled prompt string
```

---

## 2. System Prompt Assembler

Introduce `SystemPromptAssembler` — a stateless class responsible for composing a `SystemPrompt` from the agent's current context.

Responsibilities:

- Produce the built-in identity / role description (hardcoded, always present).
- Enumerate available tools from `ToolCatalog` — dynamically discovered.
- Describe the workspace from `ExecutionContext`.
- Accept optional user-provided `InstructionBlock` objects.
- Return a complete, ordered `SystemPrompt`.

```python
assembler = SystemPromptAssembler()
prompt = assembler.assemble(context, catalog, extra_blocks=user_instructions)
```

The assembler runs once per `AgentRuntime.run()` invocation — before the reasoning loop — because tools and workspace context do not change mid-interaction.

---

## 3. System Prompt Adapter (Strategy Pattern)

Introduce `SystemPromptAdapter` — an abstract strategy for translating a domain `SystemPrompt` into a provider-specific message dict.

Follows the same pattern as `ToolSchemaAdapter`:

- Abstract base class in `llm/representations/base.py`.
- Concrete implementation `DeepSeekSystemPromptAdapter` in `llm/representations/deepseek.py`.

```python
class SystemPromptAdapter(ABC):
    @abstractmethod
    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]: ...

class DeepSeekSystemPromptAdapter(SystemPromptAdapter):
    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]:
        return {"role": "system", "content": prompt.text}
```

---

## 4. Conversation Representation Integration

Extend `ConversationRepresentation.to_provider_messages()` to accept an optional pre-formatted system prompt dict.

```python
def to_provider_messages(
    self,
    conversation: Conversation,
    *,
    system_prompt: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    messages = []
    if system_prompt is not None:
        messages.append(system_prompt)
    # ... existing conversion logic
```

Rationale: The `ConversationRepresentation` receives a **pre-formatted** dict (already processed by `SystemPromptAdapter`), not the domain `SystemPrompt`. This keeps the representation strategy focused on message formatting — it does not need to know about the `SystemPrompt` domain object.

---

## 5. Agent Runtime Integration

`AgentRuntime` owns the `SystemPromptAssembler` and `SystemPromptAdapter` as constructor dependencies.

In `run()`:

1. Assemble the `SystemPrompt` via the assembler (once, before the loop).
2. Convert it to a provider dict via the adapter.
3. Pass the formatted system prompt to `to_provider_messages()` on every iteration.

The reasoning loop itself does not change — only the setup phase is extended.

---

# Constraints

- System prompts must remain completely provider-independent — no provider logic in `prompts/`.
- `Conversation` must not gain a system prompt field — the system prompt is runtime configuration, not conversation history.
- `ConversationRepresentation` receives a pre-formatted dict, not a `SystemPrompt` domain object.
- The assembler must be stateless and run once per `run()` call.
- Do not introduce prompt templating engines (Jinja2, etc.).
- Do not introduce file-based prompt loading.
- Do not introduce multi-agent or role-based prompt selection.
