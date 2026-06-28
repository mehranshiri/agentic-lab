## Sprint 5 — Provider Tool Representation

## Goal

Introduce a provider-specific representation layer that converts our internal tool descriptions into the format expected by an LLM provider (currently DeepSeek).

This layer acts as an adapter between the Tool Framework and the LLM module while keeping both independent.

Why this sprint exists:

* The Tool Framework defines tools using our own domain model.

* LLM providers require their own tool/function schemas.

* Rather than exposing provider-specific formats throughout the application, we introduce a dedicated representation layer that translates between the two.

* This follows the Dependency Inversion Principle: our domain remains stable even if providers change.

---

## Responsibilities

### Provider Tool Representation

Responsible for:

* Receiving tool descriptions from the Tool Catalog.
* Converting them into the schema required by a specific provider.
* Remaining isolated inside the LLM module.
* Producing provider-ready definitions without executing tools.
* DeepSeek Representation

Implement the first concrete representation for DeepSeek.

Only DeepSeek-specific code should know the exact schema required by the provider.

---

## Constraints

* Do not execute tools.
* Do not implement tool calling.
* Do not parse LLM responses.
* Do not introduce planners or agents.
* Do not introduce LangGraph.
* Do not modify the Tool Framework.
* Keep provider-specific logic inside the LLM module.


---

## Acceptance Criteria

### I would define only four:

* The ToolCatalog provides tool descriptions to the LLM layer.
* The LLM layer converts them into DeepSeek's expected tool definition format.
* Provider-specific representation is isolated from the Tool Framework.
* `app/main.py` demonstrates generating DeepSeek-compatible tool definitions.