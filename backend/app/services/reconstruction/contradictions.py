from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .models import Contradiction, ReconstructionEvent


CONTRADICTORY_PAYMENT_EVENTS = frozenset(
    {
        frozenset({"payment.captured", "payment.failed"}),
    }
)


def find_contradictions(
    events: Iterable[ReconstructionEvent],
) -> tuple[Contradiction, ...]:
    """
    Detect mutually incompatible observed payment evidence.

    Contradictions are reported, not resolved.

    The function must:
    - preserve all observed evidence
    - never choose a winning event
    - never infer which event is correct
    - remain deterministic
    """

    events_by_payment: dict[str, list[ReconstructionEvent]] = defaultdict(list)

    for event in events:
        if event.payment_id is not None:
            events_by_payment[event.payment_id].append(event)

    contradictions: list[Contradiction] = []

    for payment_id, payment_events in events_by_payment.items():
        events_by_type: dict[str, list[ReconstructionEvent]] = defaultdict(list)

        for event in payment_events:
            events_by_type[event.event_type].append(event)

        event_types = set(events_by_type)

        for contradictory_pair in CONTRADICTORY_PAYMENT_EVENTS:
            if contradictory_pair.issubset(event_types):
                captured_events = events_by_type["payment.captured"]
                failed_events = events_by_type["payment.failed"]

                event_ids = tuple(
                    sorted(
                        event.event_id
                        for event in (
                            captured_events + failed_events
                        )
                    )
                )

                contradictions.append(
                    Contradiction(
                        event_ids=event_ids,
                        description=(
                            f"Payment {payment_id} has conflicting "
                            "terminal evidence: payment.captured and "
                            "payment.failed."
                        ),
                    )
                )

    return tuple(
        sorted(
            contradictions,
            key=lambda contradiction: contradiction.event_ids,
        )
    )