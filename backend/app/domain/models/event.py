import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint(
            "merchant_id",
            "source",
            "event_id",
            name="uq_event_merchant_source_event_id",
        ),
        Index("ix_events_merchant_occurred_at", "merchant_id", "occurred_at"),
        Index("ix_events_payment_occurred_at", "payment_id", "occurred_at"),
        Index("ix_events_order_occurred_at", "order_id", "occurred_at"),
    )

    event_id: Mapped[str] = mapped_column(String(255), nullable=False)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payments.id"))
    order_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("orders.id"))
    customer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("customers.id"))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    sequence_hint: Mapped[int | None] = mapped_column(Integer)

    merchant = relationship("Merchant", back_populates="events")
    payment = relationship("Payment", back_populates="events")
    order = relationship("Order", back_populates="events")
    customer = relationship("Customer", back_populates="events")
