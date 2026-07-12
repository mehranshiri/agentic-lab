"""Grep tool — :class:`GrepTool` for searching file contents.

Searches files within the workspace using a regex pattern, returning
matching file paths, line numbers, and line content.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from tools.base import Tool
from tools.execution_context import ExecutionContext
from tools.metadata import ToolMetadata
from tools.result import ToolResult

logger = logging.getLogger(__name__)


class GrepTool(Tool):
    """Search file contents within the workspace using a regex pattern.

    Only files within the workspace root are searched.  Binary files
    are silently skipped.  Results are capped at the configured maximum
    to avoid overwhelming the LLM context window.

    Usage::

        context = ExecutionContext(workspace_root=Path("/home/project"))
        tool = GrepTool()
        result = await tool.run(
            pattern="def _resolve",
            glob="**/*.py",
            _context=context,
        )
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="grep",
            description=(
                "Search file contents within the workspace using a regex pattern. "
                "Returns matching file paths, line numbers, and line content. "
                "Results are capped to avoid overwhelming output."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "The regex pattern to search for.",
                    },
                    "glob": {
                        "type": "string",
                        "description": (
                            "Glob pattern to filter files (e.g. '**/*.py'). "
                            "Defaults to '**/*' (all files)."
                        ),
                    },
                },
                "required": ["pattern"],
            },
        )

    # ------------------------------------------------------------------
    # Tool lifecycle
    # ------------------------------------------------------------------

    async def validate(self, **kwargs: Any) -> None:
        pattern = kwargs.get("pattern")
        if not pattern or not isinstance(pattern, str):
            raise ValueError("Missing or invalid required parameter 'pattern'")
        # Compile early to fail fast on invalid regex
        try:
            re.compile(pattern)
        except re.error as exc:
            raise ValueError(f"Invalid regex pattern: {exc}") from exc

    async def execute(self, **kwargs: Any) -> ToolResult:
        pattern: str = kwargs["pattern"]
        glob_pattern: str = kwargs.get("glob", "**/*")
        context: ExecutionContext = kwargs["_context"]
        max_results: int = context.grep_max_results

        compiled = re.compile(pattern)
        matches: list[str] = []

        try:
            for file_path in context.workspace_root.glob(glob_pattern):
                if not file_path.is_file():
                    continue

                # Read and search the file
                try:
                    lines = file_path.read_text(encoding="utf-8").splitlines()
                except (UnicodeDecodeError, OSError):
                    # Binary or unreadable — skip silently
                    continue

                for line_no, line in enumerate(lines, start=1):
                    if compiled.search(line):
                        relative = file_path.relative_to(context.workspace_root)
                        matches.append(f"{relative}:{line_no}:{line}")
                        if len(matches) >= max_results:
                            break

                if len(matches) >= max_results:
                    break

        except OSError as exc:
            return ToolResult.fail(f"Failed to search workspace: {exc}")

        if not matches:
            return ToolResult.ok("No matches found.")

        output = "\n".join(matches)
        if len(matches) >= max_results:
            output += f"\n... (results truncated at {max_results} matches)"

        return ToolResult.ok(output)
