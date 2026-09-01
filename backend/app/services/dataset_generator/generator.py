from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime, timezone

from app.services.dataset_generator.disturbances import (
    build_observed_events,
)
from app.services.dataset_generator.factories import (
    create_case,
    create_customer,
    create_merchant,
)
from app.services.dataset_generator.models import GeneratedCase
from app.services.dataset_generator.scenarios import (
    generate_abandoned_checkout,
    generate_ambiguous_payment,
    generate_order_payment_mismatch,
)


GENERATOR_VERSION = "0.1.0"


@dataclass(frozen=True)
class GeneratorConfig:
    """
    Configuration for deterministic dataset generation.
    """

    case_count: int = 100
    seed: int = 42
    generator_version: str = GENERATOR_VERSION

    abandoned_checkout_ratio: float = 0.34
    ambiguous_payment_ratio: float = 0.33
    order_payment_mismatch_ratio: float = 0.33

    disturbance_probability: float = 0.65

    merchant_count: int = 5

    start_date: datetime = datetime(
        2026,
        8,
        1,
        0,
        0,
        0,
        tzinfo=timezone.utc,
    )


class DatasetGenerator:
    """
    Deterministic synthetic dataset generator for RECOVER.

    Pipeline:

        Scenario Truth
             ↓
        True Events
             ↓
        Disturbances
             ↓
        Observed Events
             ↓
        GeneratedCase

    Ground truth is retained separately and must never be supplied
    to the Reconstruction Engine as evidence.
    """

    def __init__(
        self,
        config: GeneratorConfig | None = None,
    ) -> None:
        self.config = (
            config
            or GeneratorConfig()
        )

        if self.config.case_count <= 0:
            raise ValueError(
                "case_count must be greater than zero"
            )

        if not 0 <= self.config.disturbance_probability <= 1:
            raise ValueError(
                "disturbance_probability must be between 0 and 1"
            )

        ratio_total = (
            self.config.abandoned_checkout_ratio
            + self.config.ambiguous_payment_ratio
            + self.config.order_payment_mismatch_ratio
        )

        if abs(ratio_total - 1.0) > 1e-9:
            raise ValueError(
                "Scenario ratios must sum to 1.0"
            )

        if self.config.merchant_count <= 0:
            raise ValueError(
                "merchant_count must be greater than zero"
            )

        self.rng = random.Random(
            self.config.seed
        )

    def generate(
        self,
    ) -> list[GeneratedCase]:
        """
        Generate the complete deterministic dataset.
        """

        generated_cases: list[GeneratedCase] = []

        scenario_counts = (
            self._calculate_scenario_counts()
        )

        case_number = 1

        for scenario_type, count in scenario_counts:
            for _ in range(count):
                generated_case = (
                    self._generate_case(
                        case_number=case_number,
                        scenario_type=scenario_type,
                    )
                )

                generated_cases.append(
                    generated_case
                )

                case_number += 1

        return generated_cases

    def _calculate_scenario_counts(
        self,
    ) -> list[tuple[str, int]]:
        """
        Convert scenario ratios into deterministic integer counts.
        """

        raw_counts = {
            "ABANDONED_CHECKOUT": (
                self.config.case_count
                * self.config.abandoned_checkout_ratio
            ),
            "AMBIGUOUS_PAYMENT": (
                self.config.case_count
                * self.config.ambiguous_payment_ratio
            ),
            "ORDER_PAYMENT_MISMATCH": (
                self.config.case_count
                * self.config.order_payment_mismatch_ratio
            ),
        }

        counts = {
            scenario: int(value)
            for scenario, value in raw_counts.items()
        }

        remaining = (
            self.config.case_count
            - sum(counts.values())
        )

        fractional = sorted(
            raw_counts.items(),
            key=lambda item: (
                item[1] - int(item[1])
            ),
            reverse=True,
        )

        for index in range(remaining):
            scenario = fractional[
                index % len(fractional)
            ][0]

            counts[scenario] += 1

        return [
            (
                "ABANDONED_CHECKOUT",
                counts[
                    "ABANDONED_CHECKOUT"
                ],
            ),
            (
                "AMBIGUOUS_PAYMENT",
                counts[
                    "AMBIGUOUS_PAYMENT"
                ],
            ),
            (
                "ORDER_PAYMENT_MISMATCH",
                counts[
                    "ORDER_PAYMENT_MISMATCH"
                ],
            ),
        ]

    def _generate_case(
        self,
        *,
        case_number: int,
        scenario_type: str,
    ) -> GeneratedCase:
        """
        Generate one synthetic RECOVER case.
        """

        merchant_index = (
            (case_number - 1)
            % self.config.merchant_count
        ) + 1

        merchant = create_merchant(
            rng=self.rng,
            merchant_index=merchant_index,
        )

        customer = create_customer(
            rng=self.rng,
            customer_index=case_number,
        )

        start = (
            self.config.start_date
            + self._case_time_offset(
                case_number
            )
        )

        if scenario_type == "ABANDONED_CHECKOUT":

            order, ground_truth = (
                generate_abandoned_checkout(
                    rng=self.rng,
                    merchant=merchant,
                    customer=customer,
                    case_index=case_number,
                    start=start,
                )
            )

            payment = None

        elif scenario_type == "AMBIGUOUS_PAYMENT":

            (
                order,
                payment,
                ground_truth,
            ) = generate_ambiguous_payment(
                rng=self.rng,
                merchant=merchant,
                customer=customer,
                case_index=case_number,
                start=start,
            )

        elif scenario_type == "ORDER_PAYMENT_MISMATCH":

            (
                order,
                payment,
                ground_truth,
            ) = generate_order_payment_mismatch(
                rng=self.rng,
                merchant=merchant,
                customer=customer,
                case_index=case_number,
                start=start,
            )

        else:
            raise ValueError(
                f"Unsupported scenario type: {scenario_type}"
            )

        true_events = (
            ground_truth.true_event_sequence
        )

        observed_events, disturbances = (
            build_observed_events(
                true_events=true_events,
                rng=self.rng,
                received_at_base=start,
            )
        )

        return create_case(
            case_number=case_number,
            merchant=merchant,
            customer=customer,
            order=order,
            payment=payment,
            scenario_type=scenario_type,
            ground_truth=ground_truth,
            observed_events=observed_events,
            disturbances=disturbances,
            generator_version=(
                self.config.generator_version
            ),
            seed=self.config.seed,
        )

    @staticmethod
    def _case_time_offset(
        case_number: int,
    ):
        """
        Produce deterministic spacing between generated cases.
        """

        from datetime import timedelta

        return timedelta(
            minutes=case_number - 1
        )


def generate_dataset(
    case_count: int = 100,
    seed: int = 42,
    generator_version: str = GENERATOR_VERSION,
) -> list[GeneratedCase]:
    """
    Public convenience API.
    """

    config = GeneratorConfig(
        case_count=case_count,
        seed=seed,
        generator_version=generator_version,
    )

    return DatasetGenerator(
        config
    ).generate()