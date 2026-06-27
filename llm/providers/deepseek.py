"""DeepSeek LLM provider.

Uses the OpenAI-compatible :class:`openai.AsyncOpenAI` client pointed at
the DeepSeek API endpoint.
"""

from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from llm.base import LlmProvider


class DeepSeekProvider(LlmProvider):
    """LLM provider that calls the DeepSeek Chat Completions API.

    Dependencies (*api_key*, *base_url*) are injected via the constructor
    so that the provider does not reach for a global config singleton.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str = "deepseek-chat",
    ) -> None:
        self._default_model = model
        self._client: AsyncOpenAI = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
        )

    async def send_message(
        self,
        messages: list[dict[str, str]],
        *,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        chosen_model = model or self._default_model

        response = await self._client.chat.completions.create(
            model=chosen_model,
            messages=messages,  # type: ignore[arg-type]
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return response.choices[0].message.content or ""