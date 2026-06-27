"""Application entry-point — composition root that wires dependencies."""

from __future__ import annotations

import asyncio

from core.config import settings
from llm import LlmClient
from llm.providers import DeepSeekProvider


async def main() -> None:
    provider = DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )
    client = LlmClient(provider)
    answer = await client.generate("What is React?")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())
