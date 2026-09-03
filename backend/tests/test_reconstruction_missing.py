from datetime import datetime, timedelta, timezone

from app.services.reconstruction.missing import (
    find_missing_expected_evidence,
)
from app.services.reconstruction.models import ReconstructionEvent


def make_event(
    event_id: str,
    event_type: str,
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
        payment_id="payment-1",
        payload={},
    )


def test_detects_missing_terminal_payment_evidence():
    events = (
        make_event("evt-1", "order.created"),
        make_event("evt-2", "payment.initiated", 1),
        make_event("evt-3", "payment.authorized", 2),
    )

    result = find_missing_expected_evidence(events)

    assert result == ("payment.terminal_outcome",)


def test_does_not_report_missing_terminal_evidence_when_payment_captured():
    events = (
        make_event("evt-1", "payment.initiated"),
        make_event("evt-2", "payment.authorized", 1),
        make_event("evt-3", "payment.captured", 2),
    )

    result = find_missing_expected_evidence(events)

    assert result == ()


def test_does_not_report_missing_terminal_evidence_when_payment_failed():
    events = (
        make_event("evt-1", "payment.initiated"),
        make_event("evt-2", "payment.failed", 1),
    )

    result = find_missing_expected_evidence(events)

    assert result == ()


def test_missing_evidence_does_not_infer_payment_failure():
    events = (
        make_event("evt-1", "payment.initiated"),
        make_event("evt-2", "payment.authorized", 1),
    )

    result = find_missing_expected_evidence(events)

    assert "payment.failed" not in result
    assert "payment.captured" not in result


def test_empty_events_produce_no_missing_payment_evidence():
    result = find_missing_expected_evidence(())

    assert result == ()