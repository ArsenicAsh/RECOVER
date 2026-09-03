from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class EvaluationResult:
    chronology_correct: bool
    state_correct: bool
    contradiction_detection_correct: bool
    missing_evidence_awareness_correct: bool
    uncertainty_correct: bool
    passed: bool
    failures: tuple[str, ...] = field(default_factory=tuple)