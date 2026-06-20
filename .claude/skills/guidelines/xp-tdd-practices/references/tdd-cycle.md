# TDD Cycle with TPP Example

## Full TPP Example in Action

```python
# Navigator (REASON):
"List of examples to calculate total prices:
1. Empty list
2. List with one price
3. List with multiple prices"

# Test 1: Empty list
def test_calculates_total_of_empty_price_list():
    prices = []

    total = calculate_total(prices)

    assert total == 0

# Driver (RED): Does not compile -> Minimum to compile
def calculate_total(prices):
    pass

# Test fails (None !== 0)

# Navigator (GREEN): "According to TPP: ({} -> constant)"
# Driver (GREEN):
def calculate_total(prices):
    return 0

# Test passes

# Navigator (REFACTOR): "Test passes, now refactor. All clear for now"

# Navigator (RE-EVALUATE): "The next simplest case is: list with one price"

# Test 2: List with one price
def test_calculates_total_of_single_price():
    prices = [100]

    total = calculate_total(prices)

    assert total == 100

# Test fails (0 !== 100)

# Navigator (GREEN): "According to TPP: (constant -> scalar) - use the parameter"
# Driver (GREEN):
def calculate_total(prices):
    if len(prices) == 0:
        return 0
    return prices[0]

# Both tests pass

# Navigator (REFACTOR): "Test passes, now refactor.
# According to design-principles, use a guard clause. Names are clear"

# Navigator (RE-EVALUATE): "The next case is: list with multiple prices"

# Test 3: List with multiple prices
def test_calculates_total_of_multiple_prices():
    prices = [100, 50, 25]

    total = calculate_total(prices)

    assert total == 175

# Test fails (100 !== 175)

# Navigator (GREEN): "According to TPP I have options:
# - (statement -> tail-recursion) - transformation #9
# - (if -> while) - transformation #10
#
# But in Python, sum() is simpler and clearer than recursion or loops.
# Per design-principles: 'Prefer declarative style when it improves readability'"

# Driver (GREEN):
def calculate_total(prices):
    return sum(prices)

# All tests pass

# Navigator (REFACTOR): "Test passes, now refactor.
# The code is simple and expressive. Looks good"
```

## Continuous Refactoring

- Actively identify code smells
- Suggest constant incremental improvements following `guidelines/design-principles`
- Propose extracting functions when there is complexity

(End of file - total 97 lines)
