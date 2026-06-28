"""Provider-specific tool-schema adapter layer.

Translates internal :class:`~tools.metadata.ToolMetadata` descriptors into
the schema required by a given LLM provider without executing tools.
"""

from llm.representations.base import ToolSchemaAdapter
from llm.representations.deepseek import DeepSeekToolSchemaAdapter

__all__ = ["DeepSeekToolSchemaAdapter", "ToolSchemaAdapter"]
