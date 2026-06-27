"""Abstract base class for all tools (Template Method pattern).

Every concrete tool must subclass :class:`Tool` and implement
:meth:`execute`.  The base class provides a public :meth:`run` method
that orchestrates the lifecycle (validate → execute) and returns a
structured :class:`~tools.result.ToolResult`.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from tools.metadata import ToolMetadata
from tools.result import ToolResult


class Tool(ABC):
    """Abstract template for a tool.

    Responsibilities:
    * Declare metadata via :attr:`metadata`.
    * Expose a single entry point — :meth:`run` — that calls
      :meth:`validate` and then :meth:`execute`.
    * Require subclasses to implement only :meth:`execute`.

    Life-cycle hooks (all called by :meth:`run`):
    1. :meth:`validate`   – pre-execution guard (optional override).
    2. :meth:`execute`    – the actual work (mandatory).
    """

    # ------------------------------------------------------------------
    # Subclass interface
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata:
        """Descriptive information about this tool (name, description)."""
        ...

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Perform the tool's core business logic.

        Subclasses **must** override this method and return a
        :class:`~tools.result.ToolResult`.
        """
        ...

    # ------------------------------------------------------------------
    # Optional hooks — override when needed
    # ------------------------------------------------------------------

    async def validate(self, **kwargs: Any) -> None:
        """Pre-execution hook.

        Override to perform input validation / pre-conditions checks.
        The default implementation is a no-op (always succeeds).

        Should raise an exception (e.g. :exc:`ValueError`) to signal a
        validation failure so that :meth:`run` can catch it and return
        a failed :class:`~tools.result.ToolResult`.
        """
        return

    # ------------------------------------------------------------------
    # Public API — the Template Method
    # ------------------------------------------------------------------

    async def run(self, **kwargs: Any) -> ToolResult:
        """Execute the tool through its lifecycle and return a result.

        This is the **only** method external code should call.  It
        follows the Template Method pattern:

        1. Call :meth:`validate`.
        2. Call :meth:`execute`.
        3. Return the :class:`~tools.result.ToolResult`.

        Any exception raised during validation or execution is caught
        and wrapped in a failed result — the caller never sees a raw
        exception.
        """
        try:
            await self.validate(**kwargs)
            return await self.execute(**kwargs)
        except Exception as exc:
            return ToolResult.fail(str(exc))