---
description: "Refactor selected code to reduce complexity, improve naming, and remove duplication. Select code and run /refactor."
agent: "agent"
---
Refactor the selected code following the project's [copilot-instructions.md](../copilot-instructions.md) for conventions on SOLID, architecture patterns, and code style.

If no code is selected, ask the user to select the code they want refactored before proceeding.

## Goals

1. **Reduce complexity** — Flatten deep nesting, split long functions, simplify conditionals.
2. **Preserve behavior** — The refactor must not change any observable behavior. Existing tests must still pass.
3. **Improve naming** — Variables, functions, and classes should reveal intent without needing comments.
4. **Improve testability** — Extract side effects, inject dependencies, avoid hidden state.
5. **Remove duplication** — If the same logic appears elsewhere in the codebase, extract it to a shared location (check `core/`, `llm/base.py`, `tools/base.py` first).

## Output

Apply the refactor directly, then explain:

- **What changed** — each modification and why
- **Why behavior is preserved** — how you verified the refactor is safe
- **Trade-offs considered** — alternatives you rejected and why
