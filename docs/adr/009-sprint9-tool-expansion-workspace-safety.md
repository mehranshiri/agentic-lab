# ADR-009: Sprint 9 — Tool Expansion & Workspace Safety

**Status:** Accepted

**Date:** 2026-07-12

**Sprint:** 9 — Tool Expansion & Workspace Safety

---

## Decisions

Seven architectural decisions were made to expand tool capabilities
(`ShellTool`, `GrepTool`) and harden the filesystem boundary.

---

### 1. Workspace Boundary as a Separate Function Called From `_resolve`

The boundary check is implemented as `_enforce_workspace_boundary(path, workspace_root)`
— a standalone function — rather than inlined inside `_resolve`.

```python
def _enforce_workspace_boundary(path: Path, workspace_root: Path) -> None:
    if not path.is_relative_to(workspace_root):
        raise WorkspaceBoundaryError(...)

def _resolve(path_raw: str, context: ExecutionContext) -> Path:
    ...
    resolved = path.resolve()
    _enforce_workspace_boundary(resolved, context.workspace_root)
    return resolved
```

**Rationale**

* **Single Responsibility** — `_resolve` owns resolution logic (expand,
  join, canonicalise). `_enforce_workspace_boundary` owns security
  policy. Two concerns, two functions.
* **Independently testable** — the boundary function can be unit-tested
  with edge cases (symlink escapes, exact boundary, `..` traversal)
  without going through `_resolve`.
* **Callers can't forget** — because `_resolve` calls the boundary
  function internally, every tool that resolves a path gets enforcement
  automatically. No tool author needs to remember to call it.

**Trade-offs**

* **Extra function call** — negligible cost for the clarity gained.
* **No standalone enforcement** — tools that don't use `_resolve`
  (e.g. `ShellTool`, which delegates to a subprocess) must enforce
  the boundary through other means (the subprocess `cwd`).  This is
  intentional — each tool owns its safety perimeter.

---

### 2. `_resolve` Now Requires `ExecutionContext` — No More `| None`

Before Sprint 9, `_resolve` accepted `context: ExecutionContext | None`.
When `None`, the function skipped workspace-relative resolution — an
implicit escape hatch.  Sprint 9 makes `context` mandatory.

```python
# Before
def _resolve(path_raw: str, context: ExecutionContext | None) -> Path: ...

# After
def _resolve(path_raw: str, context: ExecutionContext) -> Path: ...
```

**Rationale**

* **Eliminates the null-context escape hatch** — without a workspace
  root, there is nothing to enforce against.  Making `context` mandatory
  closes this gap at the type level.
* **Reflects reality** — `ToolInvoker` always supplies an
  `ExecutionContext`.  No production caller ever passed `None`.
  The `| None` was defensive coding for a scenario that never
  materialised.

**Trade-offs**

* **Breaks hypothetical callers without context** — but no such callers
  exist.  If one emerges, it must supply an `ExecutionContext`, which is
  the correct behaviour.

---

### 3. Boundary Check After `.resolve()` — Catches Symlink Escapes

The boundary check runs **after** `Path.resolve()`, which canonicalises
the path by following symlinks and eliminating `..` components.

```python
path = Path(path_raw).expanduser()
if not path.is_absolute():
    path = context.workspace_root / path
resolved = path.resolve()          # ← canonicalises, follows symlinks
_enforce_workspace_boundary(...)   # ← check AFTER
```

**Rationale**

* **Symlink escape detection** — if a symlink inside the workspace
  points outside (e.g. `workspace/secrets -> /etc`), the logical path
  appears safe but the real path escapes.  Checking after `.resolve()`
  catches this because `/etc/passwd` is not relative to the workspace
  root.
* **`Path.is_relative_to` is symlink-aware** — after `.resolve()`,
  `is_relative_to` compares canonical paths, so it correctly identifies
  the escape.

**Trade-offs**

* **`.resolve()` follows symlinks eagerly** — if a symlink chain is
  broken (dangling symlink), `.resolve()` raises `OSError`.  This is
  handled by the caller (e.g. `validate` checks `path.exists()`
  separately).
* **No TOCTOU protection** — the path could change between the check
  and the actual file operation.  This is a known limitation of
  filesystem-level checks and is acceptable for a development agent
  running in a trusted environment.

---

### 4. No `allow_absolute` Opt-Out — Boundary is Universal

The original Sprint 9 plan proposed an `allow_absolute: bool = False`
parameter on `_resolve` for legitimate absolute path access (e.g.
reading system config files).  This was rejected.

**Rationale**

* **No consumer exists** — no current tool needs to read files outside
  the workspace.  Adding an opt-out before a real use case emerges
  violates the project guideline: *"Don't add extensibility points
  until they have a second consumer."*
* **Security simplicity** — a universal boundary is easier to reason
  about and audit than a conditional one.  Every path through `_resolve`
  is guaranteed to be within the workspace.
* **Can be added later** — when a legitimate use case emerges (e.g. a
  `ReadSystemConfigTool`), `allow_absolute` can be added with a clear
  purpose and consumer.

---

### 5. `ShellTool` and `GrepTool` in Separate Modules

Each new tool lives in its own module (`tools/shell.py`, `tools/grep.py`)
rather than being added to `tools/filesystem.py`.

**Rationale**

* **Domain distinction** — `filesystem.py` owns file I/O.  Shell
  execution and code search are different domain concepts with different
  dependencies (`asyncio.subprocess`, `re`).
* **Single Responsibility at the module level** — each module contains
  exactly one tool class plus its private helpers.  No module grows
  beyond a single concern.
* **Consistent with project structure** — the existing pattern already
  separates `catalog.py`, `registry.py`, `invoker.py`, and
  `invocation.py` by responsibility.  Grouping tools by domain
  continues this convention.

**Trade-offs**

* **More files** — four tool modules instead of one.  Accepted as the
  cost of clear separation.

---

### 6. `shell_timeout_seconds` and `grep_max_results` on `ExecutionContext`

Runtime constraints (`shell_timeout_seconds`, `grep_max_results`) live
on `ExecutionContext` rather than as tool parameters.

```python
@dataclass(frozen=True)
class ExecutionContext:
    workspace_root: Path
    shell_timeout_seconds: int = 30
    grep_max_results: int = 100
```

**Rationale**

* **Application controls policy** — the timeout and result cap are
  operational constraints set by the application, not the LLM.  Putting
  them on `ExecutionContext` keeps them out of the tool's JSON Schema
  and prevents the LLM from requesting arbitrary timeouts.
* **Single point of configuration** — all runtime limits are discoverable
  in one place.  Adding a new limit (e.g. `max_file_size_bytes`) follows
  the same pattern.
* **Domain alignment** — "how long can a command run in this environment"
  and "how many search results can we return" are execution environment
  concerns, not tool-specific concerns.

**Trade-offs**

* **ExecutionContext grows** — each new operational constraint adds a
  field.  If the number of fields grows too large, they can be grouped
  into sub-objects (e.g. `ShellConfig`, `GrepConfig`) without breaking
  the public API.

---

### 7. `ToolResult` Stays String-Only — No `data` Field

The option of adding `data: dict[str, Any] | None = None` to
`ToolResult` for structured output was considered and rejected.

**Rationale**

* **No programmatic consumer** — today, tool results flow into
  conversation messages as text.  The LLM reads `content`.  There is
  no code that inspects or branches on structured tool output.
* **YAGNI** — the project guideline states: *"Don't add extensibility
  points until they have a second consumer."*  A `data` field with no
  consumer is dead code.
* **Serialization is sufficient** — ShellTool serialises `{stdout,
  stderr, exit_code}` into a formatted string.  GrepTool serialises
  matches into `file:line:content` lines.  Both are human- and
  LLM-readable.
* **Can be added later** — `ToolResult` is constructed only via `ok()`
  and `fail()` factory methods.  Adding a `data` parameter later is a
  backwards-compatible change.

---

### 8. `WorkspaceBoundaryError` Defined in `filesystem.py`

The new exception class lives in `tools/filesystem.py` alongside
`_enforce_workspace_boundary`, not in a separate `tools/exceptions.py`
module.

**Rationale**

* **Single consumer** — only `_enforce_workspace_boundary` raises it
  and only `_resolve` (same module) propagates it.
* **Extract when needed** — when a second module needs to import or
  raise `WorkspaceBoundaryError`, it can be extracted to a shared
  location.  Until then, locality wins.
