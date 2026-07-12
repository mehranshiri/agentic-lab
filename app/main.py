"""Application entry-point — bootstraps dependencies and invokes AgentRuntime.

The entry-point is deliberately thin: it wires together all dependencies
and delegates the entire interaction to :class:`~agent.runtime.AgentRuntime`.
"""

from __future__ import annotations

import asyncio

from agent.runtime import AgentRuntime
from core.config import PROJECT_ROOT, settings
from llm import (
    DeepSeekConversationRepresentation,
    DeepSeekProvider,
    DeepSeekToolSchemaAdapter,
    ToolCallBridge,
)
from tools import (
    ExecutionContext,
    GrepTool,
    ReadFileTool,
    ShellTool,
    ToolCatalog,
    ToolInvoker,
    ToolRegistry,
    WriteFileTool,
)


async def main() -> None:
    # ── 1. Tool infrastructure ──────────────────────────────────────────
    registry = ToolRegistry()
    registry.register(ReadFileTool())
    registry.register(WriteFileTool())
    registry.register(ShellTool())
    registry.register(GrepTool())

    catalog = ToolCatalog(registry)
    context = ExecutionContext(workspace_root=PROJECT_ROOT)
    invoker = ToolInvoker(registry, context=context)

    # ── 2. LLM infrastructure ───────────────────────────────────────────
    provider = DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )
    conversation_representation = DeepSeekConversationRepresentation()
    tool_schema_adapter = DeepSeekToolSchemaAdapter()

    # ── 3. Bridge (tool execution boundary) ─────────────────────────────
    tool_call_bridge = ToolCallBridge(invoker)

    # ── 4. Runtime — the only public entry point ────────────────────────
    runtime = AgentRuntime(
        provider=provider,
        conversation_representation=conversation_representation,
        tool_schema_adapter=tool_schema_adapter,
        tool_catalog=catalog,
        tool_call_bridge=tool_call_bridge,
    )

    # ── 5. Execute ──────────────────────────────────────────────────────
    prompt = "Read the README.md file and choose a Title for this app we are building."
    print(f"Prompt: {prompt}\n")
    print("Agent is working …\n")

    result = await runtime.run(prompt)

    print("─" * 60)
    print(f"Success: {result.success}")
    print(f"Answer:\n{result.answer}")


if __name__ == "__main__":
    asyncio.run(main())
