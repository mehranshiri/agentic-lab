"""Structured execution result returned by every tool.

Provides a consistent envelope so callers never have to inspect
per-tool internals — they always know whether the call succeeded,
what content was produced, and what error (if any) occurred.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ToolResult:
    """Immutable snapshot of a single tool execution.

    Attributes
    ----------
    success:
        ``True`` when the tool completed its work without error.
    content:
        The human-readable output produced by the tool (may be empty).
    error:
        An optional error message.  Populated only when `success` is
        ``False``.
    """

    success: bool
    content: str
    error: str | None = field(default=None)

    @classmethod
    def ok(cls, content: str) -> ToolResult:
        """Convenience constructor for successful results."""
        return cls(success=True, content=content)

    @classmethod
    def fail(cls, error: str) -> ToolResult:
        """Convenience constructor for failed results."""
        return cls(success=False, content="", error=error)