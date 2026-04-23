"""InferenceRecord dataclass for L1 Sensing module."""

from dataclasses import dataclass, field
from typing import List
from enum import Enum


class InferenceType(str, Enum):
    """Type of inference about a prospect."""
    BUSINESS_GOAL = "business_goal"
    GTM_MOTION = "gtm_motion"
    MARKET_POSITIONING = "market_positioning"
    CAPABILITY_MATURITY = "capability_maturity"
    PAIN_POINT = "pain_point"
    SERVICE_FIT = "service_fit"
    VALUE_ESTIMATE = "value_estimate"


@dataclass
class InferenceRecord:
    """High-confidence inference from signal analysis."""
    object_id: str
    prospect_id: str
    inference_type: InferenceType
    statement: str
    confidence: float  # 0-1
    assumptions: List[str] = field(default_factory=list)
    missing_data: List[str] = field(default_factory=list)
    evidence_ids: List[str] = field(default_factory=list)

    def __post_init__(self):
        """Validate confidence is within bounds."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Confidence must be between 0 and 1, got {self.confidence}")
