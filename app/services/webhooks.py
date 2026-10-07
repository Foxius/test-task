import httpx

from app.config import get_settings


class WebhookClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def send(self, url: str, payload: dict) -> None:
        async with httpx.AsyncClient(timeout=self.settings.webhook_timeout_seconds) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
