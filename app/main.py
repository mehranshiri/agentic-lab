"""Application entry-point — demonstrates tool invocation.

Registers tools, discovers metadata, translates to provider schemas,
and finally executes a tool through the :class:`~tools.invoker.ToolInvoker`.
"""

from __future__ import annotations

import asyncio
import json

from llm import DeepSeekToolSchemaAdapter
from tools import (
    ReadFileTool,
    ToolCatalog,
    ToolInvocation,
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
    # 2. Catalog — list available tools
    # ------------------------------------------------------------------
    catalog = ToolCatalog(registry)
    tool_metadata_list = catalog.list_tools()

    print(f"Available tools ({len(tool_metadata_list)}):\n")
    for tool in tool_metadata_list:
        print(f"  • {tool.name}")
        print(f"    {tool.description}\n")

    # ------------------------------------------------------------------
    # 3. Schema adapter — produce DeepSeek-compatible definitions
    # ------------------------------------------------------------------
    adapter = DeepSeekToolSchemaAdapter()

    print("─" * 60)
    print("DeepSeek-compatible tool definitions:\n")
    for metadata in tool_metadata_list:
        provider_def = adapter.to_provider_format(metadata)
        print(json.dumps(provider_def, indent=2))
        print()

    # ------------------------------------------------------------------
    # 4. Tool invoker — execute a registered tool
    # ------------------------------------------------------------------
    invoker = ToolInvoker(registry)

    invocation = ToolInvocation(
        tool_name="read_file",
        arguments={"path": "README.md"},
    )

    print("─" * 60)
    print("Executing tool invocation:\n")
    print(f"  tool:  {invocation.tool_name}")
    print(f"  args:  {invocation.arguments}\n")

    result = await invoker.invoke(invocation)

    print(f"Result:\n  success: {result.success}")
    if result.success:
        # Show the first few lines of the file
        preview = "\n".join(result.content.splitlines()[:5])
        print(f"  content (first 5 lines):\n{preview}")
    else:
        print(f"  error:   {result.error}")

    # ------------------------------------------------------------------
    # 5. Graceful handling of an unknown tool
    # ------------------------------------------------------------------
    print("\n" + "─" * 60)
    print("Invoking an unknown tool:\n")

    unknown = ToolInvocation(tool_name="nonexistent_tool", arguments={})
    unknown_result = await invoker.invoke(unknown)

    print(f"Result:\n  success: {unknown_result.success}")
    print(f"  error:   {unknown_result.error}")


if __name__ == "__main__":
    asyncio.run(main())