"""Tool invoker — execution boundary for single-tool invocation.

The invoker receives a :class:`ToolInvocation`, resolves the requested
tool through the :class:`~tools.registry.ToolRegistry`, and returns a
standardised :class:`~tools.result.ToolResult`.
"""

from __future__ import annotations

from tools.invocation import ToolInvocation
from tools.registry import ToolRegistry
from tools.result import ToolResult


class ToolInvoker:
    """Stateless execution boundary for a single tool invocation.

    Responsibilities:
    * Accept a :class:`ToolInvocation`.
    * Resolve the tool by name via :class:`ToolRegistry`.
    * Execute the tool through its lifecycle (:meth:`~tools.base.Tool.run`).
    * Return the resulting :class:`ToolResult`.

    The invoker is deliberately narrow — it does **not** select tools,
    discover tools, retry failures, or talk to LLM providers.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        """Initialise with the *registry* used for tool resolution.

        Parameters
        ----------
        registry:
            The :class:`ToolRegistry` that holds available tool instances.
            The invoker holds a reference but does not own or mutate it.
        """
        self._registry = registry

    async def invoke(self, invocation: ToolInvocation) -> ToolResult:
        """Execute the requested *invocation* and return the result.

        Parameters
        ----------
        invocation:
            Describes which tool to call and what arguments to pass.

        Returns
        -------
        ToolResult
            The outcome of the tool execution.  Returns a failure result
            when the tool is unknown or when the tool itself raises an
            exception (already caught by the Template Method lifecycle).
        """
        tool = self._registry.get(invocation.tool_name)
        if tool is None:
            return ToolResult.fail(
                f"Unknown tool: '{invocation.tool_name}'"
            )
        return await tool.run(**invocation.arguments)
