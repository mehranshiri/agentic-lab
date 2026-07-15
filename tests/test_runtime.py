"""Unit tests for the AgentRuntime."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest

from agent.result import AgentResult
from agent.runtime import AgentRuntime
from llm.conversation_representation import ConversationRepresentation
from llm.provider_tool_call import ProviderToolCall
from llm.representations.base import SystemPromptAdapter, ToolSchemaAdapter
from llm.response import LLMResponse
from prompts.assembler import SystemPromptAssembler
from prompts.models import SystemPrompt
from tools.catalog import ToolCatalog
from tools.execution_context import ExecutionContext
from tools.metadata import ToolMetadata
from tools.registry import ToolRegistry


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class FakeConversationRepresentation(ConversationRepresentation):
    """Stub that converts a Conversation into simple role/content dicts."""

    def to_provider_messages(
        self,
        conversation: Any,
        *,
        system_prompt: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        if system_prompt is not None:
            result.append(system_prompt)
        for msg in conversation.messages:
            item: dict[str, Any] = {
                "role": msg.role.value,
                "content": msg.content or "",
            }
            if msg.tool_call_id:
                item["tool_call_id"] = msg.tool_call_id
            if msg.tool_calls:
                item["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.name,
                            "arguments": json.dumps(tc.arguments),
                        },
                    }
                    for tc in msg.tool_calls
                ]
            result.append(item)
        return result


class FakeToolSchemaAdapter(ToolSchemaAdapter):
    """Stub that passes metadata through unchanged."""

    def to_provider_format(self, metadata: ToolMetadata) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": metadata.parameters,
            },
        }


class FakeSystemPromptAdapter(SystemPromptAdapter):
    """Stub that returns a minimal system message dict."""

    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]:
        return {"role": "system", "content": prompt.text}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_provider() -> Mock:
    """Return a mock LLM provider."""
    return Mock()


@pytest.fixture
def empty_catalog() -> ToolCatalog:
    """Return a ToolCatalog with an empty registry (no tools)."""
    return ToolCatalog(ToolRegistry())


@pytest.fixture
def context() -> ExecutionContext:
    """Return a minimal ExecutionContext for testing."""
    return ExecutionContext(workspace_root=Path("/tmp/test-workspace"))


@pytest.fixture
def prompt_assembler() -> SystemPromptAssembler:
    """Return a SystemPromptAssembler instance."""
    return SystemPromptAssembler()


@pytest.fixture
def prompt_adapter() -> FakeSystemPromptAdapter:
    """Return a fake SystemPromptAdapter."""
    return FakeSystemPromptAdapter()


@pytest.fixture
def mock_bridge() -> AsyncMock:
    """Return a mock ToolCallBridge."""
    bridge = AsyncMock()
    bridge.process = AsyncMock()
    return bridge


@pytest.fixture
def runtime(
    mock_provider: Mock,
    empty_catalog: ToolCatalog,
    mock_bridge: AsyncMock,
    prompt_assembler: SystemPromptAssembler,
    prompt_adapter: FakeSystemPromptAdapter,
    context: ExecutionContext,
) -> AgentRuntime:
    """Return a fully wired AgentRuntime with mock dependencies."""
    return AgentRuntime(
        provider=mock_provider,
        conversation_representation=FakeConversationRepresentation(),
        tool_schema_adapter=FakeToolSchemaAdapter(),
        tool_catalog=empty_catalog,
        tool_call_bridge=mock_bridge,
        prompt_assembler=prompt_assembler,
        prompt_adapter=prompt_adapter,
        context=context,
    )


# ---------------------------------------------------------------------------
# AgentResult
# ---------------------------------------------------------------------------


class TestAgentResult:
    """Tests for :class:`AgentResult`."""

    def test_is_frozen(self) -> None:
        result = AgentResult(success=True, answer="ok")
        with pytest.raises(Exception):
            result.success = False  # type: ignore[misc]

    def test_success_result(self) -> None:
        result = AgentResult(success=True, answer="the answer")
        assert result.success is True
        assert result.answer == "the answer"

    def test_failure_result(self) -> None:
        result = AgentResult(success=False, answer="")
        assert result.success is False
        assert result.answer == ""

    def test_equality(self) -> None:
        a = AgentResult(success=True, answer="x")
        b = AgentResult(success=True, answer="x")
        assert a == b

    def test_inequality(self) -> None:
        a = AgentResult(success=True, answer="x")
        b = AgentResult(success=True, answer="y")
        assert a != b


# ---------------------------------------------------------------------------
# AgentRuntime
# ---------------------------------------------------------------------------


class TestAgentRuntime:
    """Tests for :class:`AgentRuntime`."""

    @pytest.mark.asyncio
    async def test_direct_answer_no_tools(
        self,
        runtime: AgentRuntime,
        mock_provider: Mock,
    ) -> None:
        """When the LLM returns text without tool calls, return it directly."""
        mock_provider.send_message = AsyncMock(
            return_value=LLMResponse(
                text="This is the answer.",
                model="test-model",
                finish_reason="stop",
                tool_calls=None,
            )
        )

        result = await runtime.run("What is 2+2?")

        assert isinstance(result, AgentResult)
        assert result.success is True
        assert result.answer == "This is the answer."

    @pytest.mark.asyncio
    async def test_single_tool_call_then_answer(
        self,
        runtime: AgentRuntime,
        mock_provider: Mock,
        mock_bridge: AsyncMock,
    ) -> None:
        """One tool call followed by a final text answer."""
        # First call: tool call
        # Second call: final answer
        mock_provider.send_message = AsyncMock(
            side_effect=[
                LLMResponse(
                    text="",
                    model="test-model",
                    finish_reason="tool_calls",
                    tool_calls=[
                        ProviderToolCall(
                            id="call_1",
                            name="read_file",
                            arguments={"path": "README.md"},
                        )
                    ],
                ),
                LLMResponse(
                    text="The project is about agentic AI.",
                    model="test-model",
                    finish_reason="stop",
                    tool_calls=None,
                ),
            ]
        )

        from tools.result import ToolResult
        from llm.tool_call_bridge import ToolCallResult
        from tools.invocation import ToolInvocation

        mock_bridge.process.return_value = [
            ToolCallResult(
                tool_call_id="call_1",
                invocation=ToolInvocation(
                    tool_name="read_file",
                    arguments={"path": "README.md"},
                ),
                result=ToolResult.ok("Tool output content"),
            )
        ]

        result = await runtime.run("Read the README and explain.")

        assert result.success is True
        assert result.answer == "The project is about agentic AI."
        assert mock_provider.send_message.call_count == 2
        assert mock_bridge.process.call_count == 1

    @pytest.mark.asyncio
    async def test_max_iterations_exceeded(
        self,
        mock_provider: Mock,
        empty_catalog: ToolCatalog,
        mock_bridge: AsyncMock,
        prompt_assembler: SystemPromptAssembler,
        prompt_adapter: FakeSystemPromptAdapter,
        context: ExecutionContext,
    ) -> None:
        """When the agent loops beyond max_iterations, return failure."""
        runtime = AgentRuntime(
            provider=mock_provider,
            conversation_representation=FakeConversationRepresentation(),
            tool_schema_adapter=FakeToolSchemaAdapter(),
            tool_catalog=empty_catalog,
            tool_call_bridge=mock_bridge,
            prompt_assembler=prompt_assembler,
            prompt_adapter=prompt_adapter,
            context=context,
            max_iterations=2,
        )

        # Always return tool calls so the loop never ends
        mock_provider.send_message = AsyncMock(
            return_value=LLMResponse(
                text="",
                model="test-model",
                finish_reason="tool_calls",
                tool_calls=[
                    ProviderToolCall(
                        id="call_x",
                        name="read_file",
                        arguments={"path": "x"},
                    )
                ],
            )
        )

        from tools.result import ToolResult
        from llm.tool_call_bridge import ToolCallResult
        from tools.invocation import ToolInvocation

        mock_bridge.process.return_value = [
            ToolCallResult(
                tool_call_id="call_x",
                invocation=ToolInvocation(
                    tool_name="read_file", arguments={"path": "x"}
                ),
                result=ToolResult.ok("content"),
            )
        ]

        result = await runtime.run("infinite loop")

        assert result.success is False
        assert "2 iterations" in result.answer

    @pytest.mark.asyncio
    async def test_conversation_grows_with_tool_calls(
        self,
        runtime: AgentRuntime,
        mock_provider: Mock,
        mock_bridge: AsyncMock,
    ) -> None:
        """Verify that tool results are appended to the conversation."""
        mock_provider.send_message = AsyncMock(
            side_effect=[
                LLMResponse(
                    text="",
                    model="test-model",
                    finish_reason="tool_calls",
                    tool_calls=[
                        ProviderToolCall(
                            id="call_1",
                            name="echo",
                            arguments={},
                        )
                    ],
                ),
                LLMResponse(
                    text="done",
                    model="test-model",
                    finish_reason="stop",
                    tool_calls=None,
                ),
            ]
        )

        from tools.result import ToolResult
        from llm.tool_call_bridge import ToolCallResult
        from tools.invocation import ToolInvocation

        mock_bridge.process.return_value = [
            ToolCallResult(
                tool_call_id="call_1",
                invocation=ToolInvocation(tool_name="echo", arguments={}),
                result=ToolResult.ok("echo output"),
            )
        ]

        result = await runtime.run("test")

        assert result.success is True
        # Verify the second call includes the full conversation
        # [system, user, assistant, tool] — 4 messages with system prompt
        second_call_messages = mock_provider.send_message.call_args_list[1][1][
            "messages"
        ]
        assert len(second_call_messages) == 4
        assert second_call_messages[0]["role"] == "system"
        assert second_call_messages[1]["role"] == "user"
        assert second_call_messages[2]["role"] == "assistant"
        assert second_call_messages[2]["tool_calls"] is not None
        assert second_call_messages[3]["role"] == "tool"
        assert second_call_messages[3]["tool_call_id"] == "call_1"

    @pytest.mark.asyncio
    async def test_tool_failure_appended_as_error(
        self,
        runtime: AgentRuntime,
        mock_provider: Mock,
        mock_bridge: AsyncMock,
    ) -> None:
        """Tool failures must be appended to the conversation as error messages."""
        mock_provider.send_message = AsyncMock(
            side_effect=[
                LLMResponse(
                    text="",
                    model="test-model",
                    finish_reason="tool_calls",
                    tool_calls=[
                        ProviderToolCall(
                            id="call_1",
                            name="bad_tool",
                            arguments={},
                        )
                    ],
                ),
                LLMResponse(
                    text="recovered",
                    model="test-model",
                    finish_reason="stop",
                    tool_calls=None,
                ),
            ]
        )

        from tools.result import ToolResult
        from llm.tool_call_bridge import ToolCallResult
        from tools.invocation import ToolInvocation

        mock_bridge.process.return_value = [
            ToolCallResult(
                tool_call_id="call_1",
                invocation=ToolInvocation(tool_name="bad_tool", arguments={}),
                result=ToolResult.fail("tool crashed"),
            )
        ]

        result = await runtime.run("test")

        assert result.success is True
        second_call_messages = mock_provider.send_message.call_args_list[1][1][
            "messages"
        ]
        # [system, user, assistant, tool] — tool is at index 3
        assert second_call_messages[3]["role"] == "tool"
        assert "Error: tool crashed" in second_call_messages[3]["content"]

    @pytest.mark.asyncio
    async def test_llm_returns_none_text(
        self,
        runtime: AgentRuntime,
        mock_provider: Mock,
    ) -> None:
        """When LLM returns empty text and no tool calls, answer is empty string."""
        mock_provider.send_message = AsyncMock(
            return_value=LLMResponse(
                text=None,  # type: ignore[arg-type]
                model="test-model",
                finish_reason="stop",
                tool_calls=None,
            )
        )

        result = await runtime.run("test")
        assert result.success is True
        assert result.answer == ""
