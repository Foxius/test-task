import asyncio
import logging
from datetime import UTC, datetime

from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from sqlalchemy import select, update

from app.config import get_settings
from app.db import SessionFactory
from app.models import OutboxEvent, OutboxStatus

logger = logging.getLogger(__name__)
settings = get_settings()
broker = RabbitBroker(settings.rabbitmq_url)

payments_queue = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={"x-dead-letter-exchange": "payments.dlx", "x-dead-letter-routing-key": "payments.new"},
)
payments_exchange = RabbitExchange("payments", durable=True)


async def run_relay(batch_size: int = 100, interval_seconds: float = 1.0) -> None:
    async with broker:
        while True:
            async with SessionFactory() as session:
                result = await session.execute(
                    select(OutboxEvent)
                    .where(OutboxEvent.status == OutboxStatus.pending)
                    .order_by(OutboxEvent.created_at)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
                events = result.scalars().all()
                for event in events:
                    event.status = OutboxStatus.processing
                await session.commit()

                for event in events:
                    try:
                        await broker.publish(event.payload, queue=payments_queue, exchange=payments_exchange)
                        await session.execute(
                            update(OutboxEvent)
                            .where(OutboxEvent.id == event.id)
                            .values(status=OutboxStatus.sent, processed_at=datetime.now(UTC))
                        )
                        await session.commit()
                    except Exception as error:
                        event.retry_count += 1
                        event.last_error = str(error)
                        event.status = OutboxStatus.failed if event.retry_count >= 3 else OutboxStatus.pending
                        await session.commit()
                        logger.exception("Outbox event %s failed", event.id)

            await asyncio.sleep(interval_seconds)


if __name__ == "__main__":
    asyncio.run(run_relay())
