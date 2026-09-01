from __future__ import annotations

import random
from datetime import datetime
from typing import Any

from app.services.dataset_generator.factories import (
    choose_amount,
    make_event,
    make_order,
    make_payment,
    timeline,
)
from app.services.dataset_generator.models import GroundTruth, GroundTruthEvent


def generate_abandoned_checkout(
    rng: random.Random,
    *,
    merchant: dict[str, Any],
    customer: dict[str, Any],
    case_index: int,
    start: datetime,
) -> tuple[dict[str, Any], GroundTruth]:
    """
    Generate an ABANDONED_CHECKOUT scenario.

    No payment entity is created because the customer abandons
    before successful payment completion.
    """

    amount = choose_amount(rng)

    order = make_order(
        rng,
        merchant["id"],
        customer["id"],
        case_index,
        amount,
        merchant["currency"],
        status="UNPAID",
    )

    events = [
        make_event(
            rng,
            event_type="order.created",
            occurred_at=timeline(start, minutes=0),
            source="merchant",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="checkout.started",
            occurred_at=timeline(start, minutes=2),
            source="merchant",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="checkout.abandoned",
            occurred_at=timeline(start, minutes=17),
            source="merchant",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payload={
                "reason": "customer_abandoned",
            },
        ),
    ]

    ground_truth = GroundTruth(
        scenario_type="ABANDONED_CHECKOUT",
        true_event_sequence=events,
        true_money_state="RECOVERABLE",
        true_workflow_condition="CUSTOMER_ABANDONED_BEFORE_PAYMENT_COMPLETION",
        expected_reconstruction={
            "order_status": "UNPAID",
            "payment_exists": False,
            "checkout_abandoned": True,
            "recoverable": True,
        },
        expected_action="RECOVERY_OUTREACH",
        expected_outcome="RECOVERY_PENDING",
    )

    return order, ground_truth


def generate_ambiguous_payment(
    rng: random.Random,
    *,
    merchant: dict[str, Any],
    customer: dict[str, Any],
    case_index: int,
    start: datetime,
) -> tuple[dict[str, Any], dict[str, Any], GroundTruth]:
    """
    Generate an AMBIGUOUS_PAYMENT scenario.

    The payment evidence is intentionally incomplete/ambiguous.
    """

    amount = choose_amount(rng)

    order = make_order(
        rng,
        merchant["id"],
        customer["id"],
        case_index,
        amount,
        merchant["currency"],
        status="UNPAID",
    )

    payment = make_payment(
        rng,
        merchant["id"],
        customer["id"],
        order["id"],
        amount,
        merchant["currency"],
        status="INITIATED",
    )

    events = [
        make_event(
            rng,
            event_type="order.created",
            occurred_at=timeline(start, minutes=0),
            source="merchant",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="payment.initiated",
            occurred_at=timeline(start, minutes=1),
            source="razorpay",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payment_id=payment["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="payment.authorized",
            occurred_at=timeline(start, minutes=3),
            source="razorpay",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payment_id=payment["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
    ]

    ground_truth = GroundTruth(
        scenario_type="AMBIGUOUS_PAYMENT",
        true_event_sequence=events,
        true_money_state="UNKNOWN",
        true_workflow_condition="PAYMENT_OUTCOME_UNCERTAIN",
        expected_reconstruction={
            "payment_exists": True,
            "payment_status": "UNCERTAIN",
            "order_status": "UNPAID",
            "money_state": "UNKNOWN",
        },
        expected_action="MANUAL_RECONCILIATION",
        expected_outcome="PENDING_RECONCILIATION",
    )

    return order, payment, ground_truth


def generate_order_payment_mismatch(
    rng: random.Random,
    *,
    merchant: dict[str, Any],
    customer: dict[str, Any],
    case_index: int,
    start: datetime,
) -> tuple[dict[str, Any], dict[str, Any], GroundTruth]:
    """
    Generate an ORDER_PAYMENT_MISMATCH scenario.

    Payment evidence says the payment succeeded while the merchant
    order remains unpaid.
    """

    amount = choose_amount(rng)

    order = make_order(
        rng,
        merchant["id"],
        customer["id"],
        case_index,
        amount,
        merchant["currency"],
        status="UNPAID",
    )

    payment = make_payment(
        rng,
        merchant["id"],
        customer["id"],
        order["id"],
        amount,
        merchant["currency"],
        status="CAPTURED",
    )

    payment["captured_at"] = timeline(start, minutes=7)

    events = [
        make_event(
            rng,
            event_type="order.created",
            occurred_at=timeline(start, minutes=0),
            source="merchant",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="payment.initiated",
            occurred_at=timeline(start, minutes=1),
            source="razorpay",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payment_id=payment["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="payment.authorized",
            occurred_at=timeline(start, minutes=4),
            source="razorpay",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payment_id=payment["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
        make_event(
            rng,
            event_type="payment.captured",
            occurred_at=timeline(start, minutes=7),
            source="razorpay",
            merchant_id=merchant["id"],
            customer_id=customer["id"],
            order_id=order["id"],
            payment_id=payment["id"],
            payload={
                "amount": amount,
                "currency": merchant["currency"],
            },
        ),
    ]

    ground_truth = GroundTruth(
        scenario_type="ORDER_PAYMENT_MISMATCH",
        true_event_sequence=events,
        true_money_state="AT_RISK",
        true_workflow_condition="PAYMENT_CAPTURED_ORDER_UNPAID",
        expected_reconstruction={
            "payment_exists": True,
            "payment_status": "CAPTURED",
            "payment_amount": amount,
            "order_status": "UNPAID",
            "mismatch": True,
        },
        expected_action="ORDER_RECONCILIATION",
        expected_outcome="ORDER_RECONCILIATION_PENDING",
    )

    return order, payment, ground_truth