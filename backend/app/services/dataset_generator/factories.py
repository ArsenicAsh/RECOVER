from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.dataset_generator.models import (
    GeneratedCase,
    GroundTruthEvent,
)


CURRENCIES = ("INR",)

PAYMENT_METHODS = (
    "card",
    "upi",
    "netbanking",
    "wallet",
)

AMOUNT_OPTIONS = (
    499,
    799,
    999,
    1499,
    1999,
    2499,
    2999,
    4999,
    7999,
    9999,
)


def deterministic_uuid(rng: random.Random) -> uuid.UUID:
    """
    Generate a deterministic UUID from the supplied RNG.
    """

    return uuid.UUID(
        int=rng.getrandbits(128)
    )


def choose_amount(
    rng: random.Random,
) -> int:
    """Choose a deterministic synthetic amount."""

    return rng.choice(
        AMOUNT_OPTIONS
    )


def choose_currency(
    rng: random.Random,
) -> str:
    """Choose a deterministic currency."""

    return rng.choice(
        CURRENCIES
    )


def choose_payment_method(
    rng: random.Random,
) -> str:
    """Choose a deterministic payment method."""

    return rng.choice(
        PAYMENT_METHODS
    )


def create_merchant(
    rng: random.Random,
    merchant_index: int,
) -> dict[str, Any]:
    """
    Create a synthetic merchant.
    """

    merchant_id = deterministic_uuid(rng)

    return {
        "id": merchant_id,
        "name": f"Merchant {merchant_index:03d}",
        "external_ref": f"merchant_{merchant_index:03d}",
        "currency": choose_currency(rng),
    }


def create_customer(
    rng: random.Random,
    customer_index: int,
) -> dict[str, Any]:
    """
    Create a synthetic customer.
    """

    customer_id = deterministic_uuid(rng)

    return {
        "id": customer_id,
        "name": f"Customer {customer_index:03d}",
        "external_ref": f"customer_{customer_index:03d}",
    }


def create_order(
    rng: random.Random,
    merchant_id: uuid.UUID,
    customer_id: uuid.UUID,
    case_index: int,
    amount: int,
    currency: str,
    *,
    status: str,
) -> dict[str, Any]:
    """
    Create a synthetic order.

    Signature intentionally matches the scenario-generation
    contract used by scenarios.py.
    """

    order_id = deterministic_uuid(rng)

    return {
        "id": order_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "external_ref": f"order_{case_index:04d}",
        "amount": amount,
        "currency": currency,
        "status": status,
        "metadata": {
            "synthetic": True,
            "case_index": case_index,
        },
    }


def create_payment(
    rng: random.Random,
    merchant_id: uuid.UUID,
    customer_id: uuid.UUID,
    order_id: uuid.UUID,
    amount: int,
    currency: str,
    *,
    status: str,
) -> dict[str, Any]:
    """
    Create a synthetic payment.

    Signature intentionally matches the scenario-generation
    contract used by scenarios.py.
    """

    payment_id = deterministic_uuid(rng)

    return {
        "id": payment_id,
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "order_id": order_id,
        "amount": amount,
        "currency": currency,
        "method": choose_payment_method(rng),
        "status": status,
        "authorized_at": None,
        "captured_at": None,
        "failed_at": None,
        "refunded_at": None,
        "razorpay_payment_id": (
            f"pay_sim_{payment_id.hex[:16]}"
        ),
        "metadata": {
            "synthetic": True,
        },
    }


def make_event(
    rng: random.Random,
    *,
    event_type: str,
    occurred_at: datetime,
    source: str,
    merchant_id: uuid.UUID,
    customer_id: uuid.UUID | None = None,
    order_id: uuid.UUID | None = None,
    payment_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
) -> GroundTruthEvent:
    """
    Create a canonical synthetic ground-truth event.
    """

    event_uuid = deterministic_uuid(rng)

    return GroundTruthEvent(
        event_id=f"evt_{event_uuid.hex}",
        event_type=event_type,
        occurred_at=occurred_at,
        source=source,
        merchant_id=merchant_id,
        customer_id=customer_id,
        order_id=order_id,
        payment_id=payment_id,
        payload=payload or {},
    )


def timeline(
    start: datetime,
    *,
    minutes: int = 0,
    seconds: int = 0,
) -> datetime:
    """
    Produce a deterministic event timestamp relative to
    scenario start.
    """

    if start.tzinfo is None:
        start = start.replace(
            tzinfo=timezone.utc
        )

    return start + timedelta(
        minutes=minutes,
        seconds=seconds,
    )


def create_case(
    *,
    case_number: int,
    merchant: dict[str, Any],
    customer: dict[str, Any],
    order: dict[str, Any],
    payment: dict[str, Any] | None,
    scenario_type: str,
    ground_truth: Any,
    observed_events: list[Any],
    disturbances: list[Any],
    generator_version: str,
    seed: int,
) -> GeneratedCase:
    """
    Assemble the final GeneratedCase.

    Ground truth and observed events remain separate objects.
    """

    case_id = deterministic_uuid(
        random.Random(
            f"{seed}:{case_number}"
        )
    )

    return GeneratedCase(
        case_id=str(case_id),
        case_number=f"CASE-{case_number:04d}",

        merchant_id=str(
            merchant["id"]
        ),
        customer_id=str(
            customer["id"]
        ),
        order_id=str(
            order["id"]
        ),
        payment_id=(
            str(payment["id"])
            if payment is not None
            else None
        ),

        amount=(
            order["amount"]
        ),
        currency=order["currency"],

        scenario_type=scenario_type,

        observed_events=observed_events,
        disturbances=disturbances,
        ground_truth=ground_truth,

        # Compatibility fields expected by the current test contract.
        payment=payment,
        true_events=ground_truth.true_event_sequence,
        generator_version=generator_version,
        seed=seed,
    )


# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------

make_merchant = create_merchant
make_customer = create_customer
make_order = create_order
make_payment = create_payment