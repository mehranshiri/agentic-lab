"""Descriptive information about a tool (name, description, parameters, …).

Tool metadata is intentionally kept small and independent so that
registries, UIs, and LLM prompting layers can reason about tools
without importing their implementations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ToolMetadata:
    """Lightweight descriptor for a tool.

    Attributes
    ----------
    name:
        Unique, human-readable identifier for the tool (e.g.
        ``"read_file"``).  Used as the key in the tool registry.
    description:
        Short sentence explaining what the tool does, suitable for
        display in a UI or injection into an LLM system prompt.
    parameters:
        JSON Schema describing the tool's input parameters.  Defaults
        to an empty object schema (no parameters).  Conforming providers
        use this to generate well-formed tool calls automatically.
    """

    name: str
    description: str
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {},
            "required": [],
        }
    )
