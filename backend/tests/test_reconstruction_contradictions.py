from datetime import datetime, timedelta, timezone

from app.services.reconstruction.contradictions import (
    find_contradictions,
)
from app.services.reconstruction.models import ReconstructionEvent


def make_event(
    event_id: str,
    event_type: str,
    payment_id: str = "payment-1",
    offset: int = 0,
) -> ReconstructionEvent:
    timestamp = datetime(
        2026,
        1,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    return ReconstructionEvent(
        event_id=event_id,
        event_type=event_type,
        occurred_at=timestamp + timedelta(minutes=offset),
        received_at=timestamp + timedelta(minutes=offset),
        processed_at=None,
        source="test",
        merchant_id="merchant-1",
        customer_id="customer-1",
        order_id="order-1",
        payment_id=payment_id,
        payload={},
    )


def test_detects_captured_and_failed_contradiction():
    events = (
        make_event("evt-captured", "payment.captured", offset=2),
        make_event("evt-failed", "payment.failed", offset=3),
    )

    result = find_contradictions(events)

    assert len(result) == 1
    assert result[0].event_ids == (
        "evt-captured",
        "evt-failed",
    )


def test_does_not_flag_consistent_captured_payment():
    events = (
        make_event("evt-initiated", "payment.initiated"),
        make_event("evt-authorized", "payment.authorized", offset=1),
        make_event("evt-captured", "payment.captured", offset=2),
    )

    result = find_contradictions(events)

    assert result == ()


def test_does_not_flag_consistent_failed_payment():
    events = (
        make_event("evt-initiated", "payment.initiated"),
        make_event("evt-failed", "payment.failed", offset=1),
    )

    result = find_contradictions(events)

    assert result == ()


def test_contradictions_are_scoped_to_same_payment():
    events = (
        make_event(
            "evt-captured",
            "payment.captured",
            payment_id="payment-1",
        ),
        make_event(
            "evt-failed",
            "payment.failed",
            payment_id="payment-2",
        ),
    )

    result = find_contradictions(events)

    assert result == ()


def test_contradiction_detection_does_not_remove_evidence():
    events = (
        make_event("evt-captured", "payment.captured"),
        make_event("evt-failed", "payment.failed", offset=1),
    )

    original_ids = [event.event_id for event in events]

    find_contradictions(events)

    assert [event.event_id for event in events] == original_ids


def test_contradiction_detection_is_deterministic():
    events = (
        make_event("evt-z", "payment.failed", offset=2),
        make_event("evt-a", "payment.captured", offset=1),
    )

    result = find_contradictions(events)

    assert result[0].event_ids == (
        "evt-a",
        "evt-z",
    )