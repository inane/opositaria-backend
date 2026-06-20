---
name: task-architecture-review
description: 'Review hexagonal architecture compliance: layer boundaries, dependencies, and module structure. Triggers: "review architecture", "check layers".'
argument-hint: "[git range]"
context: fork
agent: architecture-reviewer
allowed-tools: Read, Glob, Grep, Bash, Edit, Write
---

# Architecture Review

Launch a subagent to review code against `guidelines/architecture-hexagonal`.

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

1. Determine the file list from the scope
2. Check dependency direction (infra → app → domain, never backwards)
3. Check layer responsibilities (no business logic in infra, no HTTP in domain)
4. Check module structure and cross-module rules
5. Check naming conventions per layer
6. Fix all violations found
7. Run tests to verify fixes don't break anything

## Output

A table of violations found and fixes applied, plus a module health summary.
