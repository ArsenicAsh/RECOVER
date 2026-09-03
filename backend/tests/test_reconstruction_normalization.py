from datetime import datetime, timezone

from app.services.dataset_generator.models import ObservedEvent

from app.services.reconstruction.normalization import normalize_observed_events


def make_observed_event(
    event_id: str,
    event_type: str,
    occurred_at: datetime,
    received_at: datetime,
) -> ObservedEvent:
    return ObservedEvent(
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
        payload={"test": True},
        sequence_hint=None,
    )


def test_normalization_preserves_event_fields():
    occurred_at = datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)
    received_at = datetime(2026, 1, 1, 10, 1, tzinfo=timezone.utc)

    event = make_observed_event(
        event_id="evt-1",
        event_type="payment.initiated",
        occurred_at=occurred_at,
        received_at=received_at,
    )

    result = normalize_observed_events([event])

    assert len(result) == 1

    normalized = result[0]

    assert normalized.event_id == "evt-1"
    assert normalized.event_type == "payment.initiated"
    assert normalized.occurred_at == occurred_at
    assert normalized.received_at == received_at
    assert normalized.processed_at is None
    assert normalized.source == "test"
    assert normalized.merchant_id == "merchant-1"
    assert normalized.customer_id == "customer-1"
    assert normalized.order_id == "order-1"
    assert normalized.payment_id == "payment-1"
    assert normalized.payload == {"test": True}


def test_normalization_preserves_input_order():
    first = make_observed_event(
        "evt-1",
        "payment.captured",
        datetime(2026, 1, 1, 10, 2, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 3, tzinfo=timezone.utc),
    )

    second = make_observed_event(
        "evt-2",
        "payment.initiated",
        datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        datetime(2026, 1, 1, 10, 4, tzinfo=timezone.utc),
    )

    result = normalize_observed_events([first, second])

    assert [event.event_id for event in result] == [
        "evt-1",
        "evt-2",
    ]

    assert [event.event_type for event in result] == [
        "payment.captured",
        "payment.initiated",
    ]


def test_normalization_preserves_sequence_hint_without_using_it():
    event = ObservedEvent(
        event_id="evt-1",
        event_type="payment.authorized",
        occurred_at=datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc),
        received_at=datetime(2026, 1, 1, 10, 5, tzinfo=timezone.utc),
        processed_at=None,
        source="test",
        merchant_id="merchant-1",
        customer_id="customer-1",
        order_id="order-1",
        payment_id="payment-1",
        payload={},
        sequence_hint=99,
    )

    result = normalize_observed_events([event])

    assert result[0].sequence_hint == 99