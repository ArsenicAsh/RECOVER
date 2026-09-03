from __future__ import annotations

from app.domain.models.case import ReconstructionStatus
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus

from .models import ReconstructionEvent


PAYMENT_EVENT_STATES: dict[str, PaymentStatus] = {
    "payment.initiated": PaymentStatus.INITIATED,
    "payment.authorized": PaymentStatus.AUTHORIZED,
    "payment.captured": PaymentStatus.CAPTURED,
    "payment.failed": PaymentStatus.FAILED,
    "payment.refunded": PaymentStatus.REFUNDED,
}


ORDER_EVENT_STATES: dict[str, OrderStatus] = {
    "order.created": OrderStatus.CREATED,
    "order.paid": OrderStatus.PAID,
    "order.unpaid": OrderStatus.UNPAID,
    "order.cancelled": OrderStatus.CANCELLED,
}


def reconstruct_payment_state(
    events: tuple[ReconstructionEvent, ...],
) -> PaymentStatus | None:
    """
    Reconstruct payment state from chronologically ordered evidence.

    The function assumes that contradiction detection has already happened.
    If conflicting terminal evidence exists, callers must not use this
    function as a resolver.
    """
    payment_state: PaymentStatus | None = None

    for event in events:
        state = PAYMENT_EVENT_STATES.get(event.event_type)

        if state is not None:
            payment_state = state

    return payment_state


def reconstruct_order_state(
    events: tuple[ReconstructionEvent, ...],
) -> OrderStatus | None:
    """
    Reconstruct order state from explicitly observed order events.

    No order state is invented from payment evidence.
    """
    order_state: OrderStatus | None = None

    for event in events:
        state = ORDER_EVENT_STATES.get(event.event_type)

        if state is not None:
            order_state = state

    return order_state


def reconstruct_state(
    events: tuple[ReconstructionEvent, ...],
    has_contradictions: bool,
    has_missing_expected_evidence: bool,
) -> tuple[
    PaymentStatus | None,
    OrderStatus | None,
    ReconstructionStatus,
    tuple[str, ...],
]:
    """
    Reconstruct the state supported by the supplied evidence.

    This function deliberately avoids guessing when the evidence is
    incomplete or contradictory.
    """
    payment_events = tuple(
        event
        for event in events
        if event.event_type.startswith("payment.")
    )

    payment_state = reconstruct_payment_state(events)
    order_state = reconstruct_order_state(events)

    if has_contradictions:
        payment_state = None

    uncertainty: list[str] = []


    if has_contradictions:
        uncertainty.append(
            "Conflicting payment evidence prevents a definitive payment state."
        )

    if has_missing_expected_evidence:
        uncertainty.append(
            "Expected payment terminal outcome was not observed."
        )

    if payment_events and payment_state is None:
        uncertainty.append(
            "Payment evidence exists, but no definitive payment state is supported."
        )

    if has_contradictions:
        reconstruction_status = ReconstructionStatus.CONFLICTED
    elif has_missing_expected_evidence:
        reconstruction_status = ReconstructionStatus.PARTIAL
    else:
        reconstruction_status = ReconstructionStatus.COMPLETE

    return (
        payment_state,
        order_state,
        reconstruction_status,
        tuple(uncertainty),
    )