# Use Cases Detail

## Structure

```python
from typing import Optional
from orders.domain.services.pricing_service import calculate_discount
from orders.domain.repositories.order_repository import OrderRepository
from orders.domain.repositories.product_repository import ProductRepository
from orders.domain.entities.order import Order
from orders.domain.value_objects.id import Id
from shared.domain.errors import DomainError


class CreateOrderUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository: ProductRepository,
    ) -> None:
        self._order_repository = order_repository
        self._product_repository = product_repository

    async def execute(self, product_id: str, quantity: int) -> dict:
        product = await self._product_repository.find_by_id(Id.create(product_id))
        if product is None:
            raise DomainError.not_found(f"Product {product_id} not found")

        order = Order.create(Id.generate())
        order.add_item(product, quantity)

        discount = calculate_discount(order)
        order.apply_discount(discount)

        await self._order_repository.save(order)
        return self._to_dto(order)

    @staticmethod
    def _to_dto(order: Order) -> dict:
        return order.to_primitives()
```

## Terminal-Friendly Parameters

```python
# WORSE - Complex request object for few parameters
class CreateOrderUseCase:
    async def execute(self, request: dict) -> dict: ...


# BETTER - Primitive parameters (terminal-friendly)
class CreateOrderUseCase:
    async def execute(self, product_id: str, quantity: int) -> dict: ...


# ALSO GOOD - When more than 3 parameters, use a Pydantic request DTO
from pydantic import BaseModel


class CreateInvoiceRequest(BaseModel):
    customer_id: str
    description: str
    amount: float
    currency: str
    due_date: str


class CreateInvoiceUseCase:
    def __init__(self, invoice_repository: InvoiceRepository) -> None:
        self._invoice_repository = invoice_repository

    async def execute(self, request: CreateInvoiceRequest) -> dict:
        customer_id = Id.create(request.customer_id)
        money = Money.create(request.amount, request.currency)
        ...
```

## Single Entry Point

```python
# WORSE - Multiple entry points
class OrderUseCase:
    async def create(self) -> None: ...
    async def update(self) -> None: ...
    async def delete(self) -> None: ...


# BETTER - Single responsibility
class CreateOrderUseCase:
    async def execute(self, product_id: str, quantity: int) -> dict: ...


class UpdateOrderUseCase:
    async def execute(self, order_id: str, quantity: int) -> dict: ...
```

## Dependencies

```python
from typing import Optional
from orders.domain.services.shipping_calculator import calculate_shipping_cost
from orders.domain.repositories.order_repository import OrderRepository
from orders.domain.value_objects.id import Id
from shared.domain.errors import DomainError


class ProcessPaymentUseCase:
    def __init__(
        self,
        order_repository: OrderRepository,
        payment_gateway: PaymentGateway,
    ) -> None:
        self._order_repository = order_repository
        self._payment_gateway = payment_gateway

    async def execute(self, order_id: str, payment_method: str) -> None:
        order = await self._order_repository.find_by_id(Id.create(order_id))
        if order is None:
            raise DomainError.not_found("Order not found")

        shipping_cost = calculate_shipping_cost(order, order.destination)
        total = order.calculate_total().add(shipping_cost)

        await self._payment_gateway.charge(total, payment_method)
        order.mark_as_paid()
        await self._order_repository.save(order)
```
