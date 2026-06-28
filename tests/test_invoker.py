"""Unit tests for the tool invocation layer."""

from __future__ import annotations

import pytest

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
    """A registry pre-populated with two test tools."""
    reg = ToolRegistry()
    reg.register(_EchoTool())
    reg.register(_FailingTool())
    return reg


@pytest.fixture
def invoker(registry: ToolRegistry) -> ToolInvoker:
    return ToolInvoker(registry)


# ---------------------------------------------------------------------------
# ToolInvocation
# ---------------------------------------------------------------------------

class TestToolInvocation:
    """Tests for the :class:`ToolInvocation` value object."""

    def test_is_frozen(self) -> None:
        """``ToolInvocation`` must be immutable."""
        inv = ToolInvocation(tool_name="x", arguments={"a": 1})
        with pytest.raises(Exception):
            inv.tool_name = "y"  # type: ignore[misc]

    def test_equality(self) -> None:
        """Two invocations with identical fields must be equal."""
        a = ToolInvocation(tool_name="t", arguments={"k": "v"})
        b = ToolInvocation(tool_name="t", arguments={"k": "v"})
        assert a == b

    def test_different_tool_name_not_equal(self) -> None:
        """Invocations with different tool names must not be equal."""
        a = ToolInvocation(tool_name="a", arguments={})
        b = ToolInvocation(tool_name="b", arguments={})
        assert a != b

    def test_different_arguments_not_equal(self) -> None:
        """Invocations with different arguments must not be equal."""
        a = ToolInvocation(tool_name="t", arguments={"x": 1})
        b = ToolInvocation(tool_name="t", arguments={"x": 2})
        assert a != b

    def test_empty_arguments_allowed(self) -> None:
        """An invocation with no arguments must be valid."""
        inv = ToolInvocation(tool_name="t", arguments={})
        assert inv.arguments == {}


# ---------------------------------------------------------------------------
# ToolInvoker
# ---------------------------------------------------------------------------

class TestToolInvoker:
    """Tests for the :class:`ToolInvoker`."""

    @pytest.mark.asyncio
    async def test_invoke_known_tool_succeeds(
        self, invoker: ToolInvoker
    ) -> None:
        """Invoking a registered tool must return a successful result."""
        invocation = ToolInvocation(
            tool_name="echo", arguments={"hello": "world"}
        )
        result = await invoker.invoke(invocation)
        assert result.success

    @pytest.mark.asyncio
    async def test_invoke_known_tool_passes_arguments(
        self, invoker: ToolInvoker
    ) -> None:
        """Arguments from the invocation must reach the tool."""
        invocation = ToolInvocation(
            tool_name="echo", arguments={"key": "value"}
        )
        result = await invoker.invoke(invocation)
        assert "key" in result.content

    @pytest.mark.asyncio
    async def test_invoke_unknown_tool_returns_failure(
        self, invoker: ToolInvoker
    ) -> None:
        """Invoking an unregistered tool must return a failure result."""
        invocation = ToolInvocation(
            tool_name="ghost_tool", arguments={}
        )
        result = await invoker.invoke(invocation)
        assert not result.success
        assert "Unknown tool" in (result.error or "")

    @pytest.mark.asyncio
    async def test_invoke_failing_tool_returns_failure(
        self, invoker: ToolInvoker
    ) -> None:
        """When a tool raises, the invoker must still return a ``ToolResult``."""
        invocation = ToolInvocation(
            tool_name="failing", arguments={}
        )
        result = await invoker.invoke(invocation)
        assert not result.success
        assert "deliberate failure" in (result.error or "")

    @pytest.mark.asyncio
    async def test_invoke_always_returns_tool_result(
        self, invoker: ToolInvoker
    ) -> None:
        """Every invocation, regardless of outcome, must return a ``ToolResult``."""
        for name in ("echo", "failing", "ghost_tool"):
            inv = ToolInvocation(tool_name=name, arguments={})
            result = await invoker.invoke(inv)
            assert isinstance(result, ToolResult)

    @pytest.mark.asyncio
    async def test_invoker_is_stateless(
        self, invoker: ToolInvoker
    ) -> None:
        """Repeated invocations must produce consistent results."""
        invocation = ToolInvocation(
            tool_name="echo", arguments={"count": 1}
        )
        first = await invoker.invoke(invocation)
        second = await invoker.invoke(invocation)
        assert first == second
