# XP Pair Programming Workflow Detail

## When to Consult the Technical Lead

Consult (with prior analysis) when:

- **Architecture decisions**: "Options A vs B have been considered, which is preferred given that...?"
- **Ambiguous requirements**: "This could mean X or Y, what is the intention?"
- **Important trade-offs**: "Optimizing for X means losing Y, what is the priority?"
- **Technologies/dependencies**: "Is this library acceptable or is another alternative preferred?"
- **Design validation**: "This design has been reached, does it seem correct?"

## Consultation Format

When consulting, always include:

1. **Context**: What is being attempted
2. **Analysis**: Options that have been considered
3. **Specific question**: What needs to be decided
4. **Recommendation** (if any): What seems better and why

Example:

```
"Invoice has been implemented with 3 tests. Discounts have complex
logic (by volume, by VIP customer, by season).
Options considered:
- Option A: Methods in Invoice (high cohesion)
- Option B: Separate DiscountCalculator (more testable)

Recommendation: A for now (only 3 types of discounts). Will there
be many more types of discounts in the future?"
```

## Tone

- Direct and straightforward
- Constructive, always with alternatives

(End of file - total 38 lines)
