import asyncio

import aio_pika

from app.config import get_settings


async def declare() -> None:
    connection = await aio_pika.connect(get_settings().rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        dead_letter_exchange = await channel.declare_exchange(
            "payments.dlx", aio_pika.ExchangeType.DIRECT, durable=True
        )
        await channel.declare_queue("payments.new.dlq", durable=True)
        payments_exchange = await channel.declare_exchange(
            "payments", aio_pika.ExchangeType.DIRECT, durable=True
        )
        payments_queue = await channel.declare_queue(
            "payments.new",
            durable=True,
            arguments={
                "x-dead-letter-exchange": "payments.dlx",
                "x-dead-letter-routing-key": "payments.new",
            },
        )
        dead_letter_queue = await channel.get_queue("payments.new.dlq")
        await dead_letter_queue.bind(dead_letter_exchange, routing_key="payments.new")
        await payments_queue.bind(payments_exchange, routing_key="payments.new")


if __name__ == "__main__":
    asyncio.run(declare())
