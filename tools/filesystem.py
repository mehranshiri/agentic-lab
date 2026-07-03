"""Filesystem tools — currently :class:`ReadFileTool`.

Reads the contents of text files without modifying them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.base import Tool
from tools.execution_context import ExecutionContext
from tools.metadata import ToolMetadata
from tools.result import ToolResult


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
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve(path_raw: str, context: ExecutionContext | None) -> Path:
        """Resolve *path_raw* to an absolute :class:`Path`.

        Rules (in order):
        1. ``~`` expansion (``Path.expanduser()``).
        2. If absolute after expansion → used as-is.
        3. Otherwise resolved against ``context.workspace_root``.
        4. Finally ``.resolve()`` to eliminate symlinks / ``..``.
        """
        path = Path(path_raw).expanduser()
        if not path.is_absolute() and context is not None:
            path = context.workspace_root / path
        return path.resolve()

    # ------------------------------------------------------------------
    # Tool lifecycle
    # ------------------------------------------------------------------

    async def validate(self, **kwargs: Any) -> None:
        path_raw = kwargs.get("path")
        if not path_raw:
            raise ValueError("Missing required parameter 'path'")
        context = kwargs.get("_context")
        path = self._resolve(path_raw, context)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = self._resolve(kwargs["path"], kwargs.get("_context"))
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult.ok(content)
        except UnicodeDecodeError:
            return ToolResult.fail(
                f"Cannot read {path} as UTF-8 text — it may be a binary file."
            )
