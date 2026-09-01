from typing import Any

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class Merchant(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    metadata_: Mapped[dict[str, Any] | None] = mapped_column("metadata", JSONB, nullable=True)

    customers = relationship("Customer", back_populates="merchant")
    orders = relationship("Order", back_populates="merchant")
    payments = relationship("Payment", back_populates="merchant")
    events = relationship("Event", back_populates="merchant")
    cases = relationship("Case", back_populates="merchant")
