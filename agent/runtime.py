"""AgentRuntime — executes the full agent reasoning loop.

The runtime is the only public entry point for executing an agent
interaction.  It orchestrates conversation management, LLM communication,
tool execution, and the reasoning loop behind a single :meth:`run` method.
"""

from __future__ import annotations

import logging
from typing import Any

from agent.result import AgentResult
from conversation.models import Conversation, ToolCall
from llm.base import LlmProvider
from llm.conversation_representation import ConversationRepresentation
from llm.provider_tool_call import ProviderToolCall
from llm.representations.base import ToolSchemaAdapter
from llm.tool_call_bridge import ToolCallBridge
from tools.catalog import ToolCatalog

logger = logging.getLogger(__name__)


class AgentRuntime:
    """Execute one complete agent interaction.

    Responsibilities:
    * Receive a user's prompt.
    * Create the initial Conversation.
    * Convert the Conversation into provider-specific messages.
    * Send messages to the configured LLM provider.
    * Detect tool requests.
    * Delegate tool execution to :class:`ToolCallBridge`.
    * Append tool results into a new Conversation.
    * Continue the reasoning loop until no further tool calls are requested.
    * Return an :class:`AgentResult`.

    The runtime owns the reasoning loop and is the only public entry
    point for executing an agent interaction.  It does **not** plan,
    persist, retry, or manage memory.
    """

    def __init__(
        self,
        provider: LlmProvider,
        conversation_representation: ConversationRepresentation,
        tool_schema_adapter: ToolSchemaAdapter,
        tool_catalog: ToolCatalog,
        tool_call_bridge: ToolCallBridge,
        *,
        max_iterations: int = 10,
    ) -> None:
        """Initialise the runtime with all required dependencies.

        Parameters
        ----------
        provider:
            The LLM provider used for all chat completions.
        conversation_representation:
            Translates domain Conversations into provider-compatible messages.
        tool_schema_adapter:
            Translates ToolMetadata into provider tool definitions.
        tool_catalog:
            Discovers available tools and their metadata.
        tool_call_bridge:
            Executes provider tool calls through the Tool Framework.
        max_iterations:
            Maximum number of reasoning-loop iterations before raising
            an error.  Protects against infinite loops.  Defaults to 10.
        """
        self._provider = provider
        self._conversation_representation = conversation_representation
        self._tool_schema_adapter = tool_schema_adapter
        self._tool_catalog = tool_catalog
        self._tool_call_bridge = tool_call_bridge
        self._max_iterations = max_iterations

    async def run(self, prompt: str) -> AgentResult:
        """Execute the full agent interaction for *prompt*.

        Parameters
        ----------
        prompt:
            The user's natural-language prompt.

        Returns
        -------
        AgentResult
            The outcome of the completed interaction, including the
            final answer and success status.
        """
        # ── 1. Create initial Conversation with the user prompt ─────────
        conversation = Conversation().add_user_message(prompt)

        # ── 2. Discover available tools (once, before the loop) ─────────
        tool_metadata_list = self._tool_catalog.list_tools()
        provider_tools = [
            self._tool_schema_adapter.to_provider_format(meta)
            for meta in tool_metadata_list
        ]

        # ── 3. Reasoning loop ───────────────────────────────────────────
        for iteration in range(1, self._max_iterations + 1):
            logger.debug("Reasoning iteration %d", iteration)

            # 3a. Convert Conversation to provider messages
            provider_messages = (
                self._conversation_representation.to_provider_messages(
                    conversation
                )
            )

            # 3b. Send to LLM
            response = await self._provider.send_message(
                messages=provider_messages,
                tools=provider_tools if provider_tools else None,
            )

            # 3c. No tool calls → final answer
            if not response.tool_calls:
                return AgentResult(
                    success=True,
                    answer=response.text or "",
                )

            # 3d. Tool calls received — record assistant message
            domain_tool_calls = self._to_domain_tool_calls(
                response.tool_calls
            )
            conversation = conversation.add_assistant_message(
                content=response.text or None,
                tool_calls=domain_tool_calls,
            )

            # 3e. Execute tools via ToolCallBridge
            tool_call_results = await self._tool_call_bridge.process(
                response.tool_calls
            )

            # 3f. Append tool results into the Conversation
            for tcr in tool_call_results:
                content = (
                    tcr.result.content
                    if tcr.result.success
                    else f"Error: {tcr.result.error or 'Unknown error'}"
                )
                # Use the provider tool call id that matches this result
                provider_tc = next(
                    (
                        tc
                        for tc in response.tool_calls
                        if tc.name == tcr.invocation.tool_name
                    ),
                    None,
                )
                tool_call_id = (
                    provider_tc.id if provider_tc else tcr.invocation.tool_name
                )
                conversation = conversation.add_tool_message(
                    tool_call_id=tool_call_id,
                    content=content,
                )

            # 3g. Continue loop with updated conversation

        # ── 4. Max iterations exceeded ──────────────────────────────────
        logger.warning(
            "AgentRuntime exceeded max_iterations (%d) without reaching "
            "a final answer. Returning failure result.",
            self._max_iterations,
        )
        return AgentResult(
            success=False,
            answer=(
                f"Agent stopped after {self._max_iterations} iterations "
                "without reaching a final answer."
            ),
        )

    @staticmethod
    def _to_domain_tool_calls(
        provider_tool_calls: list[ProviderToolCall],
    ) -> list[ToolCall]:
        """Convert provider tool calls into domain ToolCall objects.

        Parameters
        ----------
        provider_tool_calls:
            The provider-independent tool calls from the LLM response.

        Returns
        -------
        list[ToolCall]
            Domain tool calls suitable for inclusion in a Conversation.
        """
        return [
            ToolCall(
                id=tc.id,
                name=tc.name,
                arguments=tc.arguments,
            )
            for tc in provider_tool_calls
        ]