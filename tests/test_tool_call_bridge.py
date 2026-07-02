"""Unit tests for the ToolCallBridge."""

from __future__ import annotations

import pytest

from llm.provider_tool_call import ProviderToolCall
from llm.tool_call_bridge import ToolCallBridge, ToolCallResult
from tools.base import Tool
from tools.invocation import ToolInvocation
from tools.invoker import ToolInvoker
from tools.metadata import ToolMetadata
from tools.registry import ToolRegistry
from tools.result import ToolResult


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


class _EchoTool(Tool):
    """A toy tool that echoes back its arguments for testing."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(name="echo", description="Echoes arguments.")

    async def execute(self, **kwargs: object) -> ToolResult:
        return ToolResult.ok(str(kwargs))


class _FailingTool(Tool):
    """A toy tool that always raises during execution."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(name="failing", description="Always fails.")

    async def execute(self, **kwargs: object) -> ToolResult:
        raise RuntimeError("deliberate failure")


@pytest.fixture
def registry() -> ToolRegistry:
    """A registry pre-populated with test tools."""
    reg = ToolRegistry()
    reg.register(_EchoTool())
    reg.register(_FailingTool())
    return reg


@pytest.fixture
def invoker(registry: ToolRegistry) -> ToolInvoker:
    return ToolInvoker(registry)


@pytest.fixture
def bridge(invoker: ToolInvoker) -> ToolCallBridge:
    return ToolCallBridge(invoker)


# ---------------------------------------------------------------------------
# ToolCallResult
# ---------------------------------------------------------------------------


class TestToolCallResult:
    """Tests for the :class:`ToolCallResult` value object."""

    def test_is_frozen(self) -> None:
        """``ToolCallResult`` must be immutable."""
        inv = ToolInvocation(tool_name="echo", arguments={})
        res = ToolResult.ok("ok")
        tcr = ToolCallResult(invocation=inv, result=res)
        with pytest.raises(Exception):
            tcr.result = ToolResult.fail("nope")  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two results with identical fields must be equal."""
        inv = ToolInvocation(tool_name="echo", arguments={})
        ok = ToolResult.ok("ok")
        a = ToolCallResult(invocation=inv, result=ok)
        b = ToolCallResult(invocation=inv, result=ok)
        assert a == b

    def test_different_results_not_equal(self) -> None:
        """Results with different tool outcomes must not be equal."""
        inv = ToolInvocation(tool_name="echo", arguments={})
        a = ToolCallResult(invocation=inv, result=ToolResult.ok("ok"))
        b = ToolCallResult(invocation=inv, result=ToolResult.fail("fail"))
        assert a != b


# ---------------------------------------------------------------------------
# ToolCallBridge
# ---------------------------------------------------------------------------


class TestToolCallBridge:
    """Tests for the :class:`ToolCallBridge`."""

    @pytest.mark.asyncio
    async def test_processes_single_tool_call(self, bridge: ToolCallBridge) -> None:
        """A single provider tool call should produce one successful result."""
        tool_calls = [
            ProviderToolCall(
                id="call_1",
                name="echo",
                arguments={"message": "hello"},
            )
        ]

        results = await bridge.process(tool_calls)

        assert len(results) == 1
        assert results[0].result.success
        assert "message" in results[0].result.content

    @pytest.mark.asyncio
    async def test_processes_multiple_tool_calls_sequentially(
        self, bridge: ToolCallBridge
    ) -> None:
        """Multiple tool calls should be processed in order."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="echo", arguments={"n": 1}),
            ProviderToolCall(id="call_2", name="echo", arguments={"n": 2}),
            ProviderToolCall(id="call_3", name="echo", arguments={"n": 3}),
        ]

        results = await bridge.process(tool_calls)

        assert len(results) == 3
        assert all(r.result.success for r in results)

    @pytest.mark.asyncio
    async def test_preserves_invocation_result_pairing(
        self, bridge: ToolCallBridge
    ) -> None:
        """Each ToolCallResult should correctly pair invocation and result."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="echo", arguments={"key": "value"}),
        ]

        results = await bridge.process(tool_calls)

        assert results[0].invocation.tool_name == "echo"
        assert results[0].invocation.arguments == {"key": "value"}
        assert results[0].result.success

    @pytest.mark.asyncio
    async def test_handles_unknown_tool(self, bridge: ToolCallBridge) -> None:
        """A tool call for an unknown tool should produce a failure result."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="ghost_tool", arguments={}),
        ]

        results = await bridge.process(tool_calls)

        assert len(results) == 1
        assert not results[0].result.success
        assert "Unknown tool" in (results[0].result.error or "")

    @pytest.mark.asyncio
    async def test_handles_failing_tool(self, bridge: ToolCallBridge) -> None:
        """A tool call to a failing tool should still produce a ToolCallResult."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="failing", arguments={}),
        ]

        results = await bridge.process(tool_calls)

        assert len(results) == 1
        assert not results[0].result.success
        assert "deliberate failure" in (results[0].result.error or "")

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_no_tool_calls(
        self, bridge: ToolCallBridge
    ) -> None:
        """Processing an empty list should return an empty list."""
        results = await bridge.process([])
        assert results == []

    @pytest.mark.asyncio
    async def test_bridge_is_stateless(self, bridge: ToolCallBridge) -> None:
        """Repeated calls with the same input should produce consistent results."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="echo", arguments={"x": 1}),
        ]

        first = await bridge.process(tool_calls)
        second = await bridge.process(tool_calls)

        assert len(first) == len(second)
        assert first[0] == second[0]

    @pytest.mark.asyncio
    async def test_tool_call_with_empty_arguments(
        self, bridge: ToolCallBridge
    ) -> None:
        """A tool call with empty arguments dict should work."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="echo", arguments={}),
        ]

        results = await bridge.process(tool_calls)

        assert len(results) == 1
        assert results[0].result.success

    @pytest.mark.asyncio
    async def test_mixed_success_and_failure(
        self, bridge: ToolCallBridge
    ) -> None:
        """A mix of successful and failing tool calls should all be recorded."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="echo", arguments={"ok": True}),
            ProviderToolCall(id="call_2", name="failing", arguments={}),
            ProviderToolCall(id="call_3", name="echo", arguments={"ok": True}),
        ]

        results = await bridge.process(tool_calls)

        assert len(results) == 3
        assert results[0].result.success
        assert not results[1].result.success
        assert results[2].result.success

    @pytest.mark.asyncio
    async def test_result_type_is_tool_call_result(
        self, bridge: ToolCallBridge
    ) -> None:
        """Every element in the result list must be a ToolCallResult."""
        tool_calls = [
            ProviderToolCall(id="call_1", name="echo", arguments={}),
        ]

        results = await bridge.process(tool_calls)

        for r in results:
            assert isinstance(r, ToolCallResult)