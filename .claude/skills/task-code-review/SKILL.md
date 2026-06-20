---
name: task-code-review
description: Review current branch changes against design principles and fix issues found. Triggers: "review code", "code review".
argument-hint: "[git range]"
context: fork
agent: code-reviewer
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# Code Review

Launch a subagent to review changed files against `guidelines/design-principles`.

## Scope

If a git range is provided (e.g., `abc1234...HEAD`), review only files in that range:

```bash
git diff --name-only <range> -- '*.py'
```

If no git range is provided, review all changed files on the current branch:

```bash
git diff --name-only main -- '*.py'
```

## What the Agent Does

1. Determine the file list from the scope (skip test files: `*_test.py`)
2. Read each changed file
3. Evaluate against `guidelines/design-principles`:
   - Naming (pronounceable, concrete, self-explanatory)
   - Functions (SRP, arity, guard clauses, CQS)
   - Classes/modules (encapsulation, composition, rich models)
   - Error handling
4. Fix all issues found
5. Run tests to verify fixes don't break anything

## Output

A table of issues found and fixes applied per file.
