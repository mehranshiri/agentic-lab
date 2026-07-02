"""DeepSeek LLM provider.

Uses the OpenAI-compatible :class:`openai.AsyncOpenAI` client pointed at
the DeepSeek API endpoint.
"""

from __future__ import annotations

import json
from typing import Any

from openai import AsyncOpenAI

from llm.base import LlmProvider
from llm.provider_tool_call import ProviderToolCall
from llm.response import LLMResponse


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
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        chosen_model = model or self._default_model

        kwargs: dict[str, Any] = {
            "model": chosen_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            kwargs["tools"] = tools

        response = await self._client.chat.completions.create(**kwargs)  # type: ignore[arg-type]

        choice = response.choices[0]
        usage = response.usage

        # ------------------------------------------------------------------
        # Extract tool calls from the provider response (if any)
        # ------------------------------------------------------------------
        tool_calls: list[ProviderToolCall] | None = None
        raw_tool_calls = getattr(choice.message, "tool_calls", None)
        if raw_tool_calls:
            tool_calls = []
            for tc in raw_tool_calls:
                try:
                    arguments = json.loads(tc.function.arguments)
                except (json.JSONDecodeError, AttributeError):
                    arguments = {}
                tool_calls.append(
                    ProviderToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=arguments,
                    )
                )

        return LLMResponse(
            text=choice.message.content or "",
            model=response.model or chosen_model,
            usage={
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "total_tokens": usage.total_tokens if usage else 0,
            },
            finish_reason=choice.finish_reason or "",
            raw=response,
            tool_calls=tool_calls,
        )
