"""Shell tool — :class:`ShellTool` for executing shell commands.

Runs commands in a subprocess with the workspace root as the working
directory, capturing stdout, stderr, and the exit code.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from tools.base import Tool
from tools.execution_context import ExecutionContext
from tools.metadata import ToolMetadata
from tools.result import ToolResult

logger = logging.getLogger(__name__)


class ShellTool(Tool):
    """Execute a shell command inside the workspace.

    The command runs in a subprocess with the workspace root as its
    working directory.  stdout, stderr, and the exit code are captured
    and returned as a formatted string.

    A configurable timeout (from :class:`ExecutionContext`) prevents
    hung commands from blocking the agent indefinitely.

    Usage::

        context = ExecutionContext(workspace_root=Path("/home/project"))
        tool = ShellTool()
        result = await tool.run(
            command="python -m pytest tests/ -v",
            _context=context,
        )
    """

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(
            name="shell",
            description=(
                "Execute a shell command inside the workspace directory. "
                "Returns STDOUT, STDERR, and EXIT_CODE. "
                "The command is terminated if it exceeds the configured timeout "
                "(default 30 seconds)."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": (
                            "The shell command to execute.  The command runs "
                            "with the workspace root as the working directory."
                        ),
                    },
                },
                "required": ["command"],
            },
        )

    # ------------------------------------------------------------------
    # Tool lifecycle
    # ------------------------------------------------------------------

    async def validate(self, **kwargs: Any) -> None:
        command = kwargs.get("command")
        if not command or not isinstance(command, str):
            raise ValueError("Missing or invalid required parameter 'command'")

    async def execute(self, **kwargs: Any) -> ToolResult:
        command: str = kwargs["command"]
        context: ExecutionContext = kwargs["_context"]
        timeout: int = context.shell_timeout_seconds

        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(context.workspace_root),
            )
        except OSError as exc:
            return ToolResult.fail(f"Failed to spawn subprocess: {exc}")

        try:
            stdout_bytes, stderr_bytes = await asyncio.wait_for(
                proc.communicate(), timeout=timeout
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return ToolResult.fail(f"Command timed out after {timeout}s: {command}")

        stdout = stdout_bytes.decode("utf-8", errors="replace")
        stderr = stderr_bytes.decode("utf-8", errors="replace")
        exit_code = proc.returncode if proc.returncode is not None else -1

        output = f"STDOUT:\n{stdout}STDERR:\n{stderr}EXIT_CODE: {exit_code}"
        return ToolResult.ok(output)
