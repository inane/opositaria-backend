---
name: action-tdd
description: 'Enforce the TDD 5-step cycle and TPP when implementation skips the red-green-refactor flow. Triggers: "apply TDD", "enforce TDD", "apply TPP"'.
argument-hint: "[tdd | tpp]"
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Enforce TDD

Corrective command when the TDD cycle or TPP transformations are being skipped.

## Usage

```
/action-tdd           → Enforce full TDD cycle
/action-tdd tdd       → Enforce full TDD cycle
/action-tdd tpp       → Enforce TPP (simplest transformation)
```

## Mode: TDD (default)

The TDD cycle from `guidelines/xp-tdd-practices` and `guidelines/xp-tdd-practices` is being skipped. Apply strict TDD:

1. Stop current implementation
2. Review the TDD 5-step cycle (REASON, RED, GREEN, REFACTOR, RE-EVALUATE)
3. Follow the inside-out development approach from `guidelines/xp-tdd-practices`
4. Resume with the correct workflow

## Mode: TPP

The implementation is making jumps that are too big. Apply TPP (Transformation Priority Premise):

1. Identify the current transformation being applied
2. Check the TPP table in `guidelines/xp-tdd-practices`
3. Choose the simplest transformation that makes the test pass (the lowest number)
4. Implement only that transformation
