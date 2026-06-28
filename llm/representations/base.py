"""Abstract base class for provider-specific tool-schema adapters.

Every concrete adapter must subclass :class:`ToolSchemaAdapter` and
implement :meth:`to_provider_format`.  This keeps provider-specific
schemas isolated inside the LLM module while the Tool Framework remains
independent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from tools.metadata import ToolMetadata


class ToolSchemaAdapter(ABC):
    """Strategy interface for translating tool metadata into a provider schema.

    Responsibilities:
    * Accept a :class:`~tools.metadata.ToolMetadata` value object.
    * Translate it into a provider-specific dictionary ready for inclusion
      in an LLM request.
    * Remain stateless — all state is carried by the input metadata.

    This base class depends on the Tool Framework's domain model
    (:class:`ToolMetadata`) but the Tool Framework never needs to know
    about any concrete adapter.  This follows the Dependency Inversion
    Principle.
    """

    @abstractmethod
    def to_provider_format(self, metadata: ToolMetadata) -> dict[str, Any]:
        """Translate *metadata* into a provider-specific tool definition.

        Parameters
        ----------
        metadata:
            The descriptive tool metadata produced by the Tool Catalog.

        Returns
        -------
        dict[str, Any]
            A provider-ready tool definition dict (e.g. DeepSeek's
            ``{"type": "function", "function": {...}}`` schema).
        """
        ...
