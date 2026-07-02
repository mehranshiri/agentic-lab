"""Application entry-point — demonstrates end-to-end LLM-driven tool execution.

Builds the entire pipeline: registry → catalog → schema adapter → LLM with
tools → ToolCallBridge → structured results.
"""

from __future__ import annotations

import asyncio
import json

from core.config import settings
from llm import (
    DeepSeekProvider,
    DeepSeekToolSchemaAdapter,
    ProviderToolCall,
    ToolCallBridge,
    ToolCallResult,
)
from tools import (
    ReadFileTool,
    ToolCatalog,
    ToolInvoker,
    ToolRegistry,
)


async def main() -> None:
    # ------------------------------------------------------------------
    # 1. Build the registry and register tools
    # ------------------------------------------------------------------
    registry = ToolRegistry()
    registry.register(ReadFileTool())

    # ------------------------------------------------------------------
    # 2. Catalog — discover available tools
    # ------------------------------------------------------------------
    catalog = ToolCatalog(registry)
    tool_metadata_list = catalog.list_tools()

    print(f"Registered tools ({len(tool_metadata_list)}):\n")
    for tool in tool_metadata_list:
        print(f"  • {tool.name}")
        print(f"    {tool.description}\n")

    # ------------------------------------------------------------------
    # 3. Schema adapter — produce DeepSeek-compatible tool definitions
    # ------------------------------------------------------------------
    adapter = DeepSeekToolSchemaAdapter()
    provider_tools = [
        adapter.to_provider_format(meta) for meta in tool_metadata_list
    ]

    print("─" * 60)
    print("DeepSeek-compatible tool definitions:\n")
    for pt in provider_tools:
        print(json.dumps(pt, indent=2))
        print()

    # ------------------------------------------------------------------
    # 4. LLM — ask DeepSeek to use a tool
    # ------------------------------------------------------------------
    provider = DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    prompt = (
        "Read the file 'README.md' using the available tool, "
        "then tell me what this project is about in one sentence."
    )

    print("─" * 60)
    print(f"Prompt:\n  {prompt}\n")
    print("Calling DeepSeek with tools …\n")

    response = await provider.send_message(
        messages=[{"role": "user", "content": prompt}],
        tools=provider_tools,
    )

    print(f"Response text: {response.text or '(no text — tool call expected)'}")
    print(f"Finish reason: {response.finish_reason}")
    print(f"Usage:         {response.usage}\n")

    if response.tool_calls:
        print(f"Tool calls returned: {len(response.tool_calls)}\n")
        for tc in response.tool_calls:
            print(f"  → {tc.name}({json.dumps(tc.arguments)})")
    else:
        print("(No tool calls returned — LLM answered directly)\n")

    # ------------------------------------------------------------------
    # 5. ToolCallBridge — execute tool calls returned by the LLM
    # ------------------------------------------------------------------
    if response.tool_calls:
        print("\n" + "─" * 60)
        print("Processing tool calls through ToolCallBridge:\n")

        invoker = ToolInvoker(registry)
        bridge = ToolCallBridge(invoker)

        results: list[ToolCallResult] = await bridge.process(
            response.tool_calls
        )

        for i, tcr in enumerate(results, 1):
            print(f"  [{i}] {tcr.invocation.tool_name}")
            print(f"      success: {tcr.result.success}")
            if tcr.result.success:
                preview = "\n".join(
                    tcr.result.content.splitlines()[:5]
                )
                print(f"      content (first 5 lines):\n{preview}")
            else:
                print(f"      error:   {tcr.result.error}")
            print()

    # ------------------------------------------------------------------
    # 6. Unknown tool — demonstrate graceful failure
    # ------------------------------------------------------------------
    print("─" * 60)
    print("Simulated tool call for an unknown tool:\n")

    invoker = ToolInvoker(registry)
    bridge = ToolCallBridge(invoker)

    unknown_results = await bridge.process(
        [
            ProviderToolCall(
                id="call_fake_1",
                name="delete_everything",
                arguments={},
            )
        ]
    )

    for tcr in unknown_results:
        print(f"  tool:     {tcr.invocation.tool_name}")
        print(f"  success:  {tcr.result.success}")
        print(f"  error:    {tcr.result.error}")
        print()


if __name__ == "__main__":
    asyncio.run(main())