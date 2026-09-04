from app.services.dataset_generator.generator import (
    DatasetGenerator,
    GeneratorConfig,
)
from app.services.reconstruction import reconstruct_events
from app.services.reconstruction.models import ReconstructionResult
from app.services.state_engine.engine import run_state_engine
from app.services.state_engine.models import StateInput
from app.services.evaluation.evaluator import evaluate_case


def reconstruct_case(case):
    reconstruction = reconstruct_events(
        case.observed_events
    )

    state = run_state_engine(
        StateInput(
            reconstruction=reconstruction
        )
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

    assert isinstance(
        reconstruction,
        ReconstructionResult,
    )

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

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

    case = generator.generate()[1]

    reconstruction, state = reconstruct_case(case)

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    assert evaluation.passed is True
    assert evaluation.chronology_correct is True
    assert evaluation.state_correct is True
    assert evaluation.contradiction_detection_correct is True
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

    case = generator.generate()[2]

    reconstruction, state = reconstruct_case(case)

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    assert evaluation.passed is True
    assert evaluation.chronology_correct is True
    assert evaluation.state_correct is True
    assert evaluation.contradiction_detection_correct is True
    assert evaluation.missing_evidence_awareness_correct is True
    assert evaluation.uncertainty_correct is True


def test_evaluation_contradictory_disturbance():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=30,
            seed=42,
            disturbance_probability=1.0,
        )
    )

    cases = generator.generate()

    contradictory_case = None

    for case in cases:
        event_types = {
            event.event_type
            for event in case.observed_events
        }

        if (
            "payment.captured" in event_types
            and "payment.failed" in event_types
        ):
            contradictory_case = case
            break

    assert contradictory_case is not None

    reconstruction, state = reconstruct_case(
        contradictory_case
    )

    evaluation = evaluate_case(
        case=contradictory_case,
        reconstruction=reconstruction,
        state=state,
    )

    assert evaluation.passed is True
    assert evaluation.chronology_correct is True
    assert evaluation.state_correct is True
    assert evaluation.contradiction_detection_correct is True
    assert evaluation.missing_evidence_awareness_correct is True
    assert evaluation.uncertainty_correct is True