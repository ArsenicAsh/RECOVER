from datetime import datetime, timedelta, timezone

from app.services.reconstruction.chronology import (
    order_events_chronologically,
)
from app.services.reconstruction.models import ReconstructionEvent


def make_event(
    event_id: str,
    event_type: str,
    occurred_at: datetime,
    received_at: datetime,
    sequence_hint: int | None = None,
) -> ReconstructionEvent:
    return ReconstructionEvent(
        event_id=event_id,
        event_type=event_type,
        occurred_at=occurred_at,
        received_at=received_at,
        processed_at=None,
        source="test",
        merchant_id="merchant-1",
        customer_id="customer-1",
        order_id="order-1",
        payment_id="payment-1",
        payload={},
        sequence_hint=sequence_hint,
    )


def test_orders_events_by_occurred_at():
    base = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    captured = make_event(
        "evt-3",
        "payment.captured",
        base + timedelta(minutes=2),
        base + timedelta(minutes=3),
    )

    initiated = make_event(
        "evt-1",
        "payment.initiated",
        base,
        base + timedelta(minutes=1),
    )

    authorized = make_event(
        "evt-2",
        "payment.authorized",
        base + timedelta(minutes=1),
        base + timedelta(minutes=4),
    )

    result = order_events_chronologically(
        [captured, initiated, authorized]
    )

    assert [event.event_id for event in result] == [
        "evt-1",
        "evt-2",
        "evt-3",
    ]


def test_received_at_does_not_determine_chronology():
    base = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    earlier_event = make_event(
        "evt-1",
        "payment.initiated",
        base,
        base + timedelta(minutes=10),
    )

    later_event = make_event(
        "evt-2",
        "payment.captured",
        base + timedelta(minutes=2),
        base + timedelta(minutes=1),
    )

    result = order_events_chronologically(
        [later_event, earlier_event]
    )

    assert [event.event_id for event in result] == [
        "evt-1",
        "evt-2",
    ]


def test_sequence_hint_does_not_determine_chronology():
    base = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)

    first = make_event(
        "evt-1",
        "payment.initiated",
        base,
        base + timedelta(minutes=2),
        sequence_hint=2,
    )

    second = make_event(
        "evt-2",
        "payment.authorized",
        base + timedelta(minutes=1),
        base + timedelta(minutes=1),
        sequence_hint=1,
    )

    result = order_events_chronologically(
        [first, second]
    )

    assert [event.event_id for event in result] == [
        "evt-1",
        "evt-2",
    ]


def test_equal_occurred_at_uses_event_id_as_tie_breaker():
    timestamp = datetime(
        2026,
        1,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    event_b = make_event(
        "evt-b",
        "payment.authorized",
        timestamp,
        timestamp,
    )

    event_a = make_event(
        "evt-a",
        "payment.initiated",
        timestamp,
        timestamp + timedelta(minutes=1),
    )

    result = order_events_chronologically(
        [event_b, event_a]
    )

    assert [event.event_id for event in result] == [
        "evt-a",
        "evt-b",
    ]


def test_chronology_preserves_duplicate_events():
    timestamp = datetime(
        2026,
        1,
        1,
        10,
        0,
        tzinfo=timezone.utc,
    )

    first = make_event(
        "evt-1",
        "payment.initiated",
        timestamp,
        timestamp,
    )

    duplicate = make_event(
        "evt-1",
        "payment.initiated",
        timestamp,
        timestamp + timedelta(minutes=5),
    )

    result = order_events_chronologically(
        [duplicate, first]
    )

    assert len(result) == 2
    assert [event.event_id for event in result] == [
        "evt-1",
        "evt-1",
    ]
