"""Filesystem tools — :class:`ReadFileTool` and :class:`WriteFileTool`.

Reads and writes text files within the workspace.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.base import Tool
from tools.execution_context import ExecutionContext
from tools.metadata import ToolMetadata
from tools.result import ToolResult


# ---------------------------------------------------------------------------
# Workspace boundary enforcement
# ---------------------------------------------------------------------------


class WorkspaceBoundaryError(ValueError):
    """Raised when a resolved path escapes the workspace root."""


def _enforce_workspace_boundary(path: Path, workspace_root: Path) -> None:
    """Raise :class:`WorkspaceBoundaryError` if *path* is outside *workspace_root*.

    Uses :meth:`Path.is_relative_to` which correctly handles symlinks
    after :meth:`Path.resolve` has canonicalised the path.
    """
    if not path.is_relative_to(workspace_root):
        raise WorkspaceBoundaryError(
            f"Path '{path}' is outside the workspace root '{workspace_root}'."
        )


# ---------------------------------------------------------------------------
# Shared path-resolution helper
# ---------------------------------------------------------------------------


def _resolve(path_raw: str, context: ExecutionContext) -> Path:
    """Resolve *path_raw* to an absolute :class:`Path` within *context.workspace_root*.

    Rules (in order):
    1. ``~`` expansion (``Path.expanduser()``).
    2. If absolute after expansion → used as-is.
    3. Otherwise resolved against ``context.workspace_root``.
    4. ``.resolve()`` to eliminate symlinks / ``..``.
    5. Boundary check — raises :class:`WorkspaceBoundaryError` if the
       resolved path is outside ``context.workspace_root``.
    """
    path = Path(path_raw).expanduser()
    if not path.is_absolute():
        path = context.workspace_root / path
    resolved = path.resolve()
    _enforce_workspace_boundary(resolved, context.workspace_root)
    return resolved


# ---------------------------------------------------------------------------
# ReadFileTool
# ---------------------------------------------------------------------------


class ReadFileTool(Tool):
    """Read a text file from the local filesystem.

    Relative paths are resolved against the :attr:`workspace_root`
    provided by the :class:`ExecutionContext` injected via
    the ``_context`` keyword argument.  Absolute paths bypass the
    workspace root and are used as-is.

    Usage::

        context = ExecutionContext(workspace_root=Path("/home/project"))
        tool = ReadFileTool()
        result = await tool.run(path="README.md", _context=context)
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="read_file",
            description="Read the contents of a text file. Does not modify the file.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path (relative or absolute) of the file to read.",
                    }
                },
                "required": ["path"],
            },
        )

    # ------------------------------------------------------------------
    # Tool lifecycle
    # ------------------------------------------------------------------

    async def validate(self, **kwargs: Any) -> None:
        path_raw = kwargs.get("path")
        if not path_raw:
            raise ValueError("Missing required parameter 'path'")
        context = kwargs["_context"]
        path = _resolve(path_raw, context)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = _resolve(kwargs["path"], kwargs["_context"])
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult.ok(content)
        except UnicodeDecodeError:
            return ToolResult.fail(
                f"Cannot read {path} as UTF-8 text — it may be a binary file."
            )


# ---------------------------------------------------------------------------
# WriteFileTool
# ---------------------------------------------------------------------------


class WriteFileTool(Tool):
    """Create or overwrite a text file on the local filesystem.

    Relative paths are resolved against the :attr:`workspace_root`
    provided by the :class:`ExecutionContext`.  Intermediate directories
    are created automatically.  The write is atomic: content is written
    to a temporary file first, then renamed into place to avoid corruption
    on partial writes.

    Usage::

        context = ExecutionContext(workspace_root=Path("/home/project"))
        tool = WriteFileTool()
        result = await tool.run(
            path="src/Button.tsx",
            content="import React from 'react';\n...",
            _context=context,
        )
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="write_file",
            description=(
                "Create or overwrite a text file. Creates intermediate "
                "directories automatically. The file is written atomically."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "The path (relative or absolute) of the file to write. "
                            "Relative paths are resolved against the workspace root."
                        ),
                    },
                    "content": {
                        "type": "string",
                        "description": "The full text content to write to the file.",
                    },
                },
                "required": ["path", "content"],
            },
        )

    # ------------------------------------------------------------------
    # Tool lifecycle
    # ------------------------------------------------------------------

    async def validate(self, **kwargs: Any) -> None:
        path_raw = kwargs.get("path")
        if not path_raw:
            raise ValueError("Missing required parameter 'path'")
        # content will be checked in execute — empty string is valid

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = _resolve(kwargs["path"], kwargs["_context"])
        content = kwargs.get("content", "")

        try:
            # Ensure parent directories exist
            path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write: write to temp file in same directory, then rename
            # (rename is atomic on Unix when source and dest are on the same filesystem)

            tmp = path.with_suffix(path.suffix + ".tmp")
            tmp.write_text(content, encoding="utf-8")
            tmp.rename(path)

            return ToolResult.ok(f"Written {path} ({len(content)} bytes)")
        except OSError as exc:
            return ToolResult.fail(f"Failed to write {path}: {exc}")
