"""Filesystem tools — currently :class:`ReadFileTool`.

Reads the contents of text files without modifying them.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from tools.base import Tool
from tools.metadata import ToolMetadata
from tools.result import ToolResult


class ReadFileTool(Tool):
    """Read a text file from the local filesystem.

    Usage::

        tool = ReadFileTool()
        result = await tool.run(path="/path/to/file.txt")
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="read_file",
            description="Read the contents of a text file. Does not modify the file.",
        )

    async def validate(self, **kwargs: Any) -> None:
        path_raw = kwargs.get("path")
        if not path_raw:
            raise ValueError("Missing required parameter 'path'")
        path = Path(path_raw).expanduser().resolve()
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.is_file():
            raise IsADirectoryError(f"Path is a directory, not a file: {path}")

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = Path(kwargs["path"]).expanduser().resolve()
        try:
            content = path.read_text(encoding="utf-8")
            return ToolResult.ok(content)
        except UnicodeDecodeError:
            return ToolResult.fail(
                f"Cannot read {path} as UTF-8 text — it may be a binary file."
            )