from app.services.dataset_generator.generator import (
    DatasetGenerator,
    GeneratorConfig,
)


def test_generator_produces_requested_case_count():
    config = GeneratorConfig(
        case_count=100,
        seed=42,
    )

    generator = DatasetGenerator(config)
    cases = generator.generate()

    assert len(cases) == 100


def test_generator_is_deterministic():
    config = GeneratorConfig(
        case_count=20,
        seed=42,
    )

    first = DatasetGenerator(config).generate()
    second = DatasetGenerator(config).generate()

    assert first == second


def test_different_seed_changes_dataset():
    first_config = GeneratorConfig(
        case_count=20,
        seed=42,
    )

    second_config = GeneratorConfig(
        case_count=20,
        seed=99,
    )

    first = DatasetGenerator(first_config).generate()
    second = DatasetGenerator(second_config).generate()

    assert first != second


def test_all_three_scenarios_are_generated():
    config = GeneratorConfig(
        case_count=100,
        seed=42,
    )

    cases = DatasetGenerator(config).generate()

    scenarios = {
        case.scenario_type
        for case in cases
    }

    assert scenarios == {
        "ABANDONED_CHECKOUT",
        "AMBIGUOUS_PAYMENT",
        "ORDER_PAYMENT_MISMATCH",
    }


def test_abandoned_checkout_can_have_no_payment():
    config = GeneratorConfig(
        case_count=100,
        seed=42,
    )

    cases = DatasetGenerator(config).generate()

    abandoned = [
        case
        for case in cases
        if case.scenario_type == "ABANDONED_CHECKOUT"
    ]

    assert abandoned

    assert all(
        case.payment is None
        for case in abandoned
    )


def test_ground_truth_and_observed_events_are_distinct():
    config = GeneratorConfig(
        case_count=100,
        seed=42,
    )

    cases = DatasetGenerator(config).generate()

    for case in cases:
        assert case.true_events is not case.observed_events


def test_generator_version_is_recorded():
    config = GeneratorConfig(
        case_count=10,
        seed=42,
        generator_version="0.1.0",
    )

    cases = DatasetGenerator(config).generate()

    assert all(
        case.generator_version == "0.1.0"
        for case in cases
    )


def test_seed_is_recorded():
    config = GeneratorConfig(
        case_count=10,
        seed=12345,
    )

    cases = DatasetGenerator(config).generate()

    assert all(
        case.seed == 12345
        for case in cases
    )