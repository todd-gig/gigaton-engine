"""SegmentationEngine for customer classification and Apollo targeting."""

from typing import List, Optional, Dict, Any, Tuple
from l1_sensing.models.prospect import ProspectProfile, MaturityLevel
from l1_sensing.models.value_assessment import ProspectValueAssessment
from l2_brand_experience.models.brand_assessment import BrandExperienceAssessment
from segmentation.models.segment import CustomerSegment
from segmentation.segment_library import SEGMENT_LIBRARY


class SegmentationEngine:
    """Classifies prospects into customer segments and generates Apollo targeting."""

    def __init__(self, segment_library: Dict[str, CustomerSegment] = None):
        """Initialize with segment library.

        Args:
            segment_library: Dict of segment_key -> CustomerSegment. Defaults to SEGMENT_LIBRARY.
        """
        self.segments = segment_library or SEGMENT_LIBRARY

    def classify(
        self,
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
        brand_assessment: BrandExperienceAssessment = None,
    ) -> List[CustomerSegment]:
        """Classify a prospect into matching segments.

        Returns segments sorted by priority_tier (1 first),
        then by expected_value_range midpoint (highest first).

        Args:
            prospect: ProspectProfile to classify
            assessment: ProspectValueAssessment providing value dimensions
            brand_assessment: Optional BrandExperienceAssessment for L2 context

        Returns:
            List of matching CustomerSegments, sorted by priority and value
        """
        matches = []

        for segment in self.segments.values():
            if self._matches_criteria(segment.qualifying_criteria, prospect, assessment):
                matches.append(segment)

        # Sort by priority_tier (ascending, so 1 comes first),
        # then by expected_value_range midpoint (descending, highest value first)
        matches.sort(
            key=lambda s: (
                s.priority_tier,
                -((s.expected_value_range[0] + s.expected_value_range[1]) / 2),
            )
        )

        return matches

    def classify_single(
        self,
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
        brand_assessment: BrandExperienceAssessment = None,
    ) -> Optional[CustomerSegment]:
        """Return the single best-fit segment, or None.

        Args:
            prospect: ProspectProfile to classify
            assessment: ProspectValueAssessment providing value dimensions
            brand_assessment: Optional BrandExperienceAssessment for L2 context

        Returns:
            Best-matching CustomerSegment, or None if no matches
        """
        matches = self.classify(prospect, assessment, brand_assessment)
        return matches[0] if matches else None

    def get_apollo_targeting(
        self,
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
    ) -> Optional[Dict[str, Any]]:
        """Get Apollo API filters for the best-fit segment.

        Args:
            prospect: ProspectProfile to classify
            assessment: ProspectValueAssessment providing value dimensions

        Returns:
            Dict of Apollo API filters, or None if no segment matches
        """
        segment = self.classify_single(prospect, assessment)
        if segment:
            return segment.apollo_targeting.to_apollo_filters()
        return None

    def _matches_criteria(
        self,
        criteria: Dict[str, Any],
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
    ) -> bool:
        """Check if prospect matches all qualifying criteria.

        Criteria format:
        - Numeric ranges: dimension_name → (min_threshold, max_threshold)
        - Enum matches: dimension_name → tuple of allowed values

        Maps criteria keys to prospect/assessment fields:
        - "economic_scale" → assessment.economic_scale
        - "fit_score" → assessment.total
        - "marketing_maturity" → prospect.capability_summary.marketing_maturity.value
        - "sales_complexity" → prospect.capability_summary.sales_complexity.value
        - "measurement_maturity" → prospect.capability_summary.measurement_maturity.value
        - "interaction_management_maturity" → prospect.capability_summary.interaction_management_maturity.value
        - "gtm_motion" → prospect.gtm_motion.value

        Args:
            criteria: Dict of criteria to check
            prospect: ProspectProfile to check against
            assessment: ProspectValueAssessment to check against

        Returns:
            True if prospect matches all criteria, False otherwise
        """
        for dimension, constraint in criteria.items():
            value = self._get_dimension_value(dimension, prospect, assessment)

            if value is None:
                # Missing value fails the match
                return False

            # Check constraint
            if not self._matches_constraint(value, constraint):
                return False

        return True

    def _get_dimension_value(
        self,
        dimension: str,
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
    ) -> Any:
        """Extract dimension value from prospect or assessment.

        Args:
            dimension: Dimension name (e.g., "economic_scale", "marketing_maturity")
            prospect: ProspectProfile
            assessment: ProspectValueAssessment

        Returns:
            Dimension value, or None if not found
        """
        # Assessment dimensions (numeric 0-100)
        if dimension == "economic_scale":
            return assessment.economic_scale
        if dimension == "fit_score":
            return assessment.total
        if dimension == "need":
            return assessment.need
        if dimension == "service_fit":
            return assessment.service_fit
        if dimension == "readiness":
            return assessment.readiness
        if dimension == "accessibility":
            return assessment.accessibility
        if dimension == "expected_uplift":
            return assessment.expected_uplift
        if dimension == "confidence":
            return assessment.confidence

        # Prospect capability dimensions (MaturityLevel enums)
        if dimension == "marketing_maturity":
            return prospect.capability_summary.marketing_maturity.value
        if dimension == "sales_complexity":
            return prospect.capability_summary.sales_complexity.value
        if dimension == "measurement_maturity":
            return prospect.capability_summary.measurement_maturity.value
        if dimension == "interaction_management_maturity":
            return prospect.capability_summary.interaction_management_maturity.value

        # Prospect GTM motion
        if dimension == "gtm_motion":
            return prospect.gtm_motion.value

        return None

    def _matches_constraint(self, value: Any, constraint: Any) -> bool:
        """Check if a value matches a constraint.

        Constraint formats:
        - Tuple of 2 numbers: numeric range (min, max) — inclusive on both ends
        - Tuple of strings: enum set — value must be in set
        - Single string: exact match

        Args:
            value: The dimension value to check
            constraint: The constraint specification

        Returns:
            True if value matches constraint, False otherwise
        """
        # String enum set: constraint is tuple of allowed string values
        if isinstance(constraint, tuple) and len(constraint) > 0 and isinstance(
            constraint[0], str
        ):
            return value in constraint

        # Numeric range: constraint is (min, max) tuple
        if isinstance(constraint, tuple) and len(constraint) == 2:
            if isinstance(constraint[0], (int, float)) and isinstance(
                constraint[1], (int, float)
            ):
                return constraint[0] <= value <= constraint[1]

        # Single value match
        return value == constraint
