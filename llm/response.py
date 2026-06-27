"""Rich LLM response value object.

Provides structured access to everything the caller might need
(plain text, token usage, finish reason, …) without coupling
callers to any provider-specific response format.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class LLMResponse:
    """Immutable snapshot of an LLM completion."""

    #: The assistant's plain-text reply.
    text: str

    #: The model that produced this response (e.g. ``"deepseek-chat"``).
    model: str

    #: Token-usage breakdown, if the provider returned it.
    usage: dict[str, int] = field(default_factory=dict)

    #: Why the generation stopped (``"stop"``, ``"length"``, …).
    finish_reason: str = ""

    #: The raw provider response, useful for debugging / evaluation.
    raw: Any = None