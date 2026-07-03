"""DeepSeek-specific tool-schema adapter.

Translates :class:`~tools.metadata.ToolMetadata` into the schema expected by
the DeepSeek Chat Completions API (OpenAI-compatible function-calling format).
"""

from __future__ import annotations

from typing import Any

from llm.representations.base import ToolSchemaAdapter
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
