from __future__ import annotations

from collections.abc import Iterable

from app.services.dataset_generator.models import ObservedEvent

from .models import ReconstructionEvent


def normalize_observed_events(
    events: Iterable[ObservedEvent],
) -> tuple[ReconstructionEvent, ...]:
    """
    Convert dataset-generator observed events into the normalized
    representation consumed by the reconstruction engine.

    This function performs representation normalization only.

    It must NOT:
    - sort events chronologically
    - remove duplicates
    - resolve contradictions
    - infer state
    - use ground truth
    - treat sequence_hint as chronological truth
    """

    return tuple(
        ReconstructionEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            received_at=event.received_at,
            processed_at=event.processed_at,
            source=event.source,
            merchant_id=event.merchant_id,
            customer_id=event.customer_id,
            order_id=event.order_id,
            payment_id=event.payment_id,
            payload=dict(event.payload),
            sequence_hint=event.sequence_hint,
        )
        for event in events
    )
