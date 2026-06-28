# Sprint 4 – Tool Discovery

## Goal

Introduce the **Tool Catalog** as the discovery layer of the Tool Framework.

The Tool Catalog is responsible for exposing a provider-independent view of the capabilities available in the system. It must not execute tools or contain provider-specific logic.

This sprint establishes the bridge between the Tool Framework and future LLM integrations while keeping both modules independent.

---

## Background

At the end of Sprint 3, the application supports:

* LLM abstraction
* Tool abstraction
* Tool registry
* A concrete `ReadFileTool`

However, there is currently no mechanism for other parts of the system to discover what capabilities are available.

Sprint 4 introduces this missing architectural layer.

---

## Objectives

Implement a `ToolCatalog` responsible for discovering registered tools and exposing their descriptive information.

The catalog should always obtain information from the `ToolRegistry`.

It must **not** maintain its own internal copy of tool metadata.

---

## Responsibilities

### ToolCatalog

The catalog is responsible for:

* Discovering registered tools through the `ToolRegistry`
* Returning immutable descriptions of available tools
* Remaining completely independent from LLM providers
* Providing a stable interface for future LLM adapter modules

The catalog **must not**:

* Execute tools
* Register tools
* Modify tool metadata
* Cache tool information
* Perform provider-specific formatting

---

### Tool Metadata

Use the existing `ToolMetadata` object as the canonical representation of a tool's descriptive information.

At this stage, metadata should include only:

* name
* description

Do **not** introduce input schemas yet.

---

## Architecture

```text
                +----------------+
                | Tool Registry  |
                +----------------+
                        |
                        |
                 discovers tools
                        |
                        ▼
                +----------------+
                | Tool Catalog   |
                +----------------+
                        |
                        |
              returns ToolMetadata
                        |
                        ▼
          Future LLM Provider Adapters
```

The Tool Registry remains the source of truth for executable tool instances.

The Tool Catalog acts only as a discovery layer.

---

## Files

Create:

```text
tools/
    catalog.py
```

Update:

```text
tools/__init__.py

app/main.py
```

---

## Demonstration

Update `app/main.py` to demonstrate:

1. Registering `ReadFileTool`
2. Creating a `ToolCatalog`
3. Listing all available tools
4. Printing each tool's:

   * Name
   * Description

The catalog should never execute a tool.

---

## Constraints

* Keep the Tool Catalog stateless.
* The Tool Catalog must always query the Tool Registry instead of maintaining its own collection.
* Do not introduce provider-specific schemas.
* Do not introduce LangGraph.
* Do not introduce LLM tool calling.
* Do not execute tools through the catalog.
* Do not duplicate metadata already owned by each tool.

---

## Acceptance Criteria

* `ToolCatalog` successfully discovers all registered tools.
* The catalog exposes only descriptive information.
* The catalog always retrieves information from the `ToolRegistry`.
* The catalog contains no provider-specific logic.
* `app/main.py` demonstrates listing available tools without executing them.
* The implementation remains extensible for future provider adapters without modifying the Tool Framework.

---

## Out of Scope

The following items belong to future sprints and must **not** be implemented:

* Tool calling
* Function calling
* JSON Schema generation
* Provider-specific tool schemas
* LangGraph integration
* Agent planning
* Memory
* Tool execution orchestration
* File modification tools

---

## Design Principles

* Single Responsibility Principle (SRP)
* Dependency Inversion Principle (DIP)
* Stateless components
* Separation of discovery and execution
* Framework-first architecture
