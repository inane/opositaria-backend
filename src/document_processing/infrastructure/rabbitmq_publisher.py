"""RabbitMQ publisher adapter for document processing requests."""

import json
import uuid

import aio_pika

from src.shared.infrastructure.rabbitmq import get_rabbitmq_channel


class RabbitMQProcessingPublisher:
    """Publishes document processing requests to a RabbitMQ queue."""

    QUEUE_NAME = "document_processing"

    def __init__(self, connection: aio_pika.RobustConnection) -> None:
        self._connection = connection

    async def publish(self, document_id: uuid.UUID, job_id: uuid.UUID) -> None:
        """Publish a processing request containing document and job identifiers."""
        async with get_rabbitmq_channel(self._connection) as channel:
            await channel.declare_queue(self.QUEUE_NAME, durable=True)
            message = aio_pika.Message(
                body=json.dumps(
                    {
                        "document_id": str(document_id),
                        "job_id": str(job_id),
                    }
                ).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            )
            await channel.default_exchange.publish(message, routing_key=self.QUEUE_NAME)
