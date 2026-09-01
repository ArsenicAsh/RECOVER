from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class GroundTruthEvent:
    """
    The event as it truly occurred in the synthetic world.

    This represents reality, not necessarily what the
    Reconstruction Engine will observe.
    """

    event_id: str
    event_type: str
    occurred_at: datetime
    source: str
    merchant_id: str
    customer_id: str
    order_id: str | None = None
    payment_id: str | None = None
    payload: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class ObservedEvent:
    """
    An event delivery visible to the Reconstruction Engine.

    The observed stream may contain duplicates, delays,
    missing events, contradictory evidence, or out-of-order
    delivery.
    """

    event_id: str
    event_type: str
    occurred_at: datetime
    received_at: datetime
    processed_at: datetime | None
    source: str
    merchant_id: str
    customer_id: str
    order_id: str | None = None
    payment_id: str | None = None
    payload: dict[str, Any] = field(
        default_factory=dict
    )
    sequence_hint: int | None = None


@dataclass(frozen=True)
class Disturbance:
    """
    Records an imperfection deliberately introduced into
    the observed event stream.
    """

    disturbance_type: str
    event_id: str | None = None
    details: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass(frozen=True)
class GroundTruth:
    """
    Hidden truth for a generated case.

    This must never be supplied to the Reconstruction Engine
    as evidence.
    """

    scenario_type: str

    true_event_sequence: list[GroundTruthEvent]

    true_money_state: str
    true_workflow_condition: str

    expected_reconstruction: dict[str, Any]
    expected_action: str | None
    expected_outcome: str | None


@dataclass
class GeneratedCase:
    """
    Complete synthetic case produced by the dataset generator.
    """

    case_id: str
    case_number: str

    merchant_id: str
    customer_id: str
    order_id: str
    payment_id: str | None

    amount: int
    currency: str

    scenario_type: str

    observed_events: list[ObservedEvent]

    disturbances: list[Disturbance]

    ground_truth: GroundTruth

    # ------------------------------------------------------------------
    # Compatibility / provenance fields
    # ------------------------------------------------------------------

    payment: dict[str, Any] | None = None

    true_events: list[GroundTruthEvent] = field(
        default_factory=list
    )

    generator_version: str = "0.1.0"

    seed: int = 42