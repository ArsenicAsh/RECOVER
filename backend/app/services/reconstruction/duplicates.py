from __future__ import annotations

from collections import Counter
from collections.abc import Iterable

from .models import ReconstructionEvent


def find_duplicate_event_ids(
    events: Iterable[ReconstructionEvent],
) -> tuple[str, ...]:
    """
    Identify event IDs that occur more than once.

    Duplicate events are reported but not removed.

    Event identity is based on event_id because the upstream event
    contract guarantees logical identity at the ingestion boundary.
    """

    counts = Counter(event.event_id for event in events)

    return tuple(
        sorted(
            event_id
            for event_id, count in counts.items()
            if count > 1
        )
    )