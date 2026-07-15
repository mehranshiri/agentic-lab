"""System prompt domain models — provider-independent value objects.

Defines immutable representations of the agent's identity, behavioral
rules, and contextual instructions.  These domain objects never depend
on LLM providers, tools, or conversation infrastructure.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InstructionBlock:
    """A single, self-contained block of system-prompt content.

    Each block has a *source* that tracks provenance — where the
    instruction originated — enabling debugging and auditing of
    prompt composition.

    Attributes
    ----------
    content:
        The instruction text.  Blocks are joined by the assembler;
        whitespace between blocks is the assembler's responsibility.
    source:
        Provenance tag indicating where this instruction originated.
        Common values: ``"builtin"``, ``"tools"``, ``"workspace"``,
        ``"user"``.
    """

    content: str
    source: str


@dataclass(frozen=True)
class SystemPrompt:
    """Assembled, provider-independent system prompt.

    A :class:`SystemPrompt` is the product of assembling
    :class:`InstructionBlock` objects from multiple sources.  It is
    immutable and carries no provider-specific formatting.

    Attributes
    ----------
    blocks:
        Ordered tuple of instruction blocks that make up the prompt.
    """

    blocks: tuple[InstructionBlock, ...]

    @property
    def text(self) -> str:
        """Return the full prompt text by joining all blocks.

        Blocks are separated by double newlines for readability.
        """
        return "\n\n".join(block.content for block in self.blocks)
