from __future__ import annotations

from app.domain.models.case import ReconstructionStatus
from app.domain.models.order import OrderStatus
from app.domain.models.payment import PaymentStatus

from .models import Contradiction, InferredTransition, ReconstructionEvent


def build_explanation(
    *,
    events: tuple[ReconstructionEvent, ...],
    payment_state: PaymentStatus | None,
    order_state: OrderStatus | None,
    reconstruction_status: ReconstructionStatus,
    missing_expected_evidence: tuple[str, ...],
    contradictions: tuple[Contradiction, ...],
    inferred_transitions: tuple[InferredTransition, ...],
    uncertainty: tuple[str, ...],
) -> str:
    """
    Build a deterministic human-readable explanation from reconstruction
    evidence and derived state.

    This function only describes information supported by the supplied
    reconstruction outputs.
    """
    parts: list[str] = []

    if events:
        parts.append(
            f"{len(events)} observed event(s) were reconstructed chronologically."
        )
    else:
        parts.append("No observed events were available for reconstruction.")

    if payment_state is not None:
        parts.append(
            f"Reconstructed payment state: {payment_state.value}."
        )
    elif any(event.event_type.startswith("payment.") for event in events):
        parts.append(
            "A definitive payment state could not be established from "
            "the available payment evidence."
        )

    if order_state is not None:
        parts.append(
            f"Reconstructed order state: {order_state.value}."
        )

    if inferred_transitions:
        transition_text = "; ".join(
            (
                f"{transition.entity} transitioned from "
                f"{transition.from_state or 'UNKNOWN'} to "
                f"{transition.to_state}"
            )
            for transition in inferred_transitions
        )
        parts.append(f"Inferred transitions: {transition_text}.")

    if missing_expected_evidence:
        parts.append(
            "Expected evidence is missing: "
            + ", ".join(missing_expected_evidence)
            + "."
        )

    if contradictions:
        parts.append(
            f"{len(contradictions)} contradiction(s) were detected in the "
            "observed evidence."
        )

    if uncertainty:
        parts.append(
            "Uncertainty: " + " ".join(uncertainty)
        )

    parts.append(
        f"Reconstruction status: {reconstruction_status.value}."
    )

    return " ".join(parts)