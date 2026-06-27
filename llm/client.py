"""Clean LLM facade — the only entry-point application code should need.

``LlmClient`` wraps any :class:`LlmProvider` and exposes a single
``generate(prompt)`` method.  This keeps provider-specific details
behind the Strategy boundary.
"""

from __future__ import annotations

from llm.base import LlmProvider


class LlmClient:
    """High-level LLM client.

    Responsibilities:
    * Accept a plain-text *prompt*.
    * Delegate to the underlying :class:`LlmProvider`.
    * Return the assistant's plain-text reply.
    """

    def __init__(self, provider: LlmProvider) -> None:
        """Initialise the client.

        Parameters
        ----------
        provider:
            Any :class:`LlmProvider` implementation (injected by the
            composition root).
        """
        self._provider = provider

    async def generate(self, prompt: str) -> str:
        """Send *prompt* to the LLM and return the reply as plain text.

        Parameters
        ----------
        prompt:
            A user message string (e.g. ``"Explain quantum computing"``).

        Returns
        -------
        str
            The model's response content.
        """
        messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        return await self._provider.send_message(messages)