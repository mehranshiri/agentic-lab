"""Abstract base class for LLM providers (Strategy pattern).

Every concrete LLM provider must subclass :class:`LlmProvider` and
implement :meth:`send_message`.  This makes it trivial to swap
providers (e.g. from DeepSeek to OpenAI) without touching any
application code that depends on the abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from llm.response import LLMResponse


class LlmProvider(ABC):
    """Strategy interface for an LLM backend.

    Responsibilities:
    * Accept a list of messages (in Chat Completions format).
    * Return a rich :class:`LLMResponse` value object.
    """

    @abstractmethod
    async def send_message(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> LLMResponse:
        """Send *messages* to the LLM and return a structured response.

        Parameters
        ----------
        messages:
            List of message dicts, e.g.
            ``[{"role": "user", "content": "Hello"}]``.
        model:
            Optional model name override.  When ``None`` the provider
            uses its configured default.
        temperature:
            Sampling temperature (0.0 – 2.0).
        max_tokens:
            Maximum tokens in the response.

        Returns
        -------
        LLMResponse
            Structured response with ``.text``, ``.model``, ``.usage``,
            ``.finish_reason``, and ``.raw``.
        """
        ...
