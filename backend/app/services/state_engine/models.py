from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.models.case import (
    MoneyState,
    ReconstructionStatus,
    WorkflowState,
)
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus
from app.services.reconstruction.models import ReconstructionResult


@dataclass(frozen=True)
class StateInput:
    reconstruction: ReconstructionResult


@dataclass(frozen=True)
class StateResult:
    workflow_state: WorkflowState
    money_state: MoneyState
    reconstruction_status: ReconstructionStatus
    payment_status: PaymentStatus | None
    order_status: OrderStatus | None
    mismatch: bool | None
    requires_verification: bool
    evidence_event_ids: tuple[str, ...] = field(default_factory=tuple)
    explanation: str = ""