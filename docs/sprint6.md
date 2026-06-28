# Sprint 6 – Tool Invocation

## Goal

Introduce the **Tool Invoker** as the execution boundary between the LLM module and the Tool Framework.

The Tool Invoker is responsible for receiving tool invocation requests, resolving the requested tool through the `ToolRegistry`, invoking the tool lifecycle, and returning a standardized result.

This sprint establishes the first end-to-end execution flow while preserving the separation of concerns introduced in previous sprints.

---

# Why this sprint exists

After Sprint 5:

* The Tool Framework defines executable tools.
* The Tool Catalog exposes discoverable tool descriptions.
* The LLM module understands available tools through provider-specific representations.

However, there is still no component responsible for coordinating tool invocation.

Sprint 6 introduces this missing architectural boundary.

---

# Objectives

* Introduce a provider-independent tool invocation model.
* Implement a stateless `ToolInvoker`.
* Resolve tools through the existing `ToolRegistry`.
* Execute a single tool invocation.
* Return standardized `ToolResult` objects.
* Demonstrate the first executable path from a tool request to a tool result.

---

# Responsibilities

## ToolInvoker

The `ToolInvoker` is responsible for:

* Receiving a tool invocation request.
* Resolving the requested tool using the `ToolRegistry`.
* Invoking the tool lifecycle (`tool.run()`).
* Returning the resulting `ToolResult`.
* Handling invocation failures such as:

  * unknown tool
  * invalid request
  * execution errors

The Tool Invoker **must not**:

* Communicate with LLM providers.
* Discover available tools.
* Select which tool should be executed.
* Execute multiple tools.
* Manage workflows.
* Retry failed operations.
* Maintain state.

---

## ToolInvocation

Introduce an immutable request object representing a single tool invocation.

Example:

```python
ToolInvocation(
    tool_name="read_file",
    arguments={
        "path": "README.md"
    }
)
```

The invocation model must remain provider-independent.

---

# Architecture

```text
                ToolInvocation
                       │
                       ▼
                +---------------+
                | ToolInvoker   |
                +---------------+
                       │
                       ▼
                +---------------+
                | ToolRegistry  |
                +---------------+
                       │
                       ▼
                +---------------+
                | Tool.run()    |
                +---------------+
                       │
                       ▼
                +---------------+
                | ToolResult    |
                +---------------+
```

---

# Files

Create:

```text
tools/
    invocation.py
    invoker.py
```

Update:

```text
tools/__init__.py
app/main.py
```

---

# Demonstration

Update `app/main.py` to demonstrate:

1. Registering `ReadFileTool`.
2. Creating a `ToolInvoker`.
3. Creating a `ToolInvocation`.
4. Executing the invocation.
5. Printing the returned `ToolResult`.
6. Demonstrating graceful handling of an unknown tool.

---

# Constraints

* Keep the `ToolInvoker` stateless.
* Keep the Tool Framework provider-independent.
* Do not introduce planners.
* Do not introduce orchestration logic.
* Do not introduce retries.
* Do not introduce parallel execution.
* Do not introduce LangGraph.
* Do not modify the existing Tool lifecycle.
* Do not couple the invoker to any LLM provider.

---

# Acceptance Criteria

* `ToolInvocation` models a single provider-independent tool request.
* `ToolInvoker` resolves tools through `ToolRegistry`.
* `ToolInvoker` executes exactly one tool lifecycle.
* Execution returns a standardized `ToolResult`.
* Unknown tools are handled gracefully.
* The implementation introduces no provider-specific dependencies into the Tool Framework.
* `app/main.py` demonstrates a complete invocation flow.

---

# Out of Scope

The following features belong to future sprints and must **not** be implemented:

* Tool calling from LLM providers
* Parsing LLM tool-call responses
* Multi-tool execution
* Workflow orchestration
* Tool selection
* Planning
* Memory
* Retry policies
* Parallel execution
* LangGraph integration

---

# Design Principles

* Single Responsibility Principle (SRP)
* Dependency Inversion Principle (DIP)
* Stateless components
* Separation of discovery and execution
* Provider-independent Tool Framework

---

# Consequences

## Positive

* Introduces a dedicated execution boundary.
* Keeps the Tool Framework independent of LLM providers.
* Establishes a reusable execution component for future workflows.
* Preserves clear ownership of execution responsibilities.

## Negative

* Supports only single-tool execution.
* No retry or recovery mechanisms.
* No orchestration or workflow management.

## Deferred

The following capabilities will be addressed in future sprints:

* LLM tool calling
* Tool response parsing
* Multi-step workflows
* Planner
* Tool selection
* Orchestrator
* Memory
* Evaluation loops
* LangGraph integration
