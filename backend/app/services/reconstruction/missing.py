from __future__ import annotations

from collections.abc import Iterable

from .models import ReconstructionEvent


PAYMENT_TERMINAL_EVENTS = frozenset(
    {
        "payment.captured",
        "payment.failed",
        "payment.refunded",
    }
)


def find_missing_expected_evidence(
    events: Iterable[ReconstructionEvent],
) -> tuple[str, ...]:
    """
    Identify expected evidence that is absent from the observed event set.

    This function reports missing evidence only.

    It must NOT:
    - infer that a missing event definitely occurred
    - infer that a payment failed because failure evidence is absent
    - use ground truth
    - resolve contradictions
    - infer final payment/order state
    """

    event_types = {
        event.event_type
        for event in events
    }

    missing: list[str] = []

    if (
        "payment.initiated" in event_types
        or "payment.authorized" in event_types
    ):
        if not event_types.intersection(PAYMENT_TERMINAL_EVENTS):
            missing.append("payment.terminal_outcome")

    return tuple(missing)