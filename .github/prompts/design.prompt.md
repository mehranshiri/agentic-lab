---
description: "Design a feature before writing code — requirements, architecture, components, and implementation plan. Run /design."
agent: "ask"
---
Design the feature described by the user before any code is written. Follow the project's [copilot-instructions.md](../copilot-instructions.md) for architecture patterns (SOLID, Strategy, Template Method, Dependency Inversion) and conventions.

## Output

### 1. Requirements
What must the feature do? Distinguish functional requirements (user-visible behavior) from non-functional (performance, security, constraints).

### 2. Architecture
Where does this fit in the existing codebase? Which modules are affected? Reference the project's patterns:
- Strategy pattern (`llm/`) — for provider-swappable components
- Template Method (`tools/base.py`) — for tool-like abstractions
- Dependency Inversion — keep new code decoupled from concrete implementations

### 3. Components
What new classes, functions, or modules are needed? Name them and describe their single responsibility.

### 4. Data flow
How does data move through the system? Include inputs, transformations, and outputs. Use a sequence diagram if the flow spans multiple components.

### 5. APIs
Public signatures for new classes and functions. Include type hints, parameter meanings, and return types.

### 6. Risks
What could go wrong? Edge cases, performance bottlenecks, integration points that might break.

### 7. ADR
Does this design need an Architectural Decision Record? If it changes module boundaries, introduces a new pattern, or adds a dependency — flag it for `docs/adr/`.

### 8. Implementation steps
Ordered, small steps — each should be a self-contained commit. Reference which files to create or modify.
