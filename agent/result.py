"""AgentResult — immutable value object describing the outcome of an agent interaction."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResult:
    """Immutable snapshot describing the outcome of one completed interaction.

    Attributes
    ----------
    success:
        ``True`` when the agent completed its interaction without error.
    answer:
        The final text answer produced by the agent.  May be empty when
        the interaction failed.
    """

    success: bool
    answer: str
