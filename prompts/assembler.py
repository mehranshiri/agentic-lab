"""System prompt assembler — composes a :class:`SystemPrompt` from context.

The assembler discovers and combines instruction blocks from multiple
sources (builtin identity, available tools, workspace context) into a
single provider-independent :class:`SystemPrompt`.
"""

from __future__ import annotations

from prompts.models import InstructionBlock, SystemPrompt
from tools.catalog import ToolCatalog
from tools.execution_context import ExecutionContext


class SystemPromptAssembler:
    """Assemble a :class:`SystemPrompt` from the agent's current context.

    Responsibilities:
    * Produce the built-in identity / role description.
    * Enumerate available tools from the :class:`ToolCatalog`.
    * Describe the workspace from the :class:`ExecutionContext`.
    * Optionally inject user-provided instruction blocks.
    * Return a complete, ordered :class:`SystemPrompt`.

    The assembler is stateless — every call to :meth:`assemble` produces
    a fresh :class:`SystemPrompt` reflecting the current catalog and
    execution context.
    """

    # ------------------------------------------------------------------
    # Built-in identity block — the agent's core constitution
    # ------------------------------------------------------------------

    _BUILTIN_IDENTITY = """\
You are an expert AI coding agent. You have access to tools for \
reading, writing, and searching files, and executing shell commands \
within a designated workspace directory.

## Behaviour

- Always read a file before modifying it.
- Never execute destructive shell commands without careful consideration.
- All file paths are relative to the workspace root unless specified otherwise.
- Follow coding conventions found in the workspace.
- When uncertain, ask clarifying questions before acting."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assemble(
        self,
        context: ExecutionContext,
        catalog: ToolCatalog,
        *,
        extra_blocks: tuple[InstructionBlock, ...] = (),
    ) -> SystemPrompt:
        """Assemble a complete system prompt from all available sources.

        Parameters
        ----------
        context:
            The execution context describing the workspace environment.
        catalog:
            The tool catalog providing metadata for all registered tools.
        extra_blocks:
            Optional additional instruction blocks (e.g. user-provided
            guardrails or workspace-specific conventions).

        Returns
        -------
        SystemPrompt
            An immutable, provider-independent system prompt ready for
            provider-specific formatting.
        """
        blocks: list[InstructionBlock] = []

        # 1. Core identity — always first
        blocks.append(
            InstructionBlock(content=self._BUILTIN_IDENTITY, source="builtin")
        )

        # 2. Available tools — dynamically discovered
        blocks.append(
            InstructionBlock(
                content=self._build_tools_block(catalog),
                source="tools",
            )
        )

        # 3. Workspace context
        blocks.append(
            InstructionBlock(
                content=self._build_workspace_block(context),
                source="workspace",
            )
        )

        # 4. User / workspace extra instructions
        blocks.extend(extra_blocks)

        return SystemPrompt(blocks=tuple(blocks))

    # ------------------------------------------------------------------
    # Block builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_tools_block(catalog: ToolCatalog) -> str:
        """Build a markdown-formatted block listing available tools."""
        tools = catalog.list_tools()
        if not tools:
            return "## Available Tools\n\nNo tools are currently available."

        lines: list[str] = ["## Available Tools", ""]
        for tool in tools:
            lines.append(f"- **{tool.name}**: {tool.description}")
        return "\n".join(lines)

    @staticmethod
    def _build_workspace_block(context: ExecutionContext) -> str:
        """Build a block describing the workspace environment."""
        return (
            "## Workspace\n\n"
            f"- **Root**: {context.workspace_root}\n"
            f"- **Shell timeout**: {context.shell_timeout_seconds}s\n"
            f"- **Grep max results**: {context.grep_max_results}"
        )
