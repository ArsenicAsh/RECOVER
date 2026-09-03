from datetime import datetime, timezone

from app.domain.models.case import ReconstructionStatus
from app.domain.models.payment import PaymentStatus
from app.services.reconstruction.explanation import build_explanation
from app.services.reconstruction.models import (
    Contradiction,
    ReconstructionEvent,
)


def make_event(
    event_id: str,
    event_type: str,
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
        occurred_at=timestamp,
        received_at=timestamp,
        processed_at=None,
        source="test",
        merchant_id="merchant_1",
        customer_id="customer_1",
        order_id="order_1",
        payment_id="payment_1",
        payload={},
    )


def test_explanation_describes_complete_payment_state():
    events = (
        make_event("evt_1", "payment.initiated"),
        make_event("evt_2", "payment.captured"),
    )

    explanation = build_explanation(
        events=events,
        payment_state=PaymentStatus.CAPTURED,
        order_state=None,
        reconstruction_status=ReconstructionStatus.COMPLETE,
        missing_expected_evidence=(),
        contradictions=(),
        inferred_transitions=(),
        uncertainty=(),
    )

    assert "2 observed event(s)" in explanation
    assert "Reconstructed payment state: CAPTURED." in explanation
    assert "Reconstruction status: COMPLETE." in explanation


def test_explanation_describes_missing_terminal_evidence():
    events = (
        make_event("evt_1", "payment.initiated"),
        make_event("evt_2", "payment.authorized"),
    )

    explanation = build_explanation(
        events=events,
        payment_state=PaymentStatus.AUTHORIZED,
        order_state=None,
        reconstruction_status=ReconstructionStatus.PARTIAL,
        missing_expected_evidence=("payment.terminal_outcome",),
        contradictions=(),
        inferred_transitions=(),
        uncertainty=(
            "Expected payment terminal outcome was not observed.",
        ),
    )

    assert "Reconstructed payment state: AUTHORIZED." in explanation
    assert "Expected evidence is missing: payment.terminal_outcome." in explanation
    assert "Uncertainty:" in explanation
    assert "Reconstruction status: PARTIAL." in explanation


def test_explanation_describes_contradiction():
    events = (
        make_event("evt_1", "payment.captured"),
        make_event("evt_2", "payment.failed"),
    )

    contradiction = Contradiction(
        event_ids=("evt_1", "evt_2"),
        description="Payment has both captured and failed evidence.",
    )

    explanation = build_explanation(
        events=events,
        payment_state=None,
        order_state=None,
        reconstruction_status=ReconstructionStatus.CONFLICTED,
        missing_expected_evidence=(),
        contradictions=(contradiction,),
        inferred_transitions=(),
        uncertainty=(
            "Conflicting payment evidence prevents a definitive payment state.",
        ),
    )

    assert "A definitive payment state could not be established" in explanation
    assert "1 contradiction(s) were detected" in explanation
    assert "Reconstruction status: CONFLICTED." in explanation


def test_explanation_handles_empty_evidence():
    explanation = build_explanation(
        events=(),
        payment_state=None,
        order_state=None,
        reconstruction_status=ReconstructionStatus.PARTIAL,
        missing_expected_evidence=(),
        contradictions=(),
        inferred_transitions=(),
        uncertainty=("No evidence was available.",),
    )

    assert "No observed events were available for reconstruction." in explanation
    assert "Uncertainty: No evidence was available." in explanation
    assert "Reconstruction status: PARTIAL." in explanation