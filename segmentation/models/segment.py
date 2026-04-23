"""CustomerSegment dataclass for customer segmentation."""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from .segment_criteria import ApolloTargeting


@dataclass
class CustomerSegment:
    """Represents a customer segment with qualifying criteria and Apollo targeting."""

    segment_id: str
    segment_name: str
    description: str
    # Qualifying criteria — what makes a prospect fit this segment
    # Format: dimension_name → (min_threshold, max_threshold) for numeric
    # or dimension_name → tuple of allowed values for enums
    qualifying_criteria: Dict[str, Any]
    # What we sell them
    service_package_fit: List[str]
    # Expected value (0-100 scale)
    expected_value_range: Tuple[float, float]
    # Priority in our pipeline (1=highest, 3=lowest)
    priority_tier: int
    # Serviceability gap pattern (from the 8 patterns)
    primary_gap_pattern: str
    # Apollo targeting output
    apollo_targeting: ApolloTargeting
