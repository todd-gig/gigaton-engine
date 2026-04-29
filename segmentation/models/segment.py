"""CustomerSegment dataclass for customer segmentation."""

from dataclasses import dataclass, field
from typing import List, Tuple, Dict, Any
from .segment_criteria import ApolloTargeting


@dataclass
class CustomerSegment:
    """Represents a customer segment with qualifying criteria and Apollo targeting.

    Criteria are organized in three tiers:
    - qualifying_criteria: L1 prospect attributes (always evaluated)
    - brand_criteria: L2 brand coherence dimensions (evaluated only when brand data available)
    - interaction_criteria: L4 interaction performance dimensions (evaluated only when data available)

    This tiered approach enables graceful degradation — segmentation works with
    L1 data alone but becomes more precise as L2 and L4 data become available.
    """

    segment_id: str
    segment_name: str
    description: str
    # L1 qualifying criteria — what makes a prospect fit this segment
    # Format: dimension_name → (min_threshold, max_threshold) for numeric
    # or dimension_name → tuple of allowed values for enums
    qualifying_criteria: Dict[str, Any]
    # L2 brand criteria — evaluated only when brand_assessment is provided
    # Uses brand dimension keys (brand_experience_score, brand_coherence_composite, etc.)
    brand_criteria: Dict[str, Any] = field(default_factory=dict)
    # L4 interaction criteria — evaluated only when interaction_context is provided
    # Uses interaction dimension keys (interaction_nocs, interaction_conversion_rate, etc.)
    interaction_criteria: Dict[str, Any] = field(default_factory=dict)
    # What we sell them
    service_package_fit: List[str] = field(default_factory=list)
    # Expected value (0-100 scale)
    expected_value_range: Tuple[float, float] = (0, 100)
    # Priority in our pipeline (1=highest, 3=lowest)
    priority_tier: int = 2
    # Serviceability gap pattern (from the 8 patterns)
    primary_gap_pattern: str = ""
    # Apollo targeting output
    apollo_targeting: ApolloTargeting = field(default_factory=ApolloTargeting)
