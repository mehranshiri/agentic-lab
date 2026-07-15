"""Provider-specific adapter layer.

Translates internal domain descriptors (:class:`~tools.metadata.ToolMetadata`,
:class:`~prompts.models.SystemPrompt`) into the schema required by a given
LLM provider without executing tools or prompts.
"""

from llm.representations.base import SystemPromptAdapter, ToolSchemaAdapter
from llm.representations.deepseek import (
    DeepSeekSystemPromptAdapter,
    DeepSeekToolSchemaAdapter,
)

__all__ = [
    "DeepSeekSystemPromptAdapter",
    "DeepSeekToolSchemaAdapter",
    "SystemPromptAdapter",
    "ToolSchemaAdapter",
]
