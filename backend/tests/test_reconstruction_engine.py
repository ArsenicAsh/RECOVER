from app.services.dataset_generator.generator import (
    DatasetGenerator,
    GeneratorConfig,
)
from app.services.reconstruction import reconstruct_events
from app.services.reconstruction.models import ReconstructionResult


def test_reconstruct_events_returns_reconstruction_result():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=1,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[0]

    result = reconstruct_events(case.observed_events)

    assert isinstance(result, ReconstructionResult)


def test_reconstruct_events_orders_by_occurred_at():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=1,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[0]

    result = reconstruct_events(case.observed_events)

    timestamps = [
        event.occurred_at
        for event in result.chronological_events
    ]

    assert timestamps == sorted(timestamps)


def test_reconstruct_events_preserves_duplicate_detection():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=30,
            seed=42,
            disturbance_probability=1.0,
        )
    )

    cases = generator.generate()

    duplicate_cases = []

    for case in cases:
        result = reconstruct_events(case.observed_events)

        if result.duplicate_event_ids:
            duplicate_cases.append(result)

    assert duplicate_cases


def test_reconstruct_events_builds_explanation():
    generator = DatasetGenerator(
        GeneratorConfig(
            case_count=1,
            seed=42,
            disturbance_probability=0.0,
        )
    )

    case = generator.generate()[0]

    result = reconstruct_events(case.observed_events)

    assert result.explanation
    assert "observed event" in result.explanation
    assert "Reconstruction status:" in result.explanation