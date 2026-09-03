from datetime import datetime, timezone

from app.domain.models.case import (
    MoneyState,
    ReconstructionStatus,
    WorkflowState,
)
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus
from app.services.reconstruction.models import ReconstructionEvent
from app.services.state_engine.engine import run_state_engine
from app.services.state_engine.models import StateInput
from app.services.reconstruction.models import ReconstructionResult


def make_event(
    event_type: str,
    occurred_at: str,
    event_id: str | None = None,
) -> ReconstructionEvent:
    timestamp = datetime.fromisoformat(occurred_at)

    return ReconstructionEvent(
        event_id=event_id or event_type,
        event_type=event_type,
        occurred_at=timestamp,
        received_at=timestamp,
        processed_at=None,
        source="test",
        merchant_id="merchant_1",
        customer_id="customer_1",
        order_id="order_1",
        payment_id="payment_1",
        payload={},
        sequence_hint=None,
    )


def make_result(
    *,
    events=(),
    payment_state=None,
    order_state=None,
    reconstruction_status=ReconstructionStatus.COMPLETE,
    uncertainty=(),
):
    return ReconstructionResult(
        chronological_events=tuple(events),
        payment_state=payment_state,
        order_state=order_state,
        reconstruction_status=reconstruction_status,
        uncertainty=tuple(uncertainty),
    )


def test_captured_and_paid_is_recovered():
    events = (
        make_event("payment.captured", "2026-01-01T10:03:00+00:00"),
        make_event("order.paid", "2026-01-01T10:04:00+00:00"),
    )

    reconstruction = make_result(
        events=events,
        payment_state=PaymentStatus.CAPTURED,
        order_state=OrderStatus.PAID,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.workflow_state == WorkflowState.RECOVERED
    assert result.money_state == MoneyState.RESOLVED
    assert result.mismatch is False
    assert result.requires_verification is False


def test_captured_and_unpaid_is_at_risk():
    events = (
        make_event("payment.captured", "2026-01-01T10:03:00+00:00"),
        make_event("order.unpaid", "2026-01-01T10:04:00+00:00"),
    )

    reconstruction = make_result(
        events=events,
        payment_state=PaymentStatus.CAPTURED,
        order_state=OrderStatus.UNPAID,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.workflow_state == WorkflowState.DECISION_READY
    assert result.money_state == MoneyState.AT_RISK
    assert result.mismatch is True
    assert result.requires_verification is True


def test_conflicted_reconstruction_is_escalated():
    events = (
        make_event("payment.captured", "2026-01-01T10:03:00+00:00"),
        make_event("payment.failed", "2026-01-01T10:04:00+00:00"),
    )

    reconstruction = make_result(
        events=events,
        payment_state=None,
        order_state=OrderStatus.CREATED,
        reconstruction_status=ReconstructionStatus.CONFLICTED,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.workflow_state == WorkflowState.ESCALATED
    assert result.money_state == MoneyState.UNKNOWN
    assert result.requires_verification is True


def test_partial_reconstruction_requires_investigation():
    events = (
        make_event("payment.initiated", "2026-01-01T10:01:00+00:00"),
        make_event("payment.authorized", "2026-01-01T10:02:00+00:00"),
    )

    reconstruction = make_result(
        events=events,
        payment_state=PaymentStatus.AUTHORIZED,
        order_state=OrderStatus.CREATED,
        reconstruction_status=ReconstructionStatus.PARTIAL,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.workflow_state == WorkflowState.INVESTIGATING
    assert result.money_state == MoneyState.UNKNOWN
    assert result.requires_verification is True


def test_failed_payment_is_resolved():
    events = (
        make_event("payment.failed", "2026-01-01T10:03:00+00:00"),
    )

    reconstruction = make_result(
        events=events,
        payment_state=PaymentStatus.FAILED,
        order_state=OrderStatus.CREATED,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.workflow_state == WorkflowState.RESOLVED
    assert result.money_state == MoneyState.RESOLVED
    assert result.requires_verification is False


def test_captured_payment_without_order_state_does_not_invent_mismatch():
    events = (
        make_event("payment.captured", "2026-01-01T10:03:00+00:00"),
    )

    reconstruction = make_result(
        events=events,
        payment_state=PaymentStatus.CAPTURED,
        order_state=None,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.workflow_state == WorkflowState.INVESTIGATING
    assert result.money_state == MoneyState.UNKNOWN
    assert result.mismatch is None
    assert result.requires_verification is True


def test_abandoned_checkout_is_recoverable():
    events = (
        make_event(
            "order.created",
            "2026-01-01T10:00:00+00:00",
        ),
        make_event(
            "checkout.started",
            "2026-01-01T10:01:00+00:00",
        ),
        make_event(
            "checkout.abandoned",
            "2026-01-01T10:02:00+00:00",
        ),
    )

    reconstruction = make_result(
        events=events,
        payment_state=None,
        order_state=OrderStatus.CREATED,
        reconstruction_status=ReconstructionStatus.COMPLETE,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.money_state == MoneyState.RECOVERABLE
    assert result.workflow_state == WorkflowState.DECISION_READY
    assert result.mismatch is None
    assert result.requires_verification is False
    assert "abandoned" in result.explanation.lower()


def test_captured_payment_with_non_paid_order_is_at_risk():
    events = (
        make_event(
            "order.created",
            "2026-01-01T10:00:00+00:00",
        ),
        make_event(
            "payment.initiated",
            "2026-01-01T10:01:00+00:00",
        ),
        make_event(
            "payment.authorized",
            "2026-01-01T10:02:00+00:00",
        ),
        make_event(
            "payment.captured",
            "2026-01-01T10:03:00+00:00",
        ),
    )

    reconstruction = make_result(
        events=events,
        payment_state=PaymentStatus.CAPTURED,
        order_state=OrderStatus.CREATED,
        reconstruction_status=ReconstructionStatus.COMPLETE,
    )

    result = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    assert result.money_state == MoneyState.AT_RISK
    assert result.workflow_state == WorkflowState.DECISION_READY
    assert result.mismatch is True
    assert result.requires_verification is True
    assert "captured" in result.explanation.lower()