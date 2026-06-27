# ADR-002: Sprint 2 — LLM Infrastructure

**Status:** Accepted

**Date:** 2026-06-27 (backfilled)

**Sprint:** 2 — LLM Infrastructure

---

## Decisions

Three architectural decisions were made to build the provider-agnostic
LLM layer.

---

### 1. Strategy Pattern for LLM Providers

The `LlmProvider` abstract base class defines a common interface that
every provider implements. `LlmClient` depends on the abstraction, not
on any concrete provider. Providers are injected at startup.

```
Application
      │  depends on
      ▼
 LlmClient ──delegates to──▶ LlmProvider (ABC)
                                  ▲
                                  │  implements
                        ┌─────────┴─────────┐
                        │                   │
                  DeepSeekProvider    (future: OpenAI, ...)
```

```python
class LlmProvider(ABC):
    @abstractmethod
    async def send_message(
        self, messages: list[dict[str, str]], *, model=None,
        temperature=0.7, max_tokens=4096,
    ) -> LLMResponse: ...
```

**Rationale**

* **Swap providers without touching application code** — switching from
  DeepSeek to OpenAI means writing one new class and changing the
  composition root (`app/main.py`).
* **Testability** — tests can inject a mock or fake provider without
  network calls.
* **Single responsibility** — providers own API communication; the
  client owns the user-facing convenience layer.
* **Matches Open/Closed Principle** — open for extension (new
  providers), closed for modification (client and app code unchanged).

**Trade-off:** The abstract method signature (`messages: list[dict]`,
`temperature`, `max_tokens`) is shaped for Chat Completions APIs. A
non-chat provider (e.g., embeddings, image generation) would require a
separate abstraction or a wider interface. This is acceptable because
the sprint scopes to chat/text generation only.

---

### 2. LlmClient as a Facade

`LlmClient` wraps the provider with a simpler `generate(prompt)` method
that accepts a plain string and returns a structured `LLMResponse`.

```python
class LlmClient:
    def __init__(self, provider: LlmProvider): ...
    async def generate(self, prompt: str) -> LLMResponse:
        messages = [{"role": "user", "content": prompt}]
        return await self._provider.send_message(messages)
```

**Rationale**

* **Hides provider complexity** — callers send a string, not a
  `messages` list.
* **Single entry point** — the entire application talks to LLMs through
  one object, making logging, rate-limiting, and retries trivial to add
  later.
* **Consistent error surface** — the client is the natural place for
  future cross-cutting concerns (retry, fallback, circuit breaker).

**Trade-off:** The facade accepts only a single user message. Multi-turn
conversations will need a different method or a higher-level abstraction
(e.g., `Agent`). This is intentional — the sprint targets
request/response, not dialogue.

---

### 3. LLMResponse as a Frozen Value Object

`LLMResponse` is a frozen `@dataclass` that captures everything a
caller might need from a completion.

```python
@dataclass(frozen=True)
class LLMResponse:
    text: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    finish_reason: str = ""
    raw: Any = None
```

**Rationale**

* **Immutable** — no downstream code can accidentally mutate a response.
* **Provider-agnostic** — `text`, `model`, `usage`, and `finish_reason`
  are common to all Chat Completions APIs.
* **Debug-friendly** — `raw` preserves the provider's original response
  for inspection without exposing it to application logic.
* **Hashable** — can be used in sets, dicts, and caches.
* **Establishes a pattern** — the same frozen-dataclass-as-value-object
  pattern is reused for `Settings`, `ToolResult`, and `ToolMetadata` in
  later sprints.

**Trade-off:** The `raw: Any` field is opaque and provider-specific.
Tests or debugging code that inspects `raw` become coupled to a specific
provider's SDK types. This is acceptable because `raw` is explicitly
documented as debugging-only.

---

## Related

* ADR-001: Sprint 1 — Project Foundation (for `Settings` frozen
  dataclass and composition root in `app/main.py`)
* ADR-003: Sprint 3 — Tool Framework (for continued use of frozen
  dataclasses and Strategy/Template Method patterns)