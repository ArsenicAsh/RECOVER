from __future__ import annotations

from collections.abc import Iterable

from app.services.dataset_generator.models import ObservedEvent

from .chronology import order_events_chronologically
from .contradictions import find_contradictions
from .duplicates import find_duplicate_event_ids
from .explanation import build_explanation
from .missing import find_missing_expected_evidence
from .models import ReconstructionResult
from .normalization import normalize_observed_events
from .state import reconstruct_state


def reconstruct_events(
    events: Iterable[ObservedEvent],
) -> ReconstructionResult:
    """
    Run the complete deterministic reconstruction pipeline.

    The pipeline operates exclusively on observed events.

    Ground truth, generator metadata, arrival order, and sequence_hint
    are never used as sources of chronological or state truth.
    """

    normalized = normalize_observed_events(events)

    chronological = order_events_chronologically(
        normalized
    )

    duplicate_event_ids = find_duplicate_event_ids(
        normalized
    )

    missing_expected_evidence = find_missing_expected_evidence(
        normalized
    )

    contradictions = find_contradictions(
        normalized
    )

    (
        payment_state,
        order_state,
        reconstruction_status,
        uncertainty,
    ) = reconstruct_state(
        chronological,
        has_contradictions=bool(contradictions),
        has_missing_expected_evidence=bool(
            missing_expected_evidence
        ),
    )

    explanation = build_explanation(
        events=chronological,
        payment_state=payment_state,
        order_state=order_state,
        reconstruction_status=reconstruction_status,
        missing_expected_evidence=missing_expected_evidence,
        contradictions=contradictions,
        inferred_transitions=(),
        uncertainty=uncertainty,
    )

    return ReconstructionResult(
        chronological_events=chronological,
        duplicate_event_ids=duplicate_event_ids,
        missing_expected_evidence=missing_expected_evidence,
        contradictions=contradictions,
        payment_state=payment_state,
        order_state=order_state,
        reconstruction_status=reconstruction_status,
        uncertainty=uncertainty,
        explanation=explanation,
    )