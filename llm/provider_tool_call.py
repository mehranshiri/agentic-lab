"""Provider-independent tool call value object.

Represents a single tool call extracted from an LLM provider response,
decoupled from any specific SDK's response format.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ProviderToolCall:
    """A single tool call extracted from a provider response.

    Attributes
    ----------
    id:
        Provider-assigned identifier for this tool call (e.g. ``"call_xxx"``).
    name:
        The name of the function/tool to invoke.
    arguments:
        Parsed keyword arguments as a dict (already JSON-decoded).
    """

    id: str
    name: str
    arguments: dict[str, Any]