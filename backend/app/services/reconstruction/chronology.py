from __future__ import annotations

from collections.abc import Iterable

from .models import ReconstructionEvent


def order_events_chronologically(
    events: Iterable[ReconstructionEvent],
) -> tuple[ReconstructionEvent, ...]:
    """
    Return observed events in deterministic chronological order.

    Ordering rules:
    1. occurred_at is the source of chronological truth.
    2. event_id is the deterministic tie-breaker when timestamps match.

    received_at represents delivery timing and must not determine
    chronological order.

    sequence_hint represents delivery order and must not determine
    chronological order.

    This function does not:
    - remove duplicates
    - resolve contradictions
    - infer missing events
    - infer state
    """

    return tuple(
        sorted(
            events,
            key=lambda event: (event.occurred_at, event.event_id),
        )
    )