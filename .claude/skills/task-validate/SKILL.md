---
name: task-validate
description: Full project validation: type check, lint, format, and run all tests. Triggers: "validate", "check project", "run checks".
context: fork
agent: project-validator
allowed-tools: Read, Glob, Bash, Edit
---

# Validate

Launch a subagent to run full project validation: MyPy type checking, linting, formatting, and all test suites.

The agent runs each check via `uv run`, fixes format and lint auto-fixable issues, and reports results.

## Checks

| Check | Command |
|-------|---------|
| Formatting | `uv run ruff format .` |
| Linting | `uv run ruff check .` |
| MyPy type check | `uv run mypy src/` |
| Unit tests | `uv run pytest` |
| Integration tests | `uv run pytest -m integration` |
| E2E tests | `uv run pytest -m e2e` |

## Output

A summary table of all checks (MyPy, lint, format, unit tests, integration tests, E2E tests) with pass/fail status and error details.
