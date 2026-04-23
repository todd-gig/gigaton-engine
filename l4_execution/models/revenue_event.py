"""RevenueEvent model for tracking revenue attribution and types."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class RevenueEvent:
    """Represents a revenue event with interaction attribution."""

    revenue_event_id: str
    lead_id: str
    amount: float
    revenue_type: str = "new"  # new, expansion, renewal, retained
    attribution_interactions: List[str] = field(default_factory=list)  # interaction_ids
    timestamp: str = ""  # ISO 8601
    confidence: float = 0.5  # 0.0-1.0: confidence in attribution

    def validate_amount(self) -> bool:
        """Verify revenue amount is positive."""
        return self.amount >= 0.0

    def validate_confidence(self) -> bool:
        """Verify confidence is within valid bounds."""
        return 0.0 <= self.confidence <= 1.0

    def adjust_confidence(self, adjustment: float) -> bool:
        """
        Adjust confidence by the given amount.
        Used by feedback loop calibration.
        """
        new_confidence = self.confidence + adjustment
        if 0.0 <= new_confidence <= 1.0:
            self.confidence = new_confidence
            return True
        return False
