---
name: action-refactor
description: 'Refactor code, tests, or rename following design principles after a green test. Triggers: "refactor", "rename", "clean up code".'
argument-hint: "[code | tests | rename]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Refactor

Apply design standards and refactoring rules to code.

## Usage

```
/action-refactor            → Refactor production code (default)
/action-refactor code       → Refactor production code
/action-refactor tests      → Refactor test files
/action-refactor rename     → Rename the last artifact
```

## Mode: Code (default)

Apply the design principles from `guidelines/design-principles`:

- Naming standards (pronounceable, concrete, self-explanatory)
- Function design (SRP, arity, guard clauses, CQS)
- Classes/modules design (encapsulation, composition, rich models)

Steps:

1. Review the code against `guidelines/design-principles`
2. Apply improvements
3. Run tests after refactoring to verify nothing breaks

## Mode: Tests

Apply testing standards from `guidelines/testing-standards`:

- Business-oriented test names (domain language, not technical verbs)
- AAA structure (Arrange-Act-Assert) with blank lines between sections
- Remove TODO lists after implementation is complete
- FIRST principles

Steps:

1. Review tests against `guidelines/testing-standards`
2. Apply improvements
3. Run tests to verify nothing breaks

## Mode: Rename

Rename the last artifact following naming standards from `guidelines/design-principles`:

- Self-explanatory
- Pronounceable
- Concrete
- Clearly expresses the intention

Steps:

1. Identify the artifact to rename
2. Apply naming standards
3. Update all references
4. Run tests to verify nothing breaks
