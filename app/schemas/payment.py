import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

Currency = Literal["RUB", "USD", "EUR"]


class PaymentCreate(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=19, decimal_places=4)
    currency: Currency
    description: str = Field(min_length=1, max_length=2000)
    metadata: dict[str, Any] = Field(default_factory=dict)
    webhook_url: HttpUrl


class PaymentCreated(BaseModel):
    payment_id: uuid.UUID
    status: Literal["pending", "succeeded", "failed"]
    created_at: datetime


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: uuid.UUID
    amount: Decimal
    currency: Currency
    description: str
    metadata: dict[str, Any] = Field(validation_alias="metadata_")
    status: Literal["pending", "succeeded", "failed"]
    idempotency_key: str
    webhook_url: HttpUrl
    created_at: datetime
    processed_at: datetime | None
