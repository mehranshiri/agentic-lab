"""Tool registry — discover, register, and retrieve tools by name.

The registry knows nothing about specific tool implementations.
It simply holds references to :class:`~tools.base.Tool` instances and
lets callers look them up by name (as declared by each tool's
:attr:`~tools.base.Tool.metadata`).
"""

from __future__ import annotations

from tools.base import Tool


class ToolRegistry:
    """In-memory registry of available tools.

    Tools can be registered individually via :meth:`register` or in
    bulk via :meth:`register_all`.  Lookups are done by name through
    :meth:`get`.

    The registry remains decoupled from any concrete tool — it only
    depends on the :class:`~tools.base.Tool` abstraction.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, tool: Tool) -> None:
        """Register a single *tool*.

        The tool's name is taken from ``tool.metadata.name``.  If a
        tool with the same name already exists it is silently
        overwritten.
        """
        self._tools[tool.metadata.name] = tool

    def register_all(self, tools: list[Tool]) -> None:
        """Register several *tools* at once."""
        for tool in tools:
            self.register(tool)

    # ------------------------------------------------------------------
    # Lookup
    # ------------------------------------------------------------------

    def get(self, name: str) -> Tool | None:
        """Return the tool registered under *name*, or ``None``.

        Parameters
        ----------
        name:
            The exact tool name (e.g. ``"read_file"``).

        Returns
        -------
        Tool | None
            The registered tool instance, or ``None`` when no tool
            matches *name*.
        """
        return self._tools.get(name)

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def list_names(self) -> list[str]:
        """Return the names of all registered tools."""
        return list(self._tools.keys())

    def list_tools(self) -> list[Tool]:
        """Return all registered tool instances."""
        return list(self._tools.values())

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools