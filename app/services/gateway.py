import asyncio
import random

from app.config import get_settings


class PaymentGateway:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def process(self) -> bool:
        await asyncio.sleep(random.uniform(2, 5))
        return random.random() < self.settings.payment_success_rate
