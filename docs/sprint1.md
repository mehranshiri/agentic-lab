# Sprint 1 – Project Foundation

Create the initial project skeleton for a production-ready Python project named **agentic-lab**.

## Goal

The purpose of this sprint is only to establish the project foundation. Do **not** implement any AI, LangGraph, agents, or business logic yet.

## Requirements

### Dependency Management

* Use **uv** for dependency management.
* Generate the appropriate project files (`pyproject.toml`, `uv.lock` if applicable).
* Target Python 3.13.

### Project Structure

Create the following structure:

```text
agentic-lab/
│
├── app/
│   ├── __init__.py
│   └── main.py
│
├── agent/
│   └── __init__.py
│
├── llm/
│   └── __init__.py
│
├── tools/
│   └── __init__.py
│
├── prompts/
│
├── core/
│   └── __init__.py
│
├── tests/
│
├── .gitignore
├── .python-version
├── README.md
├── pyproject.toml
└── .env.example
```

### Main Entry Point

Implement `app/main.py` so that running

```bash
uv run python -m app.main
```

prints:

```
Agentic Lab Started
```

### Environment

Create a `.env.example` containing placeholder variables:

```
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=
```

Do **not** create a real `.env`.

### Git

Add a production-ready `.gitignore` for Python projects that ignores:

* virtual environments
* `.env`
* Python cache
* IDE files
* build artifacts

### Documentation

Create a concise `README.md` including:

* Project purpose
* Technology stack (placeholder)
* Project structure
* How to install dependencies
* How to run the application

### Constraints

Do **not**:

* install LangGraph
* install LangChain
* install any AI SDK
* write agent logic
* write tool implementations
* write configuration classes
* add placeholder code that is not yet needed

The project should contain only the minimum scaffolding necessary for future development.

## Acceptance Criteria

* The project initializes successfully using `uv`.
* `uv run python -m app.main` executes successfully.
* The directory structure is clean and easy to extend.
* No AI-specific implementation exists yet.
* The project is ready for Sprint 2.
