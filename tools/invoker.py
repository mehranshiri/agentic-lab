"""Tool invoker — execution boundary for single-tool invocation.

The invoker receives a :class:`ToolInvocation`, resolves the requested
tool through the :class:`~tools.registry.ToolRegistry`, supplies the
execution context, and returns a standardised :class:`~tools.result.ToolResult`.
"""

from __future__ import annotations

from tools.execution_context import ExecutionContext
from tools.invocation import ToolInvocation
from tools.registry import ToolRegistry
from tools.result import ToolResult


class ToolInvoker:
    """Stateless execution boundary for a single tool invocation.

    Responsibilities:
    * Accept a :class:`ToolInvocation`.
    * Resolve the tool by name via :class:`ToolRegistry`.
    * Supply the :class:`ExecutionContext` so tools can resolve paths,
      locate resources, or access shared settings.
    * Execute the tool through its lifecycle (:meth:`~tools.base.Tool.run`).
    * Return the resulting :class:`ToolResult`.

    The invoker is deliberately narrow — it does **not** select tools,
    discover tools, retry failures, or talk to LLM providers.
    """

    def __init__(
        self, registry: ToolRegistry, context: ExecutionContext | None = None
    ) -> None:
        """Initialise with the *registry* and optional *context*.

        Parameters
        ----------
        registry:
            The :class:`ToolRegistry` that holds available tool instances.
            The invoker holds a reference but does not own or mutate it.
        context:
            Immutable :class:`ExecutionContext` supplied to every tool
            invocation so that tools can resolve paths and access runtime
            settings.  When ``None`` (backwards-compatible), tools that
            depend on the context will raise an error.
        """
        self._registry = registry
        self._context = context

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
            return ToolResult.fail(f"Unknown tool: '{invocation.tool_name}'")
        kwargs = dict(invocation.arguments)
        if self._context is not None:
            kwargs["_context"] = self._context
        return await tool.run(**kwargs)
