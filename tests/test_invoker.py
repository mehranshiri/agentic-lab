"""Unit tests for the tool invocation layer."""

from __future__ import annotations

from pathlib import Path

import pytest

from tools.base import Tool
from tools.execution_context import ExecutionContext
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


class _ContextConsumerTool(Tool):
    """A toy tool that records whether it received a context."""

    @property
    def metadata(self) -> ToolMetadata:
        return ToolMetadata(name="ctx_consumer", description="Records context.")

    async def execute(self, **kwargs: object) -> ToolResult:
        ctx = kwargs.get("_context")
        if ctx is not None and isinstance(ctx, ExecutionContext):
            return ToolResult.ok(f"context received: workspace={ctx.workspace_root}")
        return ToolResult.ok("no context")


@pytest.fixture
def registry() -> ToolRegistry:
    """A registry pre-populated with two test tools."""
    reg = ToolRegistry()
    reg.register(_EchoTool())
    reg.register(_FailingTool())
    return reg


@pytest.fixture
def workspace_root(tmp_path: Path) -> Path:
    return tmp_path.resolve()


@pytest.fixture
def context(workspace_root: Path) -> ExecutionContext:
    return ExecutionContext(workspace_root=workspace_root)


@pytest.fixture
def invoker(registry: ToolRegistry) -> ToolInvoker:
    return ToolInvoker(registry)


@pytest.fixture
def invoker_with_context(
    registry: ToolRegistry, context: ExecutionContext
) -> ToolInvoker:
    return ToolInvoker(registry, context=context)


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
    async def test_invoke_known_tool_succeeds(self, invoker: ToolInvoker) -> None:
        """Invoking a registered tool must return a successful result."""
        invocation = ToolInvocation(tool_name="echo", arguments={"hello": "world"})
        result = await invoker.invoke(invocation)
        assert result.success

    @pytest.mark.asyncio
    async def test_invoke_known_tool_passes_arguments(
        self, invoker: ToolInvoker
    ) -> None:
        """Arguments from the invocation must reach the tool."""
        invocation = ToolInvocation(tool_name="echo", arguments={"key": "value"})
        result = await invoker.invoke(invocation)
        assert "key" in result.content

    @pytest.mark.asyncio
    async def test_invoke_unknown_tool_returns_failure(
        self, invoker: ToolInvoker
    ) -> None:
        """Invoking an unregistered tool must return a failure result."""
        invocation = ToolInvocation(tool_name="ghost_tool", arguments={})
        result = await invoker.invoke(invocation)
        assert not result.success
        assert "Unknown tool" in (result.error or "")

    @pytest.mark.asyncio
    async def test_invoke_failing_tool_returns_failure(
        self, invoker: ToolInvoker
    ) -> None:
        """When a tool raises, the invoker must still return a ``ToolResult``."""
        invocation = ToolInvocation(tool_name="failing", arguments={})
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
    async def test_invoker_is_stateless(self, invoker: ToolInvoker) -> None:
        """Repeated invocations must produce consistent results."""
        invocation = ToolInvocation(tool_name="echo", arguments={"count": 1})
        first = await invoker.invoke(invocation)
        second = await invoker.invoke(invocation)
        assert first == second


# ---------------------------------------------------------------------------
# ExecutionContext integration
# ---------------------------------------------------------------------------


class TestExecutionContext:
    """Tests for the :class:`ExecutionContext` value object."""

    def test_is_frozen(self, workspace_root: Path) -> None:
        """``ExecutionContext`` must be immutable."""
        ctx = ExecutionContext(workspace_root=workspace_root)
        with pytest.raises(Exception):
            ctx.workspace_root = Path("/tmp")  # type: ignore[misc]

    def test_rejects_relative_path(self) -> None:
        """``workspace_root`` must be absolute."""
        with pytest.raises(ValueError, match="must be absolute"):
            ExecutionContext(workspace_root=Path("relative/path"))


class TestToolInvokerWithContext:
    """Tests that the invoker supplies ``ExecutionContext`` to tools."""

    @pytest.mark.asyncio
    async def test_context_passed_to_tool(
        self, registry: ToolRegistry, context: ExecutionContext
    ) -> None:
        """When a context is provided, it must reach the tool."""
        registry.register(_ContextConsumerTool())
        invoker = ToolInvoker(registry, context=context)
        invocation = ToolInvocation(tool_name="ctx_consumer", arguments={})
        result = await invoker.invoke(invocation)
        assert result.success
        assert str(context.workspace_root) in result.content

    @pytest.mark.asyncio
    async def test_no_context_when_none(self, registry: ToolRegistry) -> None:
        """When no context is provided, tools get ``_context=None``."""
        registry.register(_ContextConsumerTool())
        invoker = ToolInvoker(registry)
        invocation = ToolInvocation(tool_name="ctx_consumer", arguments={})
        result = await invoker.invoke(invocation)
        assert result.success
        assert result.content == "no context"

    @pytest.mark.asyncio
    async def test_invoker_context_takes_precedence(
        self, registry: ToolRegistry, context: ExecutionContext
    ) -> None:
        """The ``_context`` injected by the invoker replaces any user-supplied ``_context``."""
        registry.register(_ContextConsumerTool())
        invoker = ToolInvoker(registry, context=context)
        invocation = ToolInvocation(
            tool_name="ctx_consumer", arguments={"_context": "explicit"}
        )
        result = await invoker.invoke(invocation)
        assert result.success
        # The invoker's real ExecutionContext must be what reaches the tool,
        # not the user-supplied string.
        assert str(context.workspace_root) in result.content
