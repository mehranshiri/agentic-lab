# ADR-005: Sprint 5 — Provider Tool Representation

**Status:** Accepted

**Date:** 2026-06-28

**Sprint:** 5 — Provider Tool Representation

---

## Decisions

Two architectural decisions were made to bridge the Tool Framework and
LLM providers without coupling them.

---

### 1. `ToolSchemaAdapter` Abstract Base Class

A new abstract base class, `ToolSchemaAdapter`, lives inside the LLM
module (`llm/representations/base.py`) and declares a single method:

```python
class ToolSchemaAdapter(ABC):
    @abstractmethod
    def to_provider_format(self, metadata: ToolMetadata) -> dict[str, Any]:
        ...
```

It depends on `ToolMetadata` (from the Tool Framework) but the Tool
Framework never imports or knows about any concrete adapter.

```text
 tools/ (stable domain)           llm/ (provider layer)
 ──────────────────────          ───────────────────────
 ToolMetadata (frozen)    ←──   ToolSchemaAdapter (ABC)
                                      ▲
                                      │ implements
                                      │
                          DeepSeekToolSchemaAdapter
                                      │
                                      ▼
                           {"type": "function",
                            "function": {...}}
```

**Rationale**

* **Dependency Inversion Principle** — the stable domain (`ToolMetadata`)
  defines the contract; provider-specific adapters depend on it, not the
  other way around. When providers change, only the representation
  layer is touched.
* **Single Responsibility** — `ToolCatalog` discovers tools;
  `ToolSchemaAdapter` translates them. Neither crosses into the other's
  concern.
* **Open for extension, closed for modification** — adding a new
  provider (e.g. OpenAI, Anthropic) means adding a single new concrete
  class; no existing code is modified.
* **Stateless** — representation instances hold no mutable state,
  making them safe to create, discard, or inject anywhere.
* **Testable in isolation** — the abstract base guarantees a uniform
  contract that every unit test can verify without touching network
  calls or tool execution.

**Trade-offs**

* **No input schemas yet** — `ToolMetadata` currently carries only
  `name` and `description`. The `parameters` block is emitted as an
  empty object (`{"type": "object", "properties": {}, "required": []}`)
  so that the definition is always structurally valid. Full parameter
  schemas belong to a future sprint.
* **One-way translation** — the representation layer only converts
  *from* metadata *to* provider format. The reverse path (parsing
  provider responses back into tool calls) is out of scope for this
  sprint.
* **No batch operation** — `to_provider_format()` processes one tool at
  a time. A `to_provider_format_batch()` convenience could be added
  later if needed.

---

### 2. `DeepSeekToolSchemaAdapter` Concrete Implementation

The first concrete adapter, `DeepSeekToolSchemaAdapter`
(`llm/representations/deepseek.py`), produces definitions matching the
DeepSeek Chat Completions API schema:

```json
{
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read the contents of a text file.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}
```

**Rationale**

* **OpenAI-compatible format** — DeepSeek follows the same
  `type/function` convention as OpenAI's function calling, so the
  output is immediately usable in `chat.completions.create(tools=...)`
  calls.
* **Provider isolation** — only this file knows the exact schema
  DeepSeek expects. If DeepSeek changes its schema, the fix is
  localised to a single file.
* **Composition root integration** — `app/main.py` is updated to
  demonstrate the full pipeline: registry → catalog → representation,
  proving the layers compose correctly without tight coupling.

**Trade-offs**

* **Hardcoded `"type": "function"`** — assumes all tools map to
  functions. If DeepSeek introduces non-function tool types in the
  future, the adapter will need updating. Currently this is
  inconsequential since only function-type tools exist.

---

## Files

| Action | File | Purpose |
|--------|------|---------|
| Create | `llm/representations/__init__.py` | Package init and exports |
| Create | `llm/representations/base.py` | `ToolSchemaAdapter` ABC |
| Create | `llm/representations/deepseek.py` | DeepSeek-specific adapter |
| Update | `llm/__init__.py` | Export new public symbols |
| Update | `app/main.py` | Demonstrate end-to-end pipeline |

---

## Related

* ADR-004: Sprint 4 — Tool Discovery (for `ToolCatalog` which feeds
  metadata into the representation layer)
* ADR-003: Sprint 3 — Tool Framework (for `ToolMetadata` frozen
  dataclass used as the translation input)
* ADR-002: Sprint 2 — LLM Infrastructure (for Strategy pattern
  continued by `ToolSchemaAdapter` ABC)
