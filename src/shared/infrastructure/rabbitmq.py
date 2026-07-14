from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import aio_pika

from src.shared.infrastructure.settings import RabbitMQSettings


async def create_rabbitmq_connection(
    settings: RabbitMQSettings | None = None,
) -> aio_pika.RobustConnection:
    """Create a shared RabbitMQ connection.

    This function lives in infrastructure and MUST NOT be imported
    by domain or application layers.
    """
    if settings is None:
        settings = RabbitMQSettings()
    return await aio_pika.connect_robust(settings.rabbitmq_url)


@asynccontextmanager
async def get_rabbitmq_channel(
    connection: aio_pika.RobustConnection,
) -> AsyncIterator[aio_pika.Channel]:
    """Yield a RabbitMQ channel from the connection."""
    async with connection.channel() as channel:
        yield channel
