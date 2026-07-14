"""RabbitMQ worker entrypoint for asynchronous document processing."""

import asyncio
import json
import uuid

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from src.document_processing.application.use_cases import ProcessStudyDocumentUseCase


class DocumentProcessingWorker:
    """Consumes RabbitMQ messages and processes study documents."""

    QUEUE_NAME = "document_processing"

    def __init__(
        self,
        connection: aio_pika.RobustConnection,
        process_use_case: ProcessStudyDocumentUseCase,
    ) -> None:
        self._connection = connection
        self._process_use_case = process_use_case

    async def start(self) -> None:
        """Start consuming messages from the processing queue."""
        async with self._connection.channel() as channel:
            await channel.declare_queue(self.QUEUE_NAME, durable=True)
            await channel.set_qos(prefetch_count=1)

            async def on_message(message: AbstractIncomingMessage) -> None:
                async with message.process(ignore_processed=True):
                    try:
                        body = json.loads(message.body.decode())
                        job_id = uuid.UUID(body["job_id"])
                        await self._process_use_case.execute(job_id=job_id)
                        await message.ack()
                    except Exception:
                        await message.reject(requeue=False)

            queue = await channel.get_queue(self.QUEUE_NAME)
            await queue.consume(on_message)

            try:
                await asyncio.Future()
            except asyncio.CancelledError:
                pass
