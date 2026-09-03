from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from app.domain.models.case import ReconstructionStatus
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus


@dataclass(frozen=True)
class ReconstructionEvent:
    """
    Normalized event representation consumed by the reconstruction engine.

    This is an internal service-layer projection of an observed event.
    It deliberately does not represent ground truth.
    """

    event_id: str
    event_type: str
    occurred_at: datetime
    received_at: datetime
    processed_at: datetime | None
    source: str
    merchant_id: str
    customer_id: str | None
    order_id: str | None
    payment_id: str | None
    payload: dict[str, Any]
    sequence_hint: int | None = None


@dataclass(frozen=True)
class InferredTransition:
    """
    A state transition inferred from observed evidence.

    The reconstruction engine must be able to explain why
    the transition was inferred.
    """

    entity: str
    from_state: str | None
    to_state: str
    evidence_event_ids: tuple[str, ...]
    explanation: str


@dataclass(frozen=True)
class Contradiction:
    """
    Represents conflicting observed evidence.

    Contradictions are preserved rather than silently resolved.
    """

    event_ids: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class ReconstructionResult:
    """
    Complete deterministic reconstruction output.

    This result is derived exclusively from observed evidence.
    Ground truth must never be supplied to the reconstruction engine.
    """

    chronological_events: tuple[ReconstructionEvent, ...] = field(default_factory=tuple)

    duplicate_event_ids: tuple[str, ...] = field(default_factory=tuple)

    inferred_transitions: tuple[InferredTransition, ...] = field(default_factory=tuple)

    missing_expected_evidence: tuple[str, ...] = field(default_factory=tuple)

    contradictions: tuple[Contradiction, ...] = field(default_factory=tuple)

    relevant_evidence: tuple[str, ...] = field(default_factory=tuple)

    payment_state: PaymentStatus | None = None
    order_state: OrderStatus | None = None

    reconstruction_status: ReconstructionStatus = ReconstructionStatus.PENDING

    confidence: float | None = None
    uncertainty: tuple[str, ...] = field(default_factory=tuple)

    explanation: str = ""