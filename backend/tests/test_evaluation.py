from app.services.dataset_generator.generator import (
    DatasetGenerator,
    GeneratorConfig,
)
from app.services.reconstruction.chronology import (
    order_events_chronologically,
)
from app.services.reconstruction.contradictions import (
    find_contradictions,
)
from app.services.reconstruction.duplicates import (
    find_duplicate_event_ids,
)
from app.services.reconstruction.missing import (
    find_missing_expected_evidence,
)
from app.services.reconstruction.models import ReconstructionResult
from app.services.reconstruction.normalization import (
    normalize_observed_events,
)
from app.services.reconstruction.state import reconstruct_state
from app.services.state_engine.engine import run_state_engine
from app.services.state_engine.models import StateInput

from app.services.evaluation.evaluator import evaluate_case


def reconstruct_case(case):
    normalized = normalize_observed_events(
        case.observed_events
    )

    chronological = order_events_chronologically(
        normalized
    )

    duplicate_ids = find_duplicate_event_ids(
        normalized
    )

    missing = find_missing_expected_evidence(
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
        has_missing_expected_evidence=bool(missing),
    )

    reconstruction = ReconstructionResult(
        chronological_events=chronological,
        duplicate_event_ids=duplicate_ids,
        missing_expected_evidence=missing,
        contradictions=contradictions,
        payment_state=payment_state,
        order_state=order_state,
        reconstruction_status=reconstruction_status,
        uncertainty=uncertainty,
    )

    state = run_state_engine(
        StateInput(reconstruction=reconstruction)
    )

    return reconstruction, state


def test_evaluation_abandoned_checkout():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=1,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[0]

    reconstruction, state = reconstruct_case(case)

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    assert case.scenario_type == "ABANDONED_CHECKOUT"
    assert evaluation.passed is True
    assert evaluation.chronology_correct is True
    assert evaluation.state_correct is True
    assert evaluation.contradiction_detection_correct is True
    assert evaluation.missing_evidence_awareness_correct is True
    assert evaluation.uncertainty_correct is True


def test_evaluation_ambiguous_payment():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=2,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    cases = generator.generate()
    case = cases[1]

    reconstruction, state = reconstruct_case(case)

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    assert case.scenario_type == "AMBIGUOUS_PAYMENT"
    assert evaluation.passed is True
    assert evaluation.chronology_correct is True
    assert evaluation.state_correct is True
    assert evaluation.missing_evidence_awareness_correct is True
    assert evaluation.uncertainty_correct is True


def test_evaluation_order_payment_mismatch():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=3,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    cases = generator.generate()
    case = cases[2]

    reconstruction, state = reconstruct_case(case)

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    assert case.scenario_type == "ORDER_PAYMENT_MISMATCH"
    assert evaluation.passed is True
    assert evaluation.chronology_correct is True
    assert evaluation.state_correct is True


def test_evaluation_detects_contradictory_disturbance():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=30,
            seed=42,
            disturbance_probability=1.0,
        )
    )

    cases = generator.generate()

    contradictory_cases = [
        case
        for case in cases
        if any(
            disturbance.disturbance_type
            == "CONTRADICTORY"
            for disturbance in case.disturbances
        )
    ]

    assert contradictory_cases

    case = next(
    case
    for case in contradictory_cases
    if any(
        event.event_type == "payment.captured"
        for event in case.observed_events
    )
    and any(
        event.event_type == "payment.failed"
        for event in case.observed_events
    )
)

    reconstruction, state = reconstruct_case(case)

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    assert evaluation.contradiction_detection_correct is True
    assert evaluation.uncertainty_correct is True