---
name: task-testing-review
description: Review test quality, naming, and coverage across unit, integration, and E2E layers. Triggers: "review tests", "test quality", "check coverage".
argument-hint: "[git range]"
context: fork
agent: tests-reviewer
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# Testing Review

Launch a subagent to review test files against `guidelines/testing-standards` and `guidelines/xp-tdd-practices`.

## Scope

If a git range is provided (e.g., `abc1234...HEAD`), review only test files and their production counterparts in that range:

```bash
git diff --name-only <range> -- '*_test.py'
```

If no git range is provided, review all changed test files on the current branch:

```bash
git diff --name-only main -- '*_test.py'
```

## What the Agent Does

1. Determine the test file list from the scope
2. Check test quality (FIRST principles, naming, AAA structure)
3. Check no-mocks policy (InMemory repos and stubs only)
4. Analyze coverage gaps across unit/integration/E2E layers
5. Create missing tests if needed
6. Fix issues and run the full test suite

## Output

Three tables: quality fixes applied, coverage analysis per production file, and new tests created.
