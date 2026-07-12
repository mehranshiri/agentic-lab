---
description: "Review code as a Staff Software Engineer for correctness, architecture, security, and testability. Select code and run /review."
agent: "agent"
---
Review the selected code as a Staff Software Engineer. Follow the project's [copilot-instructions.md](../copilot-instructions.md) for conventions on SOLID, architecture patterns, and code style.

If no code is selected, ask the user to select the code they want reviewed before proceeding.

## What to check

- **Correctness** — Does the code do what it claims? Are there logic errors?
- **Bugs** — Null/invalid-state handling, off-by-one, incorrect conditionals.
- **Race conditions** — Shared mutable state, async ordering assumptions, missing synchronization.
- **Edge cases** — Empty inputs, boundary values, error paths, resource exhaustion.
- **Performance** — Unnecessary allocations, O(n²) patterns, blocking I/O on hot paths.
- **Readability** — Naming clarity, function length, comment quality, cognitive load.
- **Architecture** — Does it follow the project's patterns (Strategy, Template Method, Dependency Inversion)? Is it in the right module?
- **SOLID** — Single responsibility, open/closed, Liskov, interface segregation, dependency inversion.
- **Security** — Injection risks, secrets in code, path traversal, unsafe deserialization.
- **Testability** — Is the code easy to test? Are dependencies injectable? Are side effects isolated?

## Output format

### 🔴 Critical issues
Issues that could cause data loss, security breaches, or incorrect behavior in production.

### 🟡 Important issues
Bugs, race conditions, or design problems that should be fixed before merging.

### 🔵 Suggestions
Readability improvements, minor optimizations, or alternative approaches worth considering.

**Do not rewrite code unless a fix is necessary to illustrate a critical issue.** Focus on explaining what's wrong and why.
