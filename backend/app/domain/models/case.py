import enum
import uuid

from sqlalchemy import CheckConstraint, Enum, ForeignKey, Integer, String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


class ScenarioType(str, enum.Enum):
    ABANDONED_CHECKOUT = "ABANDONED_CHECKOUT"
    AMBIGUOUS_PAYMENT = "AMBIGUOUS_PAYMENT"
    ORDER_PAYMENT_MISMATCH = "ORDER_PAYMENT_MISMATCH"


class WorkflowState(str, enum.Enum):
    DETECTED = "DETECTED"
    INVESTIGATING = "INVESTIGATING"
    RECONSTRUCTED = "RECONSTRUCTED"
    DECISION_READY = "DECISION_READY"
    AWAITING_PERMISSION = "AWAITING_PERMISSION"
    ACTION_PENDING = "ACTION_PENDING"
    ACTION_EXECUTING = "ACTION_EXECUTING"
    VERIFYING = "VERIFYING"
    RECOVERED = "RECOVERED"
    RESOLVED = "RESOLVED"
    ESCALATED = "ESCALATED"
    BLOCKED = "BLOCKED"


class MoneyState(str, enum.Enum):
    SAFE = "SAFE"
    AT_RISK = "AT_RISK"
    RECOVERABLE = "RECOVERABLE"
    UNKNOWN = "UNKNOWN"
    RESOLVED = "RESOLVED"


class ReconstructionStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    CONFLICTED = "CONFLICTED"


class Case(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cases"
    __table_args__ = (
        CheckConstraint("amount > 0", name="ck_case_amount_positive"),
        CheckConstraint(
            "(risk_score IS NULL OR (risk_score >= 0 AND risk_score <= 1))",
            name="ck_case_risk_score",
        ),
        CheckConstraint(
            "(recovery_probability IS NULL OR (recovery_probability >= 0 AND recovery_probability <= 1))",
            name="ck_case_recovery_probability",
        ),
        CheckConstraint(
            "(decision_confidence IS NULL OR (decision_confidence >= 0 AND decision_confidence <= 1))",
            name="ck_case_decision_confidence",
        ),
        CheckConstraint(
            "(expected_recovery IS NULL OR expected_recovery >= 0)",
            name="ck_case_expected_recovery",
        ),
    )

    case_number: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    merchant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("merchants.id"), nullable=False)
    scenario_type: Mapped[ScenarioType] = mapped_column(
        Enum(ScenarioType, name="scenario_type"),
        nullable=False,
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("customers.id"), nullable=False)
    order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("orders.id"), nullable=False)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("payments.id"))
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    workflow_state: Mapped[WorkflowState] = mapped_column(
        Enum(WorkflowState, name="workflow_state"),
        nullable=False,
    )
    money_state: Mapped[MoneyState] = mapped_column(
        Enum(MoneyState, name="money_state"),
        nullable=False,
    )
    reconstruction_status: Mapped[ReconstructionStatus] = mapped_column(
        Enum(ReconstructionStatus, name="reconstruction_status"),
        nullable=False,
    )
    risk_score: Mapped[float | None] = mapped_column(Float)
    recovery_probability: Mapped[float | None] = mapped_column(Float)
    expected_recovery: Mapped[int | None] = mapped_column(Integer)
    recommended_action: Mapped[str | None] = mapped_column(String(64))
    decision_confidence: Mapped[float | None] = mapped_column(Float)

    merchant = relationship("Merchant", back_populates="cases")
    customer = relationship("Customer", back_populates="cases")
    order = relationship("Order", back_populates="cases")
    payment = relationship("Payment", back_populates="cases")
