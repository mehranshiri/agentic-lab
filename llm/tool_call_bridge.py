"""ToolCallBridge — translates provider tool calls into domain invocations.

The bridge is the architectural boundary between the LLM module and the
Tool Framework.  It accepts provider-independent :class:`ProviderToolCall`
objects, converts each one into a :class:`~tools.invocation.ToolInvocation`,
and delegates execution to the existing :class:`~tools.invoker.ToolInvoker`.
"""

from __future__ import annotations

from dataclasses import dataclass

from llm.provider_tool_call import ProviderToolCall
from tools.invocation import ToolInvocation
from tools.invoker import ToolInvoker
from tools.result import ToolResult


@dataclass(frozen=True)
class ToolCallResult:
    """Pair a provider tool call with the result it produced.

    Attributes
    ----------
    tool_call_id:
        The provider-assigned identifier of the tool call that produced
        this result.  Carried through so that consumers (e.g. the runtime)
        can correlate results back to specific calls without re-matching
        by name.
    invocation:
        The :class:`ToolInvocation` that was executed.
    result:
        The :class:`~tools.result.ToolResult` produced by the invocation.
    """

    # DESIGN: tool_call_id is a provider-derived identifier that lives in the
    # LLM module alongside ToolCallResult.  It does NOT leak into tools/ —
    # ToolInvocation and ToolResult remain provider-agnostic.  The bridge is
    # the last component to see both the provider call ID and the tool
    # execution together; carrying the ID through avoids fragile reverse
    # lookups by every consumer of process().

    tool_call_id: str
    invocation: ToolInvocation
    result: ToolResult


class ToolCallBridge:
    """Stateless boundary that translates provider tool calls into tool executions.

    Responsibilities:
    * Accept a list of :class:`ProviderToolCall` objects.
    * Convert each to a :class:`ToolInvocation`.
    * Invoke through the :class:`ToolInvoker`.
    * Collect and return :class:`ToolCallResult` objects.

    The bridge must **not**:
    * Parse provider-specific payloads (that is the provider's job).
    * Execute tools directly.
    * Retry, plan, or maintain state.
    """

    def __init__(self, invoker: ToolInvoker) -> None:
        """Initialise with the *invoker* used for tool execution.

        Parameters
        ----------
        invoker:
            The :class:`ToolInvoker` that resolves and executes tools.
            The bridge holds a reference but does not own or mutate it.
        """
        self._invoker = invoker

    async def process(self, tool_calls: list[ProviderToolCall]) -> list[ToolCallResult]:
        """Translate and execute each provider tool call sequentially.

        Parameters
        ----------
        tool_calls:
            The list of provider tool calls to process.

        Returns
        -------
        list[ToolCallResult]
            One result per tool call, preserving the order of *tool_calls*.
        """
        results: list[ToolCallResult] = []

        for tc in tool_calls:
            invocation = ToolInvocation(
                tool_name=tc.name,
                arguments=tc.arguments,
            )
            tool_result = await self._invoker.invoke(invocation)
            results.append(
                ToolCallResult(
                    tool_call_id=tc.id,
                    invocation=invocation,
                    result=tool_result,
                )
            )

        return results
