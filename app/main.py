"""Application entry-point — demonstrates the tool-schema adapter layer.

Registers tools, discovers them through the :class:`~tools.catalog.ToolCatalog`,
and translates their metadata into DeepSeek-compatible tool definitions using
the provider-specific schema adapter.
"""

from __future__ import annotations

import json

from llm import DeepSeekToolSchemaAdapter
from tools import ReadFileTool, ToolCatalog, ToolRegistry


def main() -> None:
    # ------------------------------------------------------------------
    # 1. Build the registry and register tools
    # ------------------------------------------------------------------
    registry = ToolRegistry()
    registry.register(ReadFileTool())

    # ------------------------------------------------------------------
    # 2. Create the catalog (discovery layer — never executes tools)
    # ------------------------------------------------------------------
    catalog = ToolCatalog(registry)

    # ------------------------------------------------------------------
    # 3. List available tool metadata through the catalog
    # ------------------------------------------------------------------
    tool_metadata_list = catalog.list_tools()

    print(f"Available tools ({len(tool_metadata_list)}):\n")
    for tool in tool_metadata_list:
        print(f"  • {tool.name}")
        print(f"    {tool.description}\n")

    # ------------------------------------------------------------------
    # 4. Translate to DeepSeek-compatible tool definitions
    # ------------------------------------------------------------------
    adapter = DeepSeekToolSchemaAdapter()

    print("─" * 60)
    print("DeepSeek-compatible tool definitions:\n")

    for metadata in tool_metadata_list:
        provider_def = adapter.to_provider_format(metadata)
        print(json.dumps(provider_def, indent=2))
        print()


if __name__ == "__main__":
    main()