"""Immutable request object representing a single tool invocation.

Defines *what* tool to call and with *which* arguments, without
coupling to any LLM provider or execution strategy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ToolInvocation:
    """A provider-independent request to execute a single tool.

    Attributes
    ----------
    tool_name:
        The exact name of the tool to invoke (matches
        :attr:`~tools.metadata.ToolMetadata.name`).
    arguments:
        Keyword arguments forwarded directly to
        :meth:`~tools.base.Tool.run`.
    """

    tool_name: str
    arguments: dict[str, Any]
