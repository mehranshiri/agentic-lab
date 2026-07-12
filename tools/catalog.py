"""Tool catalog — discovery layer for available tool capabilities.

The catalog is the bridge between the Tool Registry and future LLM
integrations.  It exposes descriptive information about registered
tools without executing them or containing any provider-specific logic.
"""

from __future__ import annotations

from tools.metadata import ToolMetadata
from tools.registry import ToolRegistry


class ToolCatalog:
    """Stateless discovery layer that exposes available tool descriptors.

    Responsibilities:
    * Discover registered tools through a :class:`ToolRegistry`.
    * Return immutable :class:`ToolMetadata` snapshots.
    * Remain independent of LLM providers and execution logic.

    The catalog **never** caches tool information — it always queries
    the registry so that callers see the live set of tools.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        """Initialise with a *registry* that serves as the source of truth.

        Parameters
        ----------
        registry:
            The tool registry to discover tools from.  The catalog holds
            a reference to it but does not own or modify it.
        """
        self._registry = registry

    def list_tools(self) -> list[ToolMetadata]:
        """Return metadata for every tool currently registered.

        Each call queries the registry directly — no internal cache.

        Returns
        -------
        list[ToolMetadata]
            Immutable descriptors for all available tools, ordered by
            registry insertion order.
        """
        return [tool.metadata for tool in self._registry.list_tools()]
