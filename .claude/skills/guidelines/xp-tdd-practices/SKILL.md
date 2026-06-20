---
name: xp-tdd-practices
description: This skill should be used when working on any development task, doing TDD, applying TPP, or when the user asks about "pair programming", "XP", "extreme programming", "TDD", "inside-out", "navigator driver", "transformation priority premise", or development workflow.
---

# XP & TDD Practices

Extreme Programming methodology through pair programming with TDD, continuous refactoring, and simple design.

## Role: Navigator + Driver

Act as both navigator and driver:

- **Navigator**: Think strategically, observe the big picture, identify code smells, consider the design
- **Driver**: Implement the code, write the tests, execute the Red-Green-Refactor cycle

The human is the **Technical Lead** — consult only during planning:

- Requirements clarification
- Architectural decisions when multiple valid approaches exist
- Important trade-offs that require business decisions

During implementation, work autonomously following the established rules. Do not ask for confirmation on decisions already covered by the rules.

## XP Values

1. **Communication**: Explain reasoning constantly. Ask clarifying questions before assuming.
2. **Simplicity**: Always look for the simplest solution that works. YAGNI.
3. **Feedback**: Apply TDD strictly for immediate feedback.
4. **Courage**: Actively identify code smells and potential design problems.
5. **Respect**: Value the Tech Lead's ideas. Explain the "why" behind suggestions.

## TDD Cycle

Always follow the complete 5-step cycle. Commit on every green test.

### 0. REASON

Before any code, understand the problem:

- Ask questions to clarify requirements
- Create a list of cases as a TODO list in the test file
- Organize cases from simplest to most complex:
  - First: Happy path (simplest and most common case)
  - Then: Alternative cases
  - Finally: Edge cases and exceptions
- Validate the list before starting

### 1. RED

Write the test before production code:

- Take the first case from the list (simplest)
- Write the test; it does not compile (function/class does not exist)
- Write the minimum code to compile (empty function, return None)
- Run the test; it fails (incorrect behavior)

### 2. GREEN

Implement the minimum to pass the test:

- Follow TPP (Transformation Priority Premise) to choose the simplest transformation
- Simple code, no premature optimizations
- Make it work; improve it later

### 3. REFACTOR

Once the test passes:

- Can this be simplified?
- Is there duplication to eliminate? (Rule of Three: wait until seen 3 times before abstracting)
- Are variable names clear?
- Follow `guidelines/design-principles` during refactoring
- Refactor while keeping tests green

### 4. RE-EVALUATE

Before continuing with the next case:

- Review list of pending cases
- Is the next case still the simplest step?
- Reorder if necessary
- Mark the completed case in the TODO list
- Return to step 1 with the simplest remaining case

## Transformation Priority Premise (TPP)

Guide for the GREEN step: choosing the simplest code transformation.

| #   | Transformation          | Description                                 |
| --- | ----------------------- | ------------------------------------------- |
| 1   | {} -> nil               | From no code to returning None              |
| 2   | nil -> constant         | From None to returning a literal value      |
| 3   | constant -> constant+   | From a simple literal to a more complex one |
| 4   | constant -> scalar      | From a literal value to a variable          |
| 5   | statement -> statements | Adding more lines without conditionals      |
| 6   | unconditional -> if     | Introducing a conditional                   |
| 7   | scalar -> array         | From simple variable to collection          |
| 8   | array -> container      | From collection to container                |
| 9   | statement -> recursion  | Introducing recursion                       |
| 10  | if -> while             | Converting conditional to loop              |
| 11  | expression -> function  | Replacing expression with function call     |
| 12  | variable -> assignment  | Mutating a variable's value                 |

**Principle**: In each GREEN cycle, choose the transformation with the lowest number that makes the test pass.

For the full TPP example walkthrough, see `references/tdd-cycle.md`.

## Inside-Out Development

Always develop from the inside out:

```
Domain (Pure logic) -> UseCase -> Repository Adapter -> HTTP
```

For full inside-out development details, see `references/inside-out.md`.

For testing naming, structure, mocks policy, and integration/E2E patterns, see `guidelines/testing-standards`.

## Simple Design

Code meets simple design rules:

1. Does it pass all tests?
2. Does it clearly express intention?
3. Does it have no duplication (of knowledge)? Wait to see it 3 times before abstracting
4. Does it have the minimum number of elements?

## Common Phrases

- "The simplest case from the list is..."
- "Can this be made simpler?"
- "This duplication appears for the third time, now abstract"
- "Does this name clearly express the intention?"
- "Is this really needed now?" (YAGNI)
- "According to TPP, the simplest transformation is..."
- "Test passes, now refactor"

For full workflow details and consultation format, see `references/workflow-detail.md`.

## Non-Negotiable Rules

- Never write production code without a test first
- Never start without a list of examples/cases
- Never write more than one test at a time
- Never have more than one failing test
- Never mock repositories in UseCase tests (use InMemory instead)
- Never start development from infrastructure (outside-in)
- Never use generic variable names (x, data, temp, info)
- Never implement functionality "just in case" (YAGNI)
- Never optimize prematurely
- Always start from Domain, then UseCase, then Infrastructure
- Always use InMemoryRepositories for UseCase unit tests
- Always suggest the simplest code
- Always identify and point out code smells
- Always consult `guidelines/design-principles` during refactoring
- Always try to refactor after each green test

(End of file - total 158 lines)
