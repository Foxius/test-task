import uuid

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import validate_api_key
from app.db.base import get_session
from app.models import OutboxEvent, Payment, PaymentStatus
from app.schemas import PaymentCreate, PaymentCreated, PaymentResponse

router = APIRouter(prefix="/api/v1/payments", tags=["payments"], dependencies=[Depends(validate_api_key)])


@router.post("", response_model=PaymentCreated, status_code=status.HTTP_202_ACCEPTED)
async def create_payment(
    payload: PaymentCreate,
    idempotency_key: str = Header(alias="Idempotency-Key", min_length=1, max_length=255),
    session: AsyncSession = Depends(get_session),
) -> PaymentCreated:
    async with session.begin():
        existing = await session.execute(select(Payment).where(Payment.idempotency_key == idempotency_key))
        payment = existing.scalar_one_or_none()
        if payment is None:
            payment = Payment(
                amount=payload.amount,
                currency=payload.currency,
                description=payload.description,
                metadata_=payload.metadata,
                webhook_url=str(payload.webhook_url),
                idempotency_key=idempotency_key,
                status=PaymentStatus.pending,
            )
            session.add(payment)
            await session.flush()
            session.add(OutboxEvent(
                aggregate_type="payment",
                event_type="payment.created",
                aggregate_id=payment.id,
                payload={
                    "payment_id": str(payment.id),
                    "idempotency_key": idempotency_key,
                    "webhook_url": str(payload.webhook_url),
                },
            ))

    return PaymentCreated(payment_id=payment.id, status=payment.status, created_at=payment.created_at)


@router.get("/{payment_id}", response_model=PaymentResponse)
async def get_payment(payment_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Payment:
    result = await session.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if payment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment
