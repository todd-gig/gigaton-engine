"""Feedback loop and calibration models for closed-loop measurement."""

from dataclasses import dataclass
from enum import Enum


class FeedbackStage(str, Enum):
    """Enumeration of feedback loop stages per 13_measurement_and_feedback_loops.md."""

    OBSERVE = "observe"  # Stage 1: Observe action
    SCORE = "score"  # Stage 2: Score action
    ATTRIBUTE = "attribute"  # Stage 3: Attribute contribution
    COMPARE = "compare"  # Stage 4: Compare predicted vs realized outcome
    ADJUST = "adjust"  # Stage 5: Adjust confidence and calibration
    UPDATE = "update"  # Stage 6: Update benchmark weights or thresholds


@dataclass
class CalibrationRecord:
    """
    Records a single calibration cycle in the closed-loop measurement system.
    Tracks variance between predicted and realized outcomes.
    """

    record_id: str
    stage: FeedbackStage
    metric_name: str
    predicted_value: float
    realized_value: float
    variance: float  # predicted - realized
    confidence_adjustment: float  # how much to adjust confidence [-1.0, 1.0]
    timestamp: str = ""  # ISO 8601
    notes: str = ""

    def calculate_variance(self) -> float:
        """Calculate variance as predicted minus realized."""
        return self.predicted_value - self.realized_value

    def validate_confidence_adjustment(self) -> bool:
        """Verify confidence adjustment is within valid bounds."""
        return -1.0 <= self.confidence_adjustment <= 1.0

    def error_tolerance_met(self, tolerance_percent: float = 3.0) -> bool:
        """
        Check if variance is within acceptable error tolerance.
        Default 3% per 13_measurement_and_feedback_loops.md spec.
        Tolerance is calculated as a percentage of the realized value magnitude.
        """
        if self.realized_value == 0.0:
            # If realized was 0, predicted should also be 0
            return self.predicted_value == 0.0

        # Calculate tolerance as percentage of realized value
        tolerance = (tolerance_percent / 100.0) * abs(self.realized_value)
        return abs(self.variance) <= tolerance
