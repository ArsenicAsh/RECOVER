from datetime import datetime, timezone

from app.services.reconstruction.evidence import (
    EvidenceStatus,
    classify_observed_events,
)
from app.services.reconstruction.models import ReconstructionEvent


def make_event(event_id: str) -> ReconstructionEvent:
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
        received_at=timestamp,
        processed_at=None,
        source="test",
        merchant_id="merchant-1",
        customer_id="customer-1",
        order_id="order-1",
        payment_id="payment-1",
        payload={},
    )


def test_observed_events_are_classified_as_observed():
    events = (
        make_event("evt-1"),
        make_event("evt-2"),
    )

    result = classify_observed_events(events)

    assert [item.status for item in result] == [
        EvidenceStatus.OBSERVED,
        EvidenceStatus.OBSERVED,
    ]


def test_classification_preserves_event_identity():
    event = make_event("evt-1")

    result = classify_observed_events((event,))

    assert result[0].event == event
    assert result[0].event.event_id == "evt-1"


def test_classification_preserves_input_order():
    first = make_event("evt-1")
    second = make_event("evt-2")

    result = classify_observed_events((second, first))

    assert [item.event.event_id for item in result] == [
        "evt-2",
        "evt-1",
    ]


def test_observed_classification_has_explicit_explanation():
    event = make_event("evt-1")

    result = classify_observed_events((event,))

    assert result[0].explanation == (
        "Event is directly present in observed evidence."
    )