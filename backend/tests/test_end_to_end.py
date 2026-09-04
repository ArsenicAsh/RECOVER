from dataclasses import replace
from datetime import timedelta

from app.services.dataset_generator.models import ObservedEvent

from app.services.dataset_generator.generator import (
    DatasetGenerator,
    GeneratorConfig,
)
from app.services.evaluation.evaluator import evaluate_case
from app.services.reconstruction import reconstruct_events
from app.services.reconstruction.models import ReconstructionResult
from app.services.state_engine.engine import run_state_engine
from app.services.state_engine.models import StateInput, StateResult


def process_case(case):
    reconstruction = reconstruct_events(
        case.observed_events
    )

    state = run_state_engine(
        StateInput(
            reconstruction=reconstruction
        )
    )

    evaluation = evaluate_case(
        case=case,
        reconstruction=reconstruction,
        state=state,
    )

    return reconstruction, state, evaluation


def test_end_to_end_abandoned_checkout():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=1,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[0]

    reconstruction, state, evaluation = process_case(case)

    assert isinstance(
        reconstruction,
        ReconstructionResult,
    )

    assert isinstance(
        state,
        StateResult,
    )

    assert evaluation.passed is True
    assert state.money_state.value == "RECOVERABLE"
    assert state.requires_verification is False


def test_end_to_end_ambiguous_payment():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=2,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[1]

    reconstruction, state, evaluation = process_case(case)

    assert isinstance(
        reconstruction,
        ReconstructionResult,
    )

    assert isinstance(
        state,
        StateResult,
    )

    assert evaluation.passed is True
    assert state.money_state.value == "UNKNOWN"
    assert state.requires_verification is True


def test_end_to_end_order_payment_mismatch():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=3,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[2]

    # The current generator always applies disturbances inside
    # build_observed_events(), regardless of disturbance_probability.
    # For this clean E2E scenario test, construct an undisturbed
    # observed stream from the generated case's true event sequence.
    clean_observed_events = tuple(
        ObservedEvent(
            event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            received_at=event.occurred_at + timedelta(
                seconds=index
            ),
            processed_at=None,
            source=event.source,
            merchant_id=event.merchant_id,
            customer_id=event.customer_id,
            order_id=event.order_id,
            payment_id=event.payment_id,
            payload=dict(event.payload),
            sequence_hint=index,
        )
        for index, event in enumerate(
            case.ground_truth.true_event_sequence,
            start=1,
        )
    )

    case = replace(
        case,
        observed_events=clean_observed_events,
    )

    reconstruction, state, evaluation = process_case(case)

    assert isinstance(
        reconstruction,
        ReconstructionResult,
    )

    assert isinstance(
        state,
        StateResult,
    )

    assert evaluation.passed is True
    assert state.money_state.value == "AT_RISK"
    assert state.mismatch is True
    assert state.requires_verification is True


def test_end_to_end_pipeline_is_deterministic():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=3,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    cases = generator.generate()

    first_results = [
        process_case(case)
        for case in cases
    ]

    second_results = [
        process_case(case)
        for case in cases
    ]

    for first, second in zip(
        first_results,
        second_results,
        strict=True,
    ):
        first_reconstruction, first_state, first_evaluation = first
        second_reconstruction, second_state, second_evaluation = second

        assert first_reconstruction == second_reconstruction
        assert first_state == second_state
        assert first_evaluation == second_evaluation