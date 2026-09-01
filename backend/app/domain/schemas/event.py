import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EventCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1, max_length=255)
    event_type: str = Field(min_length=1, max_length=128)
    merchant_id: uuid.UUID
    payment_id: uuid.UUID | None = None
    order_id: uuid.UUID | None = None
    customer_id: uuid.UUID | None = None
    occurred_at: datetime
    source: str = Field(min_length=1, max_length=32)
    payload: dict[str, Any]
    sequence_hint: int | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    event_id: str
    event_type: str
    merchant_id: uuid.UUID
    payment_id: uuid.UUID | None
    order_id: uuid.UUID | None
    customer_id: uuid.UUID | None
    occurred_at: datetime
    received_at: datetime
    processed_at: datetime | None
    source: str
    payload: dict[str, Any]
    sequence_hint: int | None