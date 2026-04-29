"""SegmentationEngine for customer classification and Apollo targeting.

Now consumes L2 brand assessment and L4 interaction performance data
to produce segmentation driven by actual brand coherence and interaction
effectiveness — not just prospect profile attributes.
"""

from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from l1_sensing.models.prospect import ProspectProfile, MaturityLevel
from l1_sensing.models.value_assessment import ProspectValueAssessment
from l2_brand_experience.models.brand_assessment import BrandExperienceAssessment
from segmentation.models.segment import CustomerSegment
from segmentation.segment_library import SEGMENT_LIBRARY


@dataclass
class InteractionPerformanceContext:
    """Summarized interaction performance metrics for segmentation.

    Aggregated from L4 interaction lifecycle data (Lead status distribution,
    Campaign performance, feedback loop variance, NOCS averages).
    """
    avg_nocs: float = 50.0                  # 0-100 average NOCS across interactions
    conversion_rate: float = 0.0            # 0-1 actual conversion rate
    avg_response_time_seconds: float = 300.0  # average response time
    avg_resolution_time_seconds: float = 3600.0  # average resolution time
    interaction_count: int = 0              # total interactions scored
    avg_sentiment: float = 0.5              # 0-1 average sentiment
    avg_trust_shift: float = 0.0            # -1 to +1 average trust delta
    escalation_rate: float = 0.0            # 0-1 ratio of escalated interactions
    abandonment_rate: float = 0.0           # 0-1 ratio of abandoned interactions

    @classmethod
    def from_interactions(cls, interactions: list) -> "InteractionPerformanceContext":
        """Build from a list of InteractionEvent objects."""
        if not interactions:
            return cls()

        count = len(interactions)
        converted = sum(1 for i in interactions if getattr(i, 'converted', False))
        escalated = sum(1 for i in interactions if getattr(i, 'escalated', False))
        abandoned = sum(1 for i in interactions if getattr(i, 'abandoned', False))

        response_times = [
            i.response_time_seconds for i in interactions
            if getattr(i, 'response_time_seconds', None) is not None
        ]
        resolution_times = [
            i.resolution_time_seconds for i in interactions
            if getattr(i, 'resolution_time_seconds', None) is not None
        ]
        sentiments = [
            getattr(i, 'sentiment_score', 0.5) for i in interactions
        ]
        trust_shifts = [
            getattr(i, 'trust_shift_score', 0.0) for i in interactions
        ]

        return cls(
            conversion_rate=converted / count,
            avg_response_time_seconds=sum(response_times) / len(response_times) if response_times else 300.0,
            avg_resolution_time_seconds=sum(resolution_times) / len(resolution_times) if resolution_times else 3600.0,
            interaction_count=count,
            avg_sentiment=sum(sentiments) / count,
            avg_trust_shift=sum(trust_shifts) / count,
            escalation_rate=escalated / count,
            abandonment_rate=abandoned / count,
        )


class SegmentationEngine:
    """Classifies prospects into customer segments using L1 + L2 + L4 data.

    Now consumes:
    - L1: ProspectProfile + ProspectValueAssessment (prospect attributes, fit scores)
    - L2: BrandExperienceAssessment (coherence, channel consistency, proof ratio)
    - L4: InteractionPerformanceContext (NOCS, conversion, sentiment, trust shift)
    """

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
        interaction_context: InteractionPerformanceContext = None,
    ) -> List[CustomerSegment]:
        """Classify a prospect into matching segments.

        Returns segments sorted by priority_tier (1 first),
        then by expected_value_range midpoint (highest first).

        Args:
            prospect: ProspectProfile to classify
            assessment: ProspectValueAssessment providing value dimensions
            brand_assessment: BrandExperienceAssessment for L2 brand coherence context
            interaction_context: InteractionPerformanceContext for L4 interaction data

        Returns:
            List of matching CustomerSegments, sorted by priority and value
        """
        matches = []

        for segment in self.segments.values():
            # L1 qualifying criteria are always required
            if not self._matches_criteria(
                segment.qualifying_criteria, prospect, assessment,
                brand_assessment, interaction_context,
            ):
                continue

            # L2 brand criteria — only evaluated when brand_assessment is provided
            if brand_assessment is not None and segment.brand_criteria:
                if not self._matches_criteria(
                    segment.brand_criteria, prospect, assessment,
                    brand_assessment, interaction_context,
                ):
                    continue

            # L4 interaction criteria — only evaluated when interaction_context is provided
            if interaction_context is not None and segment.interaction_criteria:
                if not self._matches_criteria(
                    segment.interaction_criteria, prospect, assessment,
                    brand_assessment, interaction_context,
                ):
                    continue

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
        interaction_context: InteractionPerformanceContext = None,
    ) -> Optional[CustomerSegment]:
        """Return the single best-fit segment, or None.

        Args:
            prospect: ProspectProfile to classify
            assessment: ProspectValueAssessment providing value dimensions
            brand_assessment: BrandExperienceAssessment for L2 context
            interaction_context: InteractionPerformanceContext for L4 data

        Returns:
            Best-matching CustomerSegment, or None if no matches
        """
        matches = self.classify(prospect, assessment, brand_assessment, interaction_context)
        return matches[0] if matches else None

    def get_apollo_targeting(
        self,
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
        brand_assessment: BrandExperienceAssessment = None,
        interaction_context: InteractionPerformanceContext = None,
    ) -> Optional[Dict[str, Any]]:
        """Get Apollo API filters for the best-fit segment.

        Args:
            prospect: ProspectProfile to classify
            assessment: ProspectValueAssessment providing value dimensions
            brand_assessment: BrandExperienceAssessment for L2 context
            interaction_context: InteractionPerformanceContext for L4 data

        Returns:
            Dict of Apollo API filters, or None if no segment matches
        """
        segment = self.classify_single(prospect, assessment, brand_assessment, interaction_context)
        if segment:
            return segment.apollo_targeting.to_apollo_filters()
        return None

    def _matches_criteria(
        self,
        criteria: Dict[str, Any],
        prospect: ProspectProfile,
        assessment: ProspectValueAssessment,
        brand_assessment: BrandExperienceAssessment = None,
        interaction_context: InteractionPerformanceContext = None,
    ) -> bool:
        """Check if prospect matches all qualifying criteria.

        Criteria format:
        - Numeric ranges: dimension_name → (min_threshold, max_threshold)
        - Enum matches: dimension_name → tuple of allowed values

        Now supports L1, L2, AND L4 dimension keys. See _get_dimension_value()
        for the full mapping.

        Args:
            criteria: Dict of criteria to check
            prospect: ProspectProfile to check against
            assessment: ProspectValueAssessment to check against
            brand_assessment: BrandExperienceAssessment to check against
            interaction_context: InteractionPerformanceContext to check against

        Returns:
            True if prospect matches all criteria, False otherwise
        """
        for dimension, constraint in criteria.items():
            value = self._get_dimension_value(
                dimension, prospect, assessment,
                brand_assessment, interaction_context,
            )

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
        brand_assessment: BrandExperienceAssessment = None,
        interaction_context: InteractionPerformanceContext = None,
    ) -> Any:
        """Extract dimension value from prospect, assessment, brand, or interaction data.

        L1 Assessment dimensions (numeric 0-100):
            economic_scale, fit_score, need, service_fit, readiness,
            accessibility, expected_uplift, confidence

        L1 Prospect capability dimensions (string enum):
            marketing_maturity, sales_complexity, measurement_maturity,
            interaction_management_maturity, gtm_motion

        L2 Brand dimensions (numeric):
            brand_experience_score (0-100), brand_coherence_composite (0-100),
            brand_coherence_coefficient (0-1.25), channel_consistency (0-100),
            proof_to_promise_ratio (0-1), trust_layer_quality (0-100),
            brand_response_performance (0-1), brand_conversion_performance (0-1),
            ethos_truthfulness (0-100), ethos_human_centered (0-100),
            ethos_long_term_value (0-100), ethos_cost_roi (0-100),
            ethos_human_agency (0-100), ethos_trust_contribution (0-100),
            ethos_manipulation_avoidance (0-100)

        L4 Interaction dimensions (numeric):
            interaction_nocs (0-100), interaction_conversion_rate (0-1),
            interaction_sentiment (0-1), interaction_trust_shift (-1 to 1),
            interaction_escalation_rate (0-1), interaction_abandonment_rate (0-1),
            interaction_count (integer)

        Args:
            dimension: Dimension key
            prospect: ProspectProfile
            assessment: ProspectValueAssessment
            brand_assessment: BrandExperienceAssessment (optional)
            interaction_context: InteractionPerformanceContext (optional)

        Returns:
            Dimension value, or None if not found or data source not available
        """
        # ── L1: Assessment dimensions (numeric 0-100) ──
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

        # ── L1: Prospect capability dimensions (MaturityLevel enums) ──
        if dimension == "marketing_maturity":
            return prospect.capability_summary.marketing_maturity.value
        if dimension == "sales_complexity":
            return prospect.capability_summary.sales_complexity.value
        if dimension == "measurement_maturity":
            return prospect.capability_summary.measurement_maturity.value
        if dimension == "interaction_management_maturity":
            return prospect.capability_summary.interaction_management_maturity.value
        if dimension == "gtm_motion":
            return prospect.gtm_motion.value

        # ── L2: Brand experience dimensions ──
        if brand_assessment is not None:
            if dimension == "brand_experience_score":
                return brand_assessment.brand_experience_score
            if dimension == "brand_coherence_composite":
                return brand_assessment.coherence.composite_score
            if dimension == "brand_coherence_coefficient":
                return brand_assessment.coherence.coefficient
            if dimension == "channel_consistency":
                return brand_assessment.channel_consistency_score
            if dimension == "proof_to_promise_ratio":
                return brand_assessment.proof_to_promise_ratio
            if dimension == "trust_layer_quality":
                return brand_assessment.trust_layer_quality
            if dimension == "brand_response_performance":
                return brand_assessment.avg_response_performance
            if dimension == "brand_conversion_performance":
                return brand_assessment.conversion_performance
            # Individual ethos dimensions
            if dimension == "ethos_truthfulness":
                return brand_assessment.coherence.truthfulness_explainability
            if dimension == "ethos_human_centered":
                return brand_assessment.coherence.human_centered_technology
            if dimension == "ethos_long_term_value":
                return brand_assessment.coherence.long_term_value_creation
            if dimension == "ethos_cost_roi":
                return brand_assessment.coherence.cost_roi_discipline
            if dimension == "ethos_human_agency":
                return brand_assessment.coherence.human_agency_respect
            if dimension == "ethos_trust_contribution":
                return brand_assessment.coherence.trust_contribution
            if dimension == "ethos_manipulation_avoidance":
                return brand_assessment.coherence.manipulation_avoidance

        # ── L4: Interaction performance dimensions ──
        if interaction_context is not None:
            if dimension == "interaction_nocs":
                return interaction_context.avg_nocs
            if dimension == "interaction_conversion_rate":
                return interaction_context.conversion_rate
            if dimension == "interaction_sentiment":
                return interaction_context.avg_sentiment
            if dimension == "interaction_trust_shift":
                return interaction_context.avg_trust_shift
            if dimension == "interaction_escalation_rate":
                return interaction_context.escalation_rate
            if dimension == "interaction_abandonment_rate":
                return interaction_context.abandonment_rate
            if dimension == "interaction_count":
                return interaction_context.interaction_count

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
