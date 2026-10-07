from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "postgresql+asyncpg://payments:payments@postgres:5432/payments"
    rabbitmq_url: str = "amqp://payments:payments@rabbitmq:5672/"
    api_key: str = Field(default="test-api-key", alias="API_KEY")
    payment_success_rate: float = 0.9
    webhook_timeout_seconds: float = 10.0
    environment: str = "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
