"""Application entry-point — wires the LLM client and asks a sample question."""

from __future__ import annotations

import asyncio

from llm import LlmClient


async def main() -> None:
    client = LlmClient()
    answer = await client.generate("What is React?")
    print(answer)


if __name__ == "__main__":
    asyncio.run(main())