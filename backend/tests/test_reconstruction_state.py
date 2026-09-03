from datetime import datetime, timezone

from app.domain.models.case import ReconstructionStatus
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus
from app.services.reconstruction.models import ReconstructionEvent
from app.services.reconstruction.state import (
    reconstruct_order_state,
    reconstruct_payment_state,
    reconstruct_state,
)


def make_event(
    event_id: str,
    event_type: str,
    occurred_at: datetime,
    *,
    payment_id: str | None = "pay_1",
    order_id: str | None = "order_1",
) -> ReconstructionEvent:
    return ReconstructionEvent(
        event_id=event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        received_at=occurred_at,
        processed_at=None,
        source="test",
        merchant_id="merchant_1",
        customer_id="customer_1",
        order_id=order_id,
        payment_id=payment_id,
        payload={},
    )


def test_reconstruct_payment_state_from_chronological_events():
    events = (
        make_event(
            "evt_1",
            "payment.initiated",
            datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        ),
        make_event(
            "evt_2",
            "payment.authorized",
            datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        ),
        make_event(
            "evt_3",
            "payment.captured",
            datetime(2026, 1, 1, 10, 2, tzinfo=timezone.utc),
        ),
    )

    assert reconstruct_payment_state(events) == PaymentStatus.CAPTURED


def test_reconstruct_failed_payment_state():
    events = (
        make_event(
            "evt_1",
            "payment.initiated",
            datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        ),
        make_event(
            "evt_2",
            "payment.failed",
            datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        ),
    )

    assert reconstruct_payment_state(events) == PaymentStatus.FAILED


def test_reconstruct_order_state_only_from_order_events():
    events = (
        make_event(
            "evt_1",
            "order.created",
            datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
            payment_id=None,
        ),
        make_event(
            "evt_2",
            "payment.captured",
            datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        ),
    )

    assert reconstruct_order_state(events) == OrderStatus.CREATED


def test_missing_terminal_payment_outcome_is_partial():
    events = (
        make_event(
            "evt_1",
            "payment.initiated",
            datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        ),
        make_event(
            "evt_2",
            "payment.authorized",
            datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        ),
    )

    (
        payment_state,
        order_state,
        reconstruction_status,
        uncertainty,
    ) = reconstruct_state(
        events,
        has_contradictions=False,
        has_missing_expected_evidence=True,
    )

    assert payment_state == PaymentStatus.AUTHORIZED
    assert order_state is None
    assert reconstruction_status == ReconstructionStatus.PARTIAL
    assert "Expected payment terminal outcome was not observed." in uncertainty


def test_contradictory_payment_evidence_is_not_resolved():
    events = (
        make_event(
            "evt_1",
            "payment.initiated",
            datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        ),
        make_event(
            "evt_2",
            "payment.captured",
            datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc),
        ),
        make_event(
            "evt_3",
            "payment.failed",
            datetime(2026, 1, 1, 10, 2, tzinfo=timezone.utc),
        ),
    )

    (
        payment_state,
        order_state,
        reconstruction_status,
        uncertainty,
    ) = reconstruct_state(
        events,
        has_contradictions=True,
        has_missing_expected_evidence=False,
    )

    assert payment_state is None
    assert order_state is None
    assert reconstruction_status == ReconstructionStatus.CONFLICTED
    assert (
        "Conflicting payment evidence prevents a definitive payment state."
        in uncertainty
    )