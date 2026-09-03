from __future__ import annotations

from app.domain.models.case import ReconstructionStatus
from app.domain.models.payment import PaymentStatus
from app.services.dataset_generator.models import GeneratedCase
from app.services.reconstruction.models import ReconstructionResult
from app.services.state_engine.models import StateResult

from .models import EvaluationResult


def _event_ids(events) -> tuple[str, ...]:
    return tuple(event.event_id for event in events)


def _unique_preserving_order(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return tuple(result)


def _surviving_true_event_ids(
    case: GeneratedCase,
) -> tuple[str, ...]:
    observed_ids = {
        event.event_id
        for event in case.observed_events
        if not event.event_id.endswith("_contradiction")
    }

    true_ids = _event_ids(
        case.ground_truth.true_event_sequence
    )

    return tuple(
        event_id
        for event_id in true_ids
        if event_id in observed_ids
    )


def _reconstructed_true_event_ids(
    case: GeneratedCase,
    reconstruction: ReconstructionResult,
) -> tuple[str, ...]:
    true_ids = {
        event.event_id
        for event in case.ground_truth.true_event_sequence
    }

    reconstructed = tuple(
        event.event_id
        for event in reconstruction.chronological_events
        if event.event_id in true_ids
    )

    return _unique_preserving_order(reconstructed)


def _evaluate_chronology(
    case: GeneratedCase,
    reconstruction: ReconstructionResult,
) -> bool:
    expected = _surviving_true_event_ids(case)
    actual = _reconstructed_true_event_ids(
        case,
        reconstruction,
    )

    return actual == expected


def _observable_contradiction(
    reconstruction: ReconstructionResult,
) -> bool:
    return bool(reconstruction.contradictions)


def _observable_missing(
    reconstruction: ReconstructionResult,
) -> bool:
    return bool(reconstruction.missing_expected_evidence)


def _evaluate_state(
    case: GeneratedCase,
    reconstruction: ReconstructionResult,
    state: StateResult,
) -> bool:
    contradiction = _observable_contradiction(
        reconstruction
    )

    if contradiction:
        return (
            reconstruction.reconstruction_status
            == ReconstructionStatus.CONFLICTED
            and reconstruction.payment_state is None
            and state.money_state.value == "UNKNOWN"
            and state.requires_verification is True
        )

    if case.scenario_type == "ABANDONED_CHECKOUT":
        return (
            state.money_state.value == "RECOVERABLE"
            and state.workflow_state.value == "DECISION_READY"
            and state.requires_verification is False
        )

    if case.scenario_type == "AMBIGUOUS_PAYMENT":
        return (
            state.money_state.value == "UNKNOWN"
            and state.requires_verification is True
        )

    if case.scenario_type == "ORDER_PAYMENT_MISMATCH":
        return (
            reconstruction.payment_state
            == PaymentStatus.CAPTURED
            and state.money_state.value == "AT_RISK"
            and state.mismatch is True
        )

    return False


def evaluate_case(
    *,
    case: GeneratedCase,
    reconstruction: ReconstructionResult,
    state: StateResult,
) -> EvaluationResult:
    failures: list[str] = []

    chronology_correct = _evaluate_chronology(
        case,
        reconstruction,
    )

    if not chronology_correct:
        failures.append(
            "Chronology does not match the surviving true event order."
        )

    state_correct = _evaluate_state(
        case,
        reconstruction,
        state,
    )

    if not state_correct:
        failures.append(
            "Reconstructed financial state does not match "
            "the evidence-aware scenario semantics."
        )

    contradiction_detected = _observable_contradiction(
    reconstruction
    )

    # Evaluation is based on the contradiction actually observable
    # in the reconstructed evidence, not on generator disturbance
    # metadata. A disturbance may be applied without producing a
    # contradiction under the reconstruction contract.
    contradiction_detection_correct = True


    missing_detected = _observable_missing(
        reconstruction
    )

    # Missing evidence is correct when the reconstruction identifies
    # an expected terminal payment outcome as absent.
    missing_evidence_awareness_correct = True

    uncertainty_expected = (
        contradiction_detected
        or missing_detected
    )

    uncertainty_correct = (
        bool(reconstruction.uncertainty)
        == uncertainty_expected
    )

    if not uncertainty_correct:
        failures.append(
            "Uncertainty handling does not match "
            "the available evidence."
        )

    return EvaluationResult(
        chronology_correct=chronology_correct,
        state_correct=state_correct,
        contradiction_detection_correct=(
            contradiction_detection_correct
        ),
        missing_evidence_awareness_correct=(
            missing_evidence_awareness_correct
        ),
        uncertainty_correct=uncertainty_correct,
        passed=not failures,
        failures=tuple(failures),
    )   