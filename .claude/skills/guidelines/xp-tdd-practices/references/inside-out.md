# Inside-Out TDD Development

Follow the TDD cycle defined in `guidelines/xp-tdd-practices` for each layer.

## Development Flow

Always develop from the inside out:

```
Domain (Pure logic) -> UseCase -> Repository Adapter -> HTTP
```

This ensures:

- Pure business logic first
- No premature infrastructure decisions
- Testable from the core
- Clear dependency flow

## Layer Progression

```
1. Start with Domain value objects
   -> TDD cycle for each value object behavior

2. Then with Domain entities
   -> TDD cycle for each entity behavior

3. Build InMemoryRepositories
   -> TDD cycle for repository behavior

4. Add Domain Services (if needed)
   -> TDD cycle for complex domain logic

5. Build UseCases
   -> TDD cycle using InMemoryRepositories

6. Implement Repository Adapters
   -> Integration tests with real DB

7. Add External Service Adapters
   -> Integration tests with real sandbox

8. Wire up HTTP/Controllers
   -> E2E tests for full flow
```

## Unit Tests

### Domain Layer (entities, value objects, services)

Pure unit tests with no dependencies.

```python
class TestOrder:
    def test_calculates_total_from_line_items(self):
        order = Order.create(uuid4())
        order.add_item(product, 2)

        total = order.calculate_total()

        assert total == Money.create(200, "EUR")
```

### Use Cases

Unit tests using InMemoryRepositories (not mocks).

```python
class TestCreateOrderUseCase:
    async def test_creates_and_persists_an_order(self):
        order_repository = InMemoryOrderRepository()
        product_repository = InMemoryProductRepository([product])
        use_case = CreateOrderUseCase(order_repository, product_repository)

        order = await use_case.execute(product_id, 2)

        assert order.id is not None
        assert await order_repository.find_by_id(order.id) is not None
```

## Integration Tests

### Repository Adapters

Test against real database.

```python
class TestPostgresOrderRepository:
    async def test_persists_and_retrieves_an_order(self):
        repository = PostgresOrderRepository(test_db_connection)
        order = Order.create(uuid4())

        await repository.save(order)
        retrieved = await repository.find_by_id(order.id)

        assert retrieved is not None
        assert retrieved.id == order.id
```

### Application Port Adapters

Test against real external services (sandbox/test environment).

```python
class TestStripePaymentAdapter:
    async def test_charges_payment_in_test_mode(self):
        adapter = StripePaymentAdapter(stripe_test_client)

        result = await adapter.charge(Money.create(100, "EUR"), "tok_visa")

        assert result.success is True
```

## Mocks Policy

### Never mock:

- Repositories (use InMemoryRepository instead)
- Domain entities or value objects
- Domain services
- External service adapters in integration tests (use real sandbox)

### Stubs/Spies ONLY in:

- UseCase tests when the UseCase depends on an external service port

```python
class TestProcessPaymentUseCase:
    async def test_processes_payment_and_notifies(self):
        order_repository = InMemoryOrderRepository([order])
        payment_gateway = MagicMock()
        payment_gateway.charge.return_value = PaymentResult(success=True)
        notifier = MagicMock()
        use_case = ProcessPaymentUseCase(
            order_repository, payment_gateway, notifier
        )

        await use_case.execute(order_id, payment_details)

        notifier.notify_payment_received.assert_called_once_with(order_id)
```

## TDD Cycle per Layer

For each layer, follow the 5-step cycle:

0. **REASON** - Identify cases for the current layer, start with the simplest
1. **RED** - Write one failing test for the simplest case
2. **GREEN** - Implement minimum code, follow TPP
3. **REFACTOR** - Clean up while keeping tests green
4. **RE-EVALUATE** - Mark done, pick next simplest, repeat until layer is complete, then move outward

(End of file - total 159 lines)
