from __future__ import annotations

from app.domain.models.case import (
    MoneyState,
    ReconstructionStatus,
    WorkflowState,
)
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus

from .models import StateInput, StateResult


def run_state_engine(state_input: StateInput) -> StateResult:
    reconstruction = state_input.reconstruction

    payment_status = reconstruction.payment_state
    order_status = reconstruction.order_state

    evidence_event_ids = tuple(
        event.event_id
        for event in reconstruction.chronological_events
    )

    # ---------------------------------------------------------
    # Conflicting evidence
    # ---------------------------------------------------------
    if reconstruction.reconstruction_status == ReconstructionStatus.CONFLICTED:
        return StateResult(
            workflow_state=WorkflowState.ESCALATED,
            money_state=MoneyState.UNKNOWN,
            reconstruction_status=reconstruction.reconstruction_status,
            payment_status=payment_status,
            order_status=order_status,
            mismatch=None,
            requires_verification=True,
            evidence_event_ids=evidence_event_ids,
            explanation=(
                "The reconstructed evidence contains contradictions. "
                "The case requires verification before a definitive "
                "financial state can be established."
            ),
        )

    # ---------------------------------------------------------
    # Incomplete evidence
    # ---------------------------------------------------------
    if reconstruction.reconstruction_status == ReconstructionStatus.PARTIAL:
        return StateResult(
            workflow_state=WorkflowState.INVESTIGATING,
            money_state=MoneyState.UNKNOWN,
            reconstruction_status=reconstruction.reconstruction_status,
            payment_status=payment_status,
            order_status=order_status,
            mismatch=None,
            requires_verification=True,
            evidence_event_ids=evidence_event_ids,
            explanation=(
                "The available evidence is incomplete. Further "
                "verification is required before determining the "
                "definitive financial outcome."
            ),
        )

    # ---------------------------------------------------------
    # Abandoned checkout
    #
    # Evidence-based inference:
    #   checkout.abandoned
    #   + no payment evidence
    #
    # This does not rely on a scenario label or ground truth.
    # ---------------------------------------------------------
    checkout_abandoned = any(
        event.event_type == "checkout.abandoned"
        for event in reconstruction.chronological_events
    )

    has_payment_evidence = any(
        event.event_type.startswith("payment.")
        for event in reconstruction.chronological_events
    )

    if checkout_abandoned and not has_payment_evidence:
        return StateResult(
            workflow_state=WorkflowState.DECISION_READY,
            money_state=MoneyState.RECOVERABLE,
            reconstruction_status=reconstruction.reconstruction_status,
            payment_status=payment_status,
            order_status=order_status,
            mismatch=None,
            requires_verification=False,
            evidence_event_ids=evidence_event_ids,
            explanation=(
                "Checkout was abandoned and no payment evidence was "
                "observed. The case is recoverable through customer "
                "outreach."
            ),
        )

    # ---------------------------------------------------------
    # Captured payment
    # ---------------------------------------------------------
    if payment_status == PaymentStatus.CAPTURED:

        # Explicitly paid order.
        if order_status == OrderStatus.PAID:
            return StateResult(
                workflow_state=WorkflowState.RECOVERED,
                money_state=MoneyState.RESOLVED,
                reconstruction_status=reconstruction.reconstruction_status,
                payment_status=payment_status,
                order_status=order_status,
                mismatch=False,
                requires_verification=False,
                evidence_event_ids=evidence_event_ids,
                explanation=(
                    "Payment was captured and the order is explicitly "
                    "marked paid."
                ),
            )

        # Payment captured but no paid order state established.
        #
        # CREATED is intentionally included here because the event
        # evidence may establish order creation without establishing
        # an authoritative unpaid state.
        if order_status in {OrderStatus.UNPAID, OrderStatus.CREATED}:
            return StateResult(
                workflow_state=WorkflowState.DECISION_READY,
                money_state=MoneyState.AT_RISK,
                reconstruction_status=reconstruction.reconstruction_status,
                payment_status=payment_status,
                order_status=order_status,
                mismatch=True,
                requires_verification=True,
                evidence_event_ids=evidence_event_ids,
                explanation=(
                    "Payment was captured, but no paid order state is "
                    "established by the observed evidence. The payment "
                    "and order states require reconciliation."
                ),
            )

    # ---------------------------------------------------------
    # Terminal payment states
    # ---------------------------------------------------------
    if payment_status in {
        PaymentStatus.FAILED,
        PaymentStatus.REFUNDED,
    }:
        return StateResult(
            workflow_state=WorkflowState.RESOLVED,
            money_state=MoneyState.RESOLVED,
            reconstruction_status=reconstruction.reconstruction_status,
            payment_status=payment_status,
            order_status=order_status,
            mismatch=None,
            requires_verification=False,
            evidence_event_ids=evidence_event_ids,
            explanation=(
                f"Payment reached terminal state "
                f"{payment_status.value}."
            ),
        )

    # ---------------------------------------------------------
    # No definitive financial outcome
    # ---------------------------------------------------------
    return StateResult(
        workflow_state=WorkflowState.INVESTIGATING,
        money_state=MoneyState.UNKNOWN,
        reconstruction_status=reconstruction.reconstruction_status,
        payment_status=payment_status,
        order_status=order_status,
        mismatch=None,
        requires_verification=True,
        evidence_event_ids=evidence_event_ids,
        explanation=(
            "The reconstructed evidence does not establish a "
            "definitive financial outcome."
        ),
    )