from datetime import datetime, timedelta, timezone

from app.services.reconstruction.duplicates import (
    find_duplicate_event_ids,
)
from app.services.reconstruction.models import ReconstructionEvent


def make_event(
    event_id: str,
    received_offset: int = 0,
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
        event_type="payment.initiated",
        occurred_at=timestamp,
        received_at=timestamp + timedelta(minutes=received_offset),
        processed_at=None,
        source="test",
        merchant_id="merchant-1",
        customer_id="customer-1",
        order_id="order-1",
        payment_id="payment-1",
        payload={},
    )


def test_finds_duplicate_event_ids():
    events = [
        make_event("evt-1"),
        make_event("evt-2"),
        make_event("evt-1", received_offset=5),
    ]

    result = find_duplicate_event_ids(events)

    assert result == ("evt-1",)


def test_returns_empty_tuple_when_no_duplicates_exist():
    events = [
        make_event("evt-1"),
        make_event("evt-2"),
        make_event("evt-3"),
    ]

    result = find_duplicate_event_ids(events)

    assert result == ()


def test_duplicate_detection_is_deterministic():
    events = [
        make_event("evt-z"),
        make_event("evt-a"),
        make_event("evt-z", received_offset=1),
        make_event("evt-a", received_offset=2),
    ]

    result = find_duplicate_event_ids(events)

    assert result == ("evt-a", "evt-z")


def test_duplicate_detection_preserves_original_events():
    events = [
        make_event("evt-1"),
        make_event("evt-1", received_offset=5),
    ]

    original_ids = [event.event_id for event in events]

    find_duplicate_event_ids(events)

    assert [event.event_id for event in events] == original_ids