# Sprint 2 – LLM Infrastructure

## Sprint Goal

Build a reusable and provider-agnostic LLM infrastructure that enables the application to communicate with language models through a clean abstraction.

The objective is **not** to build an AI agent. Instead, this sprint establishes the foundation that future agents will use to interact with LLM providers.

---

## Architecture

```text
Application
      │
      ▼
LLM Client (Abstraction)
      │
      ▼
DeepSeek Provider
      │
      ▼
DeepSeek API
```

The application should depend only on the LLM abstraction and remain unaware of the underlying provider implementation.

---

## Files to Create

### `core/config.py`

**Responsibilities**

* Load configuration from environment variables.
* Validate required settings.
* Expose a configuration object to the application.

---

### `llm/providers/deepseek.py`

**Responsibilities**

* Implement communication with the DeepSeek API.
* Encapsulate all provider-specific logic.
* Return plain text responses.

---

### `llm/client.py`

**Responsibilities**

* Expose a provider-independent interface to the application.
* Delegate requests to the configured provider.
* Prevent provider-specific code from leaking into other modules.

---

### `app/main.py`

**Responsibilities**

* Initialize the application.
* Create an LLM client.
* Send a simple prompt.
* Print the returned response.

---

## Constraints

* Do **not** introduce LangGraph.
* Do **not** introduce LangChain.
* Do **not** implement tools.
* Do **not** implement agent logic.
* Do **not** implement memory.
* Do **not** implement prompt management.
* Keep the implementation minimal and focused on LLM communication.

---

## Acceptance Criteria

* Configuration is loaded from environment variables.
* The application communicates successfully with the DeepSeek API.
* Running

```bash
uv run python -m app.main
```

produces a valid response to a simple prompt.

* Only the provider module contains provider-specific code.
* The application depends only on the `LLMClient` abstraction.
