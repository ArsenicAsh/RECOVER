from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from .models import ReconstructionEvent


class EvidenceStatus(StrEnum):
    OBSERVED = "OBSERVED"
    INFERRED = "INFERRED"
    UNKNOWN = "UNKNOWN"
    CONTRADICTORY = "CONTRADICTORY"


@dataclass(frozen=True)
class ClassifiedEvidence:
    event: ReconstructionEvent
    status: EvidenceStatus
    explanation: str


def classify_observed_events(
    events: tuple[ReconstructionEvent, ...],
) -> tuple[ClassifiedEvidence, ...]:
    """
    Classify currently observed events.

    At this stage every supplied event is direct evidence and therefore
    receives OBSERVED status.

    State inference, missing evidence, and contradiction detection are
    intentionally handled by later reconstruction stages.
    """

    return tuple(
        ClassifiedEvidence(
            event=event,
            status=EvidenceStatus.OBSERVED,
            explanation="Event is directly present in observed evidence.",
        )
        for event in events
    )