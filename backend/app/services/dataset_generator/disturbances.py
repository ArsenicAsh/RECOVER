from __future__ import annotations

import random
from datetime import timedelta
from typing import Sequence

from app.services.dataset_generator.models import (
    Disturbance,
    GroundTruthEvent,
    ObservedEvent,
)


DUPLICATE = "DUPLICATE"
DELAYED = "DELAYED"
OUT_OF_ORDER = "OUT_OF_ORDER"
MISSING = "MISSING"
CONTRADICTORY = "CONTRADICTORY"


def _to_observed_event(
    event: GroundTruthEvent,
    *,
    received_at,
    sequence_hint: int,
) -> ObservedEvent:
    return ObservedEvent(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.occurred_at,
        received_at=received_at,
        processed_at=None,
        source=event.source,
        merchant_id=event.merchant_id,
        customer_id=event.customer_id,
        order_id=event.order_id,
        payment_id=event.payment_id,
        payload=dict(event.payload),
        sequence_hint=sequence_hint,
    )


def apply_duplicate(
    events: list[ObservedEvent],
    rng: random.Random,
) -> Disturbance | None:
    """
    Duplicate an existing logical delivery.

    The duplicate retains the same event_id, representing another
    delivery of the same logical event.
    """

    if not events:
        return None

    index = rng.randrange(len(events))
    original = events[index]

    duplicate = ObservedEvent(
        event_id=original.event_id,
        event_type=original.event_type,
        occurred_at=original.occurred_at,
        received_at=original.received_at + timedelta(seconds=1),
        processed_at=None,
        source=original.source,
        merchant_id=original.merchant_id,
        customer_id=original.customer_id,
        order_id=original.order_id,
        payment_id=original.payment_id,
        payload=dict(original.payload),
        sequence_hint=len(events) + 1,
    )

    events.append(duplicate)

    return Disturbance(
        disturbance_type=DUPLICATE,
        event_id=original.event_id,
        details={
            "original_index": index,
        },
    )


def apply_delayed(
    events: list[ObservedEvent],
    rng: random.Random,
) -> Disturbance | None:
    """
    Delay delivery of an event without changing when it occurred.
    """

    if not events:
        return None

    index = rng.randrange(len(events))
    original = events[index]

    delay_seconds = rng.randint(30, 300)

    delayed = ObservedEvent(
        event_id=original.event_id,
        event_type=original.event_type,
        occurred_at=original.occurred_at,
        received_at=original.received_at + timedelta(seconds=delay_seconds),
        processed_at=original.processed_at,
        source=original.source,
        merchant_id=original.merchant_id,
        customer_id=original.customer_id,
        order_id=original.order_id,
        payment_id=original.payment_id,
        payload=dict(original.payload),
        sequence_hint=original.sequence_hint,
    )

    events[index] = delayed

    return Disturbance(
        disturbance_type=DELAYED,
        event_id=original.event_id,
        details={
            "delay_seconds": delay_seconds,
        },
    )


def apply_out_of_order(
    events: list[ObservedEvent],
    rng: random.Random,
) -> Disturbance | None:
    """
    Change arrival order while preserving occurred_at.

    sequence_hint follows delivery order and must never be treated
    as chronological truth.
    """

    if len(events) < 2:
        return None

    original_order = [event.event_id for event in events]

    rng.shuffle(events)

    reordered = []

    for sequence, event in enumerate(events, start=1):
        reordered.append(
            ObservedEvent(
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
                sequence_hint=sequence,
            )
        )

    events[:] = reordered

    return Disturbance(
        disturbance_type=OUT_OF_ORDER,
        details={
            "original_order": original_order,
            "observed_order": [event.event_id for event in events],
        },
    )


def apply_missing(
    events: list[ObservedEvent],
    rng: random.Random,
) -> Disturbance | None:
    """
    Remove one observed event.

    Ground truth remains unchanged elsewhere.
    """

    if not events:
        return None

    index = rng.randrange(len(events))
    removed = events.pop(index)

    return Disturbance(
        disturbance_type=MISSING,
        event_id=removed.event_id,
        details={
            "removed_index": index,
            "event_type": removed.event_type,
        },
    )


def apply_contradictory(
    events: list[ObservedEvent],
    rng: random.Random,
) -> Disturbance | None:
    """
    Add contradictory payment evidence.

    The contradiction uses the canonical payment lifecycle vocabulary:
    payment.captured vs payment.failed.
    """

    payment_events = [
        event
        for event in events
        if event.payment_id is not None
        and event.event_type in {
            "payment.initiated",
            "payment.authorized",
            "payment.captured",
            "payment.failed",
        }
    ]

    if not payment_events:
        return None

    source_event = rng.choice(payment_events)

    if source_event.event_type == "payment.failed":
        contradictory_type = "payment.captured"
        status = "CAPTURED"
    else:
        contradictory_type = "payment.failed"
        status = "FAILED"

    contradiction = ObservedEvent(
        event_id=f"{source_event.event_id}_contradiction",
        event_type=contradictory_type,
        occurred_at=source_event.occurred_at + timedelta(seconds=5),
        received_at=source_event.received_at + timedelta(seconds=5),
        processed_at=None,
        source=source_event.source,
        merchant_id=source_event.merchant_id,
        customer_id=source_event.customer_id,
        order_id=source_event.order_id,
        payment_id=source_event.payment_id,
        payload={
            **source_event.payload,
            "synthetic_contradiction": True,
            "contradictory_status": status,
        },
        sequence_hint=len(events) + 1,
    )

    events.append(contradiction)

    return Disturbance(
        disturbance_type=CONTRADICTORY,
        event_id=source_event.event_id,
        details={
            "contradictory_event_id": contradiction.event_id,
            "original_event_type": source_event.event_type,
            "contradictory_event_type": contradictory_type,
        },
    )


def build_observed_events(
    true_events: Sequence[GroundTruthEvent],
    rng: random.Random,
    *,
    received_at_base,
) -> tuple[list[ObservedEvent], list[Disturbance]]:
    """
    Convert true events into observed deliveries and apply
    deterministic disturbances.
    """

    events: list[ObservedEvent] = []

    for sequence, event in enumerate(true_events, start=1):
        received_at = received_at_base + timedelta(
            seconds=sequence
        )

        events.append(
            _to_observed_event(
                event,
                received_at=received_at,
                sequence_hint=sequence,
            )
        )

    disturbances: list[Disturbance] = []

    disturbance_functions = [
        apply_duplicate,
        apply_delayed,
        apply_out_of_order,
        apply_missing,
        apply_contradictory,
    ]

    for disturbance_function in disturbance_functions:
        disturbance = disturbance_function(events, rng)

        if disturbance is not None:
            disturbances.append(disturbance)

    return events, disturbances