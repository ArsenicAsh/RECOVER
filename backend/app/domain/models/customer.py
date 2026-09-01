from typing import Any
import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Customer(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customers"
    __table_args__ = (
        UniqueConstraint("merchant_id", "external_ref", name="uq_customer_merchant_external_ref"),
    )

    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    external_ref: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(64))
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB)

    merchant = relationship("Merchant", back_populates="customers")
    orders = relationship("Order", back_populates="customer")
    payments = relationship("Payment", back_populates="customer")
    events = relationship("Event", back_populates="customer")
    cases = relationship("Case", back_populates="customer")
