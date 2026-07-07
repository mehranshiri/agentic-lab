# Sprint 8 — Conversation & Agent Runtime

## Goal

Implement the first complete agent interaction cycle by introducing a provider-independent `Conversation` abstraction and an `AgentRuntime` responsible for executing the entire reasoning loop.

The runtime must encapsulate communication with the LLM provider, tool execution, and conversation management behind a single public API.

---

# Responsibilities

## 1. Conversation

Introduce a provider-independent `Conversation` abstraction representing the complete interaction history.

The Conversation:

- Owns the message history.
- Is immutable.
- Returns a new Conversation instance whenever a message is added.
- Contains only domain objects and must not depend on any LLM provider.
- Becomes the single source of truth for every interaction.

Introduce corresponding domain objects:

- `Conversation`
- `Message`
- `MessageRole`

At minimum, support:

- User messages
- Assistant messages
- Tool messages

---

## 2. Conversation Representation

Introduce an abstraction responsible for translating a provider-independent `Conversation` into the message format required by a specific LLM provider.

Responsibilities:

- Convert Conversation into provider-compatible messages.
- Keep all provider-specific message formatting inside the LLM module.
- Allow future providers (OpenAI, Claude, Gemini, etc.) without modifying the Conversation domain.

The Conversation domain must never know how providers represent messages.

---

## 3. Agent Runtime

Introduce an `AgentRuntime` responsible for executing one complete agent interaction.

Responsibilities:

- Receive a user's prompt.
- Create the initial Conversation.
- Convert the Conversation into provider-specific messages.
- Send messages to the configured LLM provider.
- Detect tool requests.
- Delegate tool execution to `ToolCallBridge`.
- Append tool results into a new Conversation.
- Continue the reasoning loop until no further tool calls are requested.
- Return the final result.

The runtime becomes the only public entry point for executing an agent interaction.

---

## 4. Agent Result

Introduce an immutable `AgentResult` describing the outcome of one completed interaction.

For this sprint it should contain only:

- success
- answer

Execution traces, metrics, diagnostics, usage, and timing belong to future sprints.

---

# Constraints

- Conversation must remain completely provider-independent.
- Conversation must be immutable.
- Provider-specific message translation must remain inside the LLM module.
- `main.py` must not orchestrate providers or tool execution.
- AgentRuntime must own the reasoning loop.
- ToolCallBridge remains responsible only for translating provider tool calls into ToolInvocations.
- ToolInvoker remains responsible only for executing tools.
- Do not introduce Planner.
- Do not introduce Memory.
- Do not introduce LangGraph.
- Do not introduce multi-agent behaviour.
- Do not implement persistence.
- Protect the runtime from infinite loops by introducing a configurable maximum iteration limit.

---

# Acceptance Criteria

The following interaction must work:

```python
runtime = AgentRuntime(...)

result = await runtime.run(
    "Read the README and explain this project."
)
```

The runtime must:

1. Create a Conversation.
2. Send it to the provider.
3. Receive tool calls.
4. Execute requested tools.
5. Append tool results into a new Conversation.
6. Continue communicating with the provider until no further tool calls exist.
7. Return an AgentResult.

Additionally:

- `main.py` only bootstraps the application and invokes `AgentRuntime`.
- Conversation contains only provider-independent domain models.
- Provider-specific message translation is isolated inside the LLM module.
- Existing Tool Framework requires no architectural changes.
- Existing ToolCallBridge requires no architectural changes.
- Existing ToolInvoker requires no architectural changes.

---

# Out of Scope

The following capabilities explicitly belong to future sprints:

- Conversation persistence
- Memory retrieval
- Planning
- Task decomposition
- Multi-agent collaboration
- Retry policies
- Parallel reasoning
- Human approval
- Evaluation framework
- Conversation summarisation
- Streaming responses
- Token usage optimisation
- Conversation branching
