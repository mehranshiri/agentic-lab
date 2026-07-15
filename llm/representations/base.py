"""Abstract base classes for provider-specific adapters.

Defines two strategy interfaces:

* :class:`ToolSchemaAdapter` — translates :class:`~tools.metadata.ToolMetadata`
  into provider-specific tool definitions.
* :class:`SystemPromptAdapter` — translates :class:`~prompts.models.SystemPrompt`
  into a provider-specific message dict.

Both follow the Dependency Inversion Principle: the Tool and Prompt domains
never know about concrete adapters.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from prompts.models import SystemPrompt
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


class SystemPromptAdapter(ABC):
    """Strategy interface for translating a SystemPrompt into a provider dict.

    Responsibilities:
    * Accept a provider-independent :class:`~prompts.models.SystemPrompt`.
    * Translate it into a provider-specific message dict ready for
      inclusion in the message list sent to the LLM.
    * Remain stateless — all state is carried by the input prompt.

    Different providers handle system prompts differently:

    * OpenAI / DeepSeek — ``{"role": "system", "content": "..."}``
      as the first message in the messages list.
    * Anthropic — a separate ``system`` parameter, not in messages.
    * Some providers — no system prompt support (adapter returns
      ``None`` or raises).

    This base class depends on the Prompts domain model
    (:class:`~prompts.models.SystemPrompt`) but the Prompts domain
    never knows about any concrete adapter.
    """

    @abstractmethod
    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]:
        """Translate *prompt* into a provider-specific message dict.

        Parameters
        ----------
        prompt:
            The assembled, provider-independent system prompt.

        Returns
        -------
        dict[str, Any]
            A provider-ready message dict (e.g.
            ``{"role": "system", "content": "..."}``).
        """
        ...
