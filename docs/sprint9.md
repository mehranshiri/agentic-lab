# Sprint 9 — Tool Expansion & Workspace Safety

## Goal

Expand the agent's tool capabilities with shell command execution and code search, while hardening the filesystem boundary to prevent path traversal outside the workspace.

The agent must become capable of running shell commands, searching file contents, and interacting with its environment — all while remaining safely confined to the workspace root.

---

# Why this sprint exists

After Sprint 8:

* The agent can read and write files within the workspace.
* The reasoning loop executes end-to-end.
* The architecture is cleanly separated across all boundaries.

However, the agent is severely limited:

* It cannot run commands (tests, lint, install, build).
* It cannot search for code patterns without reading every file.
* The filesystem resolution (`_resolve`) allows absolute paths to bypass the workspace root — a security gap.

Sprint 9 closes these capability and safety gaps before moving to developer experience or observability.

---

# Responsibilities

## 1. ShellTool

Introduce a `ShellTool` that executes shell commands within the workspace.

The ShellTool:

* Accepts a shell command string as input.
* Runs the command in a subprocess with the workspace root as the working directory.
* Captures stdout, stderr, and the exit code as a formatted string in `ToolResult.content`.
* Enforces a configurable timeout via `ExecutionContext.shell_timeout_seconds`.
* Does **not** provide an interactive shell — each invocation is stateless and isolated.

```python
result = await shell_tool.run(
    command="python -m pytest tests/ -v",
    _context=context,
)
# result.content contains formatted output with STDOUT, STDERR, and EXIT_CODE
```

---

## 2. GrepTool

Introduce a `GrepTool` that searches file contents within the workspace using regex patterns.

The GrepTool:

* Accepts a regex pattern and an optional file glob filter (e.g. `**/*.py`).
* Searches all matching files within the workspace root.
* Returns matching file paths, line numbers, and line content.
* Respects the workspace boundary — never searches outside `workspace_root`.
* Caps results at a configurable maximum via `ExecutionContext.grep_max_results`.

```python
result = await grep_tool.run(
    pattern="def _resolve",
    glob="**/*.py",
    _context=context,
)
# result.content contains lines in "file:line:content" format
```

---

## 3. Workspace Boundary Enforcement

Harden `_resolve` in `tools/filesystem.py` to enforce a workspace safety boundary.

Current behaviour:

* Relative paths are resolved against `workspace_root` — **safe**.
* Absolute paths bypass `workspace_root` entirely — **unsafe** (e.g. `/etc/passwd`).

New behaviour:

1. `_resolve` now requires `ExecutionContext` (no longer optional) — every caller must supply one.
2. After `.resolve()`, a separate `_enforce_workspace_boundary` function verifies the final path is within `workspace_root` using `Path.is_relative_to()`.
3. If the path escapes the workspace, a `WorkspaceBoundaryError` is raised.
4. Symlink escapes (e.g. `workspace/link -> /etc`) are caught because the check runs after `.resolve()` canonicalises the path.
5. No `allow_absolute` opt-out — all callers are subject to the same boundary.

```python
def _resolve(path_raw: str, context: ExecutionContext) -> Path:
    path = Path(path_raw).expanduser()
    if not path.is_absolute():
        path = context.workspace_root / path
    resolved = path.resolve()
    _enforce_workspace_boundary(resolved, context.workspace_root)
    return resolved
```

---

## 4. Register WriteFileTool in main.py

Close the gap from Sprint 8: `WriteFileTool` is implemented and exported but not registered in `main.py`. Add it alongside `ReadFileTool`.

---

# Architecture

```text
                        AgentRuntime
                             │
                             ▼
                      ToolCallBridge
                             │
                             ▼
                       ToolInvoker
                             │
                             ▼
                       ToolRegistry
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ReadFileTool   WriteFileTool    ShellTool   GrepTool
              │              │              │           │
              └──────────────┴──────────────┴───────────┘
                             │
                             ▼
                       _resolve()
                             │
                     Workspace Boundary
                     (path must be within
                      workspace_root)
```

---

# Acceptance Criteria

1. **ShellTool**: The agent can run `python -m pytest tests/ -v` and receive stdout, stderr, and exit code.
2. **ShellTool timeout**: A command exceeding the configured timeout is terminated and reported as a failure.
3. **GrepTool**: Searching for `def test_` in `tests/**/*.py` returns all matching lines with file paths and line numbers.
4. **GrepTool result cap**: Results are capped at the configured maximum.
5. **Workspace boundary**: Resolving `/etc/passwd` raises `WorkspaceBoundaryError`.
6. **Workspace boundary**: Resolving `../../outside` relative to `workspace_root` raises `WorkspaceBoundaryError`.
7. **Symlink boundary**: A symlink pointing outside the workspace followed by `.resolve()` raises `WorkspaceBoundaryError`.
8. **WriteFileTool registered**: `main.py` registers `ReadFileTool`, `WriteFileTool`, `ShellTool`, and `GrepTool`.
9. **Existing tools unchanged**: `ReadFileTool` and `WriteFileTool` continue to work without modification to their public API.
10. **No provider leakage**: ShellTool and GrepTool have zero imports from `llm/`.
11. **Timeout enforced**: Shell commands exceeding `context.shell_timeout_seconds` are killed and reported as failures.
12. **Grep result cap**: Grep results are truncated at `context.grep_max_results`.

---

# Constraints

* ShellTool must be stateless — no persistent shell sessions.
* ShellTool must enforce a timeout on every command execution.
* GrepTool must respect the workspace boundary.
* `_resolve` must remain a shared helper used by all filesystem-adjacent tools.
* New tools must follow the existing `validate → execute` lifecycle with frozen `ToolMetadata`.
* Do not introduce a task planner or workflow engine.
* Do not implement interactive or streaming shell sessions.
* Do not add parallel tool execution.
* Do not introduce LangGraph, Memory, or multi-agent behaviour.
* Keep the same provider-independent architecture — Shell and Grep are just more tools in the registry.
