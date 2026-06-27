"""Application entry-point — demonstrates the Tool Framework.

Registers tools in the :class:`ToolRegistry` and invokes the
``ReadFileTool`` to show the lifecycle (validate → execute → result)
in action.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from tools import ReadFileTool, ToolRegistry


async def main() -> None:
    # ------------------------------------------------------------------
    # 1. Build the registry and register tools
    # ------------------------------------------------------------------
    registry = ToolRegistry()
    registry.register(ReadFileTool())

    print("Registered tools:", registry.list_names())

    # ------------------------------------------------------------------
    # 2. Look up ReadFileTool by name
    # ------------------------------------------------------------------
    tool = registry.get("read_file")
    if tool is None:
        print("Tool 'read_file' not found in registry!")
        return

    # ------------------------------------------------------------------
    # 3. Invoke the tool against a known file (pyproject.toml)
    # ------------------------------------------------------------------
    target = Path(__file__).parent.parent / "pyproject.toml"
    result = await tool.run(path=str(target))

    if result.success:
        print(f"\n--- Contents of {target.name} ---")
        print(result.content)
    else:
        print(f"Tool failed: {result.error}")

    # ------------------------------------------------------------------
    # 4. Demonstrate error handling — non-existent file
    # ------------------------------------------------------------------
    missing = await tool.run(path="/tmp/does_not_exist.txt")
    print(f"\nMissing file → success={missing.success}, error={missing.error}")

    # ------------------------------------------------------------------
    # 5. Demonstrate error handling — missing required parameter
    # ------------------------------------------------------------------
    bad_call = await tool.run()
    print(f"No path → success={bad_call.success}, error={bad_call.error}")


if __name__ == "__main__":
    asyncio.run(main())