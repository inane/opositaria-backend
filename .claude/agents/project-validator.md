---
description: Full project validator. Use proactively after code changes to compile, lint, format, and run all tests.
tools: Read, Glob, Bash, Edit
isolation: worktree
---

# Validate Agent

Run full project validation. Auto-fix formatting and lint issues. Report remaining errors.

## Steps

1. **Read project configuration** to determine available tools:
   - Check `pyproject.toml` for tool configuration (ruff, mypy, pytest)
   - If no `pyproject.toml`, check README for validation commands

2. **Auto-fix formatting** (if available):

   ```bash
   uv run ruff format .
   ```

   Report any formatting errors that could not be auto-fixed.

3. **Auto-fix lint errors** (if available):

   ```bash
   uv run ruff check --fix .
   ```

   Report any remaining lint errors that could not be auto-fixed.

4. **Run MyPy type check** (if available):

   ```bash
   uv run mypy src/
   ```

   Capture and report all type errors.

5. **Run remaining lint check** (after auto-fix):

   ```bash
   uv run ruff check .
   ```

   Capture and report errors that were not auto-fixable.

6. **Run unit tests**:

   ```bash
   uv run pytest
   ```

   Capture and report failing tests.

7. **Run integration tests** (if available):

   ```bash
   uv run pytest -m integration
   ```

8. **Run E2E tests** (if available):

   ```bash
   uv run pytest -m e2e
   ```

## Output Format

Report a summary table followed by details for each failing check:

### Summary

| Check           | Status            | Details                          |
|-----------------|-------------------|----------------------------------|
| Formatting      | fixed/clean       | N files formatted                |
| Linting         | fixed/pass/fail   | N auto-fixed, N remaining errors |
| MyPy type check | pass/fail         | N errors                         |
| Unit tests      | pass/fail         | N passed, N failed               |
| Integration tests | pass/fail/skipped | N passed, N failed               |
| E2E tests       | pass/fail/skipped | N passed, N failed               |

### Errors (if any)

For each error that could not be auto-fixed:

- **Check**: Which check failed
- **File**: File path and line number
- **Error**: Description
