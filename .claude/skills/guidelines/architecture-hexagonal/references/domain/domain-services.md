# Domain Services

Domain Services contain business logic that does not naturally belong to a specific entity or value object. They are
stateless functions that operate on domain objects.

## When to Use

Use a Domain Service when:

- The logic involves multiple entities
- The logic does not naturally belong to any single entity
- A business rule spans aggregates

## Characteristics

- **Stateless**: Pure functions, the same input always produces the same output
- **Domain language**: Named using domain terminology
- **Pure domain logic**: No infrastructure concerns (no DB, no HTTP)
- **Operates on domain objects**: Receives and returns entities/value objects

## Structure

Domain services are module-level functions (not classes). Group related functions in a module.

```python
# src/orders/domain/services/pricing_service.py
from orders.domain.entities.order import Order
from orders.domain.value_objects.money import Money
from orders.domain.value_objects.discount import Discount


def calculate_order_total(order: Order, discounts: list[Discount]) -> Money:
    subtotal = order.calculate_subtotal()
    applicable_discounts = [d for d in discounts if d.applies_to(order)]
    total = subtotal
    for discount in applicable_discounts:
        total = discount.apply(total)
    return total


def apply_volume_discount(order: Order) -> Money:
    volume_threshold = 10
    discount_percentage = 0.1

    if order.total_quantity() >= volume_threshold:
        return order.calculate_subtotal().multiply(discount_percentage)
    return Money.zero()
```

## Domain Service vs Use Case

| Domain Service                  | Use Case                                     |
|---------------------------------|----------------------------------------------|
| Pure functions                  | Orchestrates application flow                |
| No external dependencies        | Uses ports (repositories, external services) |
| Lives in `domain/services/`     | Lives in `application/`                      |
| Called by entities or use cases | Entry point from infrastructure              |

```python
# Domain Service - pure function
# src/orders/domain/services/pricing_service.py
def calculate_discount(order: Order) -> Money: ...


# Use Case - orchestrates and uses ports
# src/orders/application/create_order_use_case.py
from orders.domain.services.pricing_service import calculate_discount


class CreateOrderUseCase:
    def __init__(self, order_repository: OrderRepository) -> None:
        self._order_repository = order_repository

    async def execute(self, product_id: str, quantity: int) -> Order:
        order = Order.create(...)
        discount = calculate_discount(order)
        order.apply_discount(discount)
        await self._order_repository.save(order)
        return order
```
