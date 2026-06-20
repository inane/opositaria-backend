# Error Handling

## DomainError with Factory Methods

Use a single `DomainError` class with factory methods.

```python
class DomainError(Exception):
    def __init__(self, type_: str, message: str) -> None:
        super().__init__(message)
        self.type = type_
        self.message = message

    @classmethod
    def create_not_found(cls, message: str) -> 'DomainError':
        return cls('notFound', message)

    @classmethod
    def create_validation(cls, message: str) -> 'DomainError':
        return cls('validation', message)

    @classmethod
    def create(cls, message: str) -> 'DomainError':
        return cls('other', message)
```

## Error Types

| Factory Method        | Type       | Use                               |
| --------------------- | ---------- | --------------------------------- |
| `create_not_found()`  | notFound   | Entity does not exist             |
| `create_validation()` | validation | Invariant violated, invalid state |
| `create()`            | other      | Other domain errors               |

## Usage Examples

### In Value Objects (invariants in factory)

```python
class PositiveNumber:
    def __init__(self, value: int) -> None:
        self.value = value

    @classmethod
    def create(cls, value: int) -> 'PositiveNumber':
        if value <= 0:
            raise DomainError.create_validation('Quantity must be positive')
        return cls(value)
```

### In Entities (invariants in factory or methods)

```python
class Order:
    def add_item(self, product: Product, quantity: PositiveNumber) -> None:
        if self.status != OrderStatus.DRAFT:
            raise DomainError.create_validation('Cannot modify a confirmed order')
        # ... add item
```

### In Use Cases (not found)

```python
class CreateOrderUseCase:
    async def execute(self, product_id: str) -> OrderDTO:
        product = await self.product_repository.find_by_id(Id.create(product_id))
        if product is None:
            raise DomainError.create_not_found(f'Product {product_id} not found')
        # ... create order
```

## Domain Errors vs Technical Errors

| Type      | Examples                      | Handling                                 |
| --------- | ----------------------------- | ---------------------------------------- |
| Domain    | not found, validation failed  | Catch and return appropriate HTTP status |
| Technical | DB connection failed, timeout | Let bubble up, log, return 500           |

## Error Messages

### Include

- Human-readable description
- Relevant context (IDs, values)

### Never Include

- Stack traces
- Internal implementation details
- Database table names
- File paths

```python
# GOOD
raise DomainError.create_not_found(f'Product {product_id} not found')

# BAD - Exposes internals
raise DomainError.create_not_found("Product not found in 'products' (OrderRepository.find_by_id)")
```

## When to Throw

### Throw for:

- Invariant violations (business rules broken)
- Entity not found (when required for operation)
- Invalid state transitions
- Validation failures

### Do not throw for:

- Optional values (return `None`)
- Expected empty results (return empty list)

```python
# Throw - entity must exist for operation
order = await self.order_repository.find_by_id(order_id)
if order is None:
    raise DomainError.create_not_found(f'Order {order_id} not found')

# Return Optional - querying is not an error
async def find_by_id(self, id: Id) -> Order | None:
    return self.orders.get(id.value)

# Return empty list - no results is valid
async def find_by_customer(self, customer_id: Id) -> list[Order]:
    return [o for o in self.orders if o.customer_id == customer_id]
```
