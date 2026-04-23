"""BrandCoherenceScore model for tracking ethos alignment dimensions."""

from dataclasses import dataclass


@dataclass
class BrandCoherenceScore:
    """Tracks 7 ethos dimensions and derived composite score and coefficient."""

    # Seven ethos dimensions (0-100 scale)
    truthfulness_explainability: float = 50.0
    human_centered_technology: float = 50.0
    long_term_value_creation: float = 50.0
    cost_roi_discipline: float = 50.0
    human_agency_respect: float = 50.0
    trust_contribution: float = 50.0
    manipulation_avoidance: float = 50.0

    # Composite and coefficient
    composite_score: float = 50.0  # Weighted average of the 7 dimensions
    coefficient: float = 0.75  # 0.00-1.25 derived from composite_score

    def validate_bounds(self) -> bool:
        """Verify all dimension scores are within bounds 0-100."""
        dimensions = [
            self.truthfulness_explainability,
            self.human_centered_technology,
            self.long_term_value_creation,
            self.cost_roi_discipline,
            self.human_agency_respect,
            self.trust_contribution,
            self.manipulation_avoidance,
        ]
        return all(0.0 <= d <= 100.0 for d in dimensions)

    def is_disqualifying(self) -> bool:
        """Check if composite score is below disqualifying threshold (50.0)."""
        return self.composite_score < 50.0
