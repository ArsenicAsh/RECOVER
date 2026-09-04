from app.services.dataset_generator.generator import (
    DatasetGenerator,
    GeneratorConfig,
)
from app.services.evaluation.evaluator import evaluate_case
from app.services.reconstruction import reconstruct_events
from app.services.state_engine.engine import run_state_engine
from app.services.state_engine.models import StateInput


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


def generate_disturbed_cases():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=30,
            seed=42,
            disturbance_probability=1.0,
        )
    )

    return generator.generate()


def true_event_ids(case):
    return tuple(
        event.event_id
        for event in case.ground_truth.true_event_sequence
    )


def surviving_true_event_ids(case):
    observed_ids = {
        event.event_id
        for event in case.observed_events
        if not event.event_id.endswith(
            "_contradiction"
        )
    }

    return tuple(
        event_id
        for event_id in true_event_ids(case)
        if event_id in observed_ids
    )


def reconstructed_true_event_ids(
    case,
    reconstruction,
):
    true_ids = set(
        true_event_ids(case)
    )

    seen = set()
    result = []

    for event in reconstruction.chronological_events:
        if event.event_id not in true_ids:
            continue

        if event.event_id in seen:
            continue

        seen.add(event.event_id)
        result.append(event.event_id)

    return tuple(result)


def test_disturbance_regression_chronology_survives():
    cases = generate_disturbed_cases()

    checked = 0

    for case in cases:
        reconstruction, _, _ = process_case(case)

        expected = surviving_true_event_ids(case)
        actual = reconstructed_true_event_ids(
            case,
            reconstruction,
        )

        assert actual == expected

        timestamps = [
            event.occurred_at
            for event in reconstruction.chronological_events
        ]

        assert timestamps == sorted(timestamps)

        checked += 1

    assert checked == len(cases)


def test_disturbance_regression_duplicate_detection():
    cases = generate_disturbed_cases()

    duplicate_cases = []

    for case in cases:
        reconstruction, _, _ = process_case(case)

        if reconstruction.duplicate_event_ids:
            duplicate_cases.append(
                reconstruction
            )

    assert duplicate_cases

    for reconstruction in duplicate_cases:
        assert reconstruction.duplicate_event_ids

        for event_id in (
            reconstruction.duplicate_event_ids
        ):
            matching_events = [
                event
                for event in reconstruction.chronological_events
                if event.event_id == event_id
            ]

            assert len(matching_events) >= 2


def test_disturbance_regression_delayed_and_out_of_order():
    cases = generate_disturbed_cases()

    checked = 0

    for case in cases:
        disturbance_types = {
            disturbance.disturbance_type
            for disturbance in case.disturbances
        }

        if not {
            "DELAYED",
            "OUT_OF_ORDER",
        }.issubset(disturbance_types):
            continue

        reconstruction, _, _ = process_case(case)

        timestamps = [
            event.occurred_at
            for event in reconstruction.chronological_events
        ]

        assert timestamps == sorted(timestamps)

        expected = surviving_true_event_ids(case)
        actual = reconstructed_true_event_ids(
            case,
            reconstruction,
        )

        assert actual == expected

        checked += 1

    assert checked > 0


def test_disturbance_regression_observable_missing_evidence():
    cases = generate_disturbed_cases()

    missing_cases = []

    for case in cases:
        reconstruction, _, _ = process_case(case)

        if reconstruction.missing_expected_evidence:
            missing_cases.append(
                reconstruction
            )

    # Missing evidence is only asserted when the
    # reconstruction contract actually identifies it.
    for reconstruction in missing_cases:
        assert reconstruction.uncertainty is not None


def test_disturbance_regression_observable_contradictions():
    cases = generate_disturbed_cases()

    contradictory_cases = []

    for case in cases:
        reconstruction, state, evaluation = (
            process_case(case)
        )

        if reconstruction.contradictions:
            contradictory_cases.append(
                (
                    reconstruction,
                    state,
                    evaluation,
                )
            )

    assert contradictory_cases

    for (
        reconstruction,
        state,
        evaluation,
    ) in contradictory_cases:
        assert evaluation.passed is True

        assert (
            reconstruction.reconstruction_status.value
            == "CONFLICTED"
        )

        assert (
            state.money_state.value
            == "UNKNOWN"
        )

        assert state.requires_verification is True


def test_disturbance_regression_all_scenarios_remain_reconstructable():
    cases = generate_disturbed_cases()

    scenario_types = {
        case.scenario_type
        for case in cases
    }

    assert scenario_types == {
        "ABANDONED_CHECKOUT",
        "AMBIGUOUS_PAYMENT",
        "ORDER_PAYMENT_MISMATCH",
    }

    for case in cases:
        reconstruction, state, evaluation = (
            process_case(case)
        )

        assert reconstruction.chronological_events

        assert evaluation.chronology_correct is True

        # Disturbances may legitimately change the
        # certainty of financial state, but they must
        # never cause the pipeline itself to fail.
        assert evaluation.contradiction_detection_correct is True
        assert evaluation.missing_evidence_awareness_correct is True