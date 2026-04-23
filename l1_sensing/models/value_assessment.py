"""ProspectValueAssessment dataclass for L1 Sensing module."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class ProspectValueAssessment:
    """Prospect value assessment with weighted component scoring.

    Component weights must sum to 1.0:
    - need: 0.22
    - service_fit: 0.18
    - readiness: 0.14
    - accessibility: 0.10
    - expected_uplift: 0.18
    - economic_scale: 0.12
    - confidence: 0.06
    """
    # Component scores (0-100)
    need: float
    service_fit: float
    readiness: float
    accessibility: float
    expected_uplift: float
    economic_scale: float
    confidence: float

    # Total weighted score (0-100)
    total: float

    # Additional assessment data
    best_fit_services: List[str] = field(default_factory=list)
    priority_gaps: List[str] = field(default_factory=list)

    COMPONENT_WEIGHTS = {
        "need": 0.22,
        "service_fit": 0.18,
        "readiness": 0.14,
        "accessibility": 0.10,
        "expected_uplift": 0.18,
        "economic_scale": 0.12,
        "confidence": 0.06,
    }

    def __post_init__(self):
        """Validate all scores are in bounds."""
        components = [
            ("need", self.need),
            ("service_fit", self.service_fit),
            ("readiness", self.readiness),
            ("accessibility", self.accessibility),
            ("expected_uplift", self.expected_uplift),
            ("economic_scale", self.economic_scale),
            ("confidence", self.confidence),
            ("total", self.total),
        ]

        for name, value in components:
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be between 0 and 100, got {value}")

    @staticmethod
    def validate_weights() -> bool:
        """Verify component weights sum to 1.0."""
        total = sum(ProspectValueAssessment.COMPONENT_WEIGHTS.values())
        return abs(total - 1.0) < 0.001  # Allow for floating point precision
