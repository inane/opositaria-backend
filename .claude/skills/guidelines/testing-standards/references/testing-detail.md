# Testing Standards

## Test Pyramid

```
        /\
       /  \      E2E (few)
      /----\     - Full HTTP flows
     /      \    - Critical paths only
    /--------\   Integration (some)
   /          \  - Repository adapters
  /------------\ - External service adapters
 /              \
/----------------\ Unit (many)
                    - Domain entities, VOs, services
                    - UseCases with InMemoryRepositories
```

- **More unit tests**: Fast, isolated, cover all edge cases
- **Some integration tests**: Real DB, real sandboxes
- **Few E2E tests**: Critical user journeys only

## Test Location

Tests live inside each module:

```
src/[module-name]/tests/
├── unit/              # Fast, no external dependencies
├── integration/       # Real DB (SQLite in-memory or testcontainers)
└── e2e/               # Full HTTP stack
```

## Marks

- **Unit tests**: decorated with `@pytest.mark.unit` — run in parallel
- **Integration tests**: decorated with `@pytest.mark.integration` — run in parallel with isolated DB instances
- **E2E tests**: decorated with `@pytest.mark.e2e` — run sequentially or with isolated test databases

Run with:
```bash
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e
```

## FIRST Principles

- **Fast**: Tests must run quickly. Slow tests break the feedback loop
- **Isolated**: Each test is independent. No shared state, no execution order dependency
- **Repeatable**: Same result every time, in any environment
- **Self-validating**: Clear pass/fail result. No manual inspection needed
- **Timely**: Written at the right time (before code in TDD)

## Naming

- Names in English
- Represent business rules, not implementation details
- Descriptive: what is being tested and what is expected
- Avoid technical names or names coupled to implementation

### Test classes

- Use `Test` prefix with "The [Subject]" format to identify the component/module being tested

### Test functions

- Write tests as business rules, not technical assertions
- Avoid technical verbs: "returns", "should return", "calls", "throws"
- Use domain language: "considers", "validates", "accepts", "allows", "calculates"

```python
class TestInvoiceCalculator:
    """Tests for The Invoice Calculator."""

    def test_applies_a_10_percent_discount_for_orders_above_100(self):
        ...

    def test_does_not_allow_negative_quantities(self):
        ...
```

## AAA Structure (Arrange-Act-Assert)

- **Arrange**: Prepare context and necessary data
- **Act**: Execute the action to test
- **Assert**: Verify the expected result
- Visually separate the three sections (blank line between them)

## Mocks Policy

- Use InMemoryRepositories for UseCase tests (see `guidelines/architecture-hexagonal`)
- Stubs and spies are allowed on application ports (EmailSender, TokenGenerator, OTPGenerator)
- Never use mocks on repositories — always use InMemory implementations
- Before proposing any other mock: consult the Tech Lead first

## Examples

```python
# WORSE - Coupled to implementation
def test_calculatePrice_returns_90():
    result = calculate_price(100, 10)
    assert result == 90

# BETTER - Describes business rule
def test_calculates_price_with_discount_applied_to_given_product():
    original_price = 100
    discount_percentage = 10

    final_price = calculate_discounted_price(original_price, discount_percentage)

    assert final_price == 90
```

## Async Tests

Async test functions are supported via `pytest-asyncio` with `asyncio_mode = "auto"` — simply declare `async def test_...()` and await inside:

```python
@pytest.mark.unit
async def test_processes_payment_concurrently():
    payment = Payment(amount=100, currency="USD")

    result = await process_payment(payment)

    assert result.status == PaymentStatus.COMPLETED
```

No special decorator needed when `asyncio_mode = "auto"` is configured in `pyproject.toml` or `pytest.ini`.

## Exception Testing

Use `pytest.raises` to assert expected exceptions:

```python
def test_rejects_negative_amount():
    with pytest.raises(ValueError, match="Amount must be positive"):
        Payment(amount=-10, currency="USD")
```

## Integration Tests

### When to Use

- Repository adapters (real DB)
- External service adapters (real sandbox)

### Database Setup

Use SQLite in-memory for lightweight testing, or testcontainers for heavier database engines (PostgreSQL, MySQL, etc.):

```python
import sqlite3
import pytest
from uuid import uuid4

@pytest.mark.integration
class TestSqliteOrderRepository:
    @pytest.fixture
    def connection(self):
        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE TABLE orders (id TEXT PRIMARY KEY, customer_id TEXT, total REAL)"
        )
        yield conn
        conn.close()

    @pytest.fixture
    def repository(self, connection):
        return SqliteOrderRepository(connection)

    def test_persists_and_retrieves_an_order(self, repository):
        order_id = uuid4()
        order = Order.create(order_id)

        repository.save(order)
        retrieved = repository.find_by_id(order_id)

        assert retrieved is not None
        assert retrieved.id == order_id
```

### Rules

- **Real dependencies**: Use SQLite in-memory or testcontainers for the database
- **Isolation**: Each test cleans its own data (fixture teardown)
- **No shared state**: Tests must not depend on order of execution
- **File naming**: `*_integration_test.py`

## E2E Tests

### When to Use

- Full HTTP flows through the API
- Critical user journeys

### Rules

- **Test flows, not endpoints**: Cover complete business scenarios
- **Factories/fixtures**: Use factories to create test data
- **Clean slate**: Reset database before each test
- **File naming**: `*_e2e_test.py`

### What NOT to Test in E2E

- Edge cases (those belong in unit tests)
- Error handling details (unit tests)
- All validation combinations (unit tests)
