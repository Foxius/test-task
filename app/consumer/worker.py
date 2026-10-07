import logging
import uuid
from datetime import UTC, datetime

import asyncio
from faststream import BaseMiddleware, FastStream, Logger
from faststream.rabbit import RabbitBroker, RabbitExchange, RabbitQueue
from sqlalchemy import select, update

from app.config import get_settings
from app.db import SessionFactory
from app.models import OutboxEvent, OutboxStatus, Payment, PaymentStatus
from app.services import PaymentGateway, WebhookClient

logger = logging.getLogger(__name__)
settings = get_settings()

dead_letter_exchange = RabbitExchange("payments.dlx", durable=True)
dead_letter_queue = RabbitQueue("payments.new.dlq", durable=True)
payments_queue = RabbitQueue(
    "payments.new",
    durable=True,
    arguments={
        "x-dead-letter-exchange": "payments.dlx",
        "x-dead-letter-routing-key": "payments.new",
    },
)
payments_exchange = RabbitExchange("payments", durable=True)

class ExponentialRetryMiddleware(BaseMiddleware):
    max_attempts = 3

    async def consume_scope(self, call_next, msg) -> object:
        for attempt in range(self.max_attempts):
            try:
                return await call_next(msg)
            except Exception:
                if attempt == self.max_attempts - 1:
                    raise
                await asyncio.sleep(2**attempt)
        return None


broker = RabbitBroker(settings.rabbitmq_url, middlewares=[ExponentialRetryMiddleware])
app = FastStream(broker)


def build_payload(payment: Payment) -> dict:
    return {
        "payment_id": str(payment.id),
        "status": payment.status.value,
        "amount": str(payment.amount),
        "currency": payment.currency,
        "description": payment.description,
        "metadata": payment.metadata_,
        "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
    }


@broker.subscriber(
    queue=payments_queue,
    exchange=payments_exchange,
    retry=True,
)
async def process_payment(message: dict, logger: Logger) -> None:
    payment_id = uuid.UUID(str(message.get("payment_id")))
    gateway = PaymentGateway()
    webhook = WebhookClient()

    async with SessionFactory() as session:
        result = await session.execute(select(Payment).where(Payment.id == payment_id))
        payment = result.scalar_one()
        succeeded = await gateway.process()
        payment.status = PaymentStatus.succeeded if succeeded else PaymentStatus.failed
        payment.processed_at = datetime.now(UTC)
        await session.commit()

        try:
            await webhook.send(payment.webhook_url, build_payload(payment))
        except Exception:
            await session.rollback()
            raise

        await session.execute(
            update(OutboxEvent)
            .where(OutboxEvent.aggregate_id == payment.id)
            .values(status="sent", processed_at=datetime.now(UTC))
        )
        await session.commit()
