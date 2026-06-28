# ADR-004: Sprint 4 — Tool Discovery

**Status:** Accepted

**Date:** 2026-06-27

**Sprint:** 4 — Tool Discovery

---

## Decisions

One architectural decision was made to introduce the discovery layer.

---

### ToolCatalog as a Separate Discovery Layer

The `ToolCatalog` is a stateless bridge between the `ToolRegistry` and
future LLM integrations. It queries the registry on every call and
returns `ToolMetadata` snapshots — it never executes tools or caches
information.

```text
                +----------------+
                | Tool Registry  |   (source of truth for instances)
                +----------------+
                        |
                 discovers tools
                        |
                        ▼
                +----------------+
                | Tool Catalog   |   (discovery only — no execution)
                +----------------+
                        |
              returns ToolMetadata
                        |
                        ▼
          Future LLM Provider Adapters
```

```python
class ToolCatalog:
    def __init__(self, registry: ToolRegistry) -> None:
        self._registry = registry

    def list_tools(self) -> list[ToolMetadata]:
        return [tool.metadata for tool in self._registry.list_tools()]
```

**Rationale**

* **Separation of discovery and execution** — the registry owns tool
  lifecycle (registration, retrieval, execution); the catalog owns
  introspection. This split means LLM adapter code never touches tool
  instances directly.
* **No caching** — the catalog queries the registry on every call,
  guaranteeing that dynamically registered tools are immediately visible
  without invalidation logic.
* **Stateless** — the catalog holds only a reference to the registry. It
  can be instantiated anywhere without side effects — useful for
  injecting into LLM prompt builders or CLI `list-tools` commands.
* **Dependency Inversion** — the catalog depends on `ToolRegistry`
  (abstraction of an abstraction), not on concrete tools. New tools
  added to the registry automatically appear through the catalog.
* **Slim API surface** — a single `list_tools()` method is intentionally
  narrow. Future methods (e.g., `describe(name)`, `search(query)`) can
  be added without breaking callers.

**Trade-offs**

* **No filtering or search** — `list_tools()` returns all tools. A
  system with 50+ tools would benefit from `search()` or `by_category()`,
  but the sprint intentionally keeps the catalog minimal.
* **No tool input schemas** — LLM function-calling requires schemas
  describing tool parameters. This belongs to a future "provider
  adapter" layer (Sprint 5+), not the catalog itself.

**Future Considerations**

* Add `describe(name: str) -> ToolMetadata | None` for single-tool
  lookup by name.
* Provider adapters will consume the catalog and generate
  provider-specific schemas (e.g., JSON Schema for OpenAI function
  calling) without coupling to the catalog.

---

## Related

* ADR-003: Sprint 3 — Tool Framework (for `ToolRegistry` and
  `ToolMetadata`)