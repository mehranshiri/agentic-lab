"""DeepSeek-specific adapters for tool schemas and system prompts.

Translates domain objects (:class:`~tools.metadata.ToolMetadata`,
:class:`~prompts.models.SystemPrompt`) into the formats expected by the
DeepSeek Chat Completions API (OpenAI-compatible).
"""

from __future__ import annotations

from typing import Any

from llm.representations.base import SystemPromptAdapter, ToolSchemaAdapter
from prompts.models import SystemPrompt
from tools.metadata import ToolMetadata


class DeepSeekToolSchemaAdapter(ToolSchemaAdapter):
    """Translate :class:`ToolMetadata` into DeepSeek-compatible tool definitions.

    DeepSeek's Chat Completions API follows the OpenAI function-calling
    convention where each tool is represented as::

        {
            "type": "function",
            "function": {
                "name": "<tool_name>",
                "description": "<tool_description>",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        }

    """

    def to_provider_format(self, metadata: ToolMetadata) -> dict[str, Any]:
        """Translate *metadata* into a DeepSeek-compatible tool definition.

        Parameters
        ----------
        metadata:
            Tool descriptor produced by the :class:`~tools.catalog.ToolCatalog`.

        Returns
        -------
        dict[str, Any]
            A dict matching DeepSeek's expected ``type/function`` schema.
        """
        return {
            "type": "function",
            "function": {
                "name": metadata.name,
                "description": metadata.description,
                "parameters": metadata.parameters,
            },
        }


class DeepSeekSystemPromptAdapter(SystemPromptAdapter):
    """Translate :class:`SystemPrompt` into a DeepSeek-compatible message dict.

    DeepSeek (like OpenAI) represents system prompts as the first message
    in the messages list with ``role: "system"``::

        {"role": "system", "content": "<assembled prompt text>"}

    """

    def to_provider_format(self, prompt: SystemPrompt) -> dict[str, Any]:
        """Translate *prompt* into a DeepSeek ``system`` message dict.

        Parameters
        ----------
        prompt:
            The assembled, provider-independent system prompt.

        Returns
        -------
        dict[str, Any]
            ``{"role": "system", "content": "<text>"}``.
        """
        return {"role": "system", "content": prompt.text}
