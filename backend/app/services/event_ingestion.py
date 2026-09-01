from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.event import Event
from app.domain.schemas.event import EventCreate


async def ingest_event(
    db: AsyncSession,
    event_data: EventCreate,
) -> tuple[Event, bool]:
    received_at = datetime.now(timezone.utc)

    event = Event(
        event_id=event_data.event_id,
        event_type=event_data.event_type,
        merchant_id=event_data.merchant_id,
        payment_id=event_data.payment_id,
        order_id=event_data.order_id,
        customer_id=event_data.customer_id,
        occurred_at=event_data.occurred_at,
        received_at=received_at,
        processed_at=None,
        source=event_data.source,
        payload=event_data.payload,
        sequence_hint=event_data.sequence_hint,
    )

    db.add(event)

    try:
        await db.commit()
        await db.refresh(event)
        return event, False

    except IntegrityError:
        await db.rollback()

        result = await db.execute(
            select(Event).where(
                Event.merchant_id == event_data.merchant_id,
                Event.source == event_data.source,
                Event.event_id == event_data.event_id,
            )
        )

        existing_event = result.scalar_one_or_none()

        if existing_event is None:
            raise

        return existing_event, True