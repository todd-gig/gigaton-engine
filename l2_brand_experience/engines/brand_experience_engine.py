"""BrandExperienceEngine for comprehensive brand experience assessment."""

from typing import List
from ..models.brand_profile import BrandProfile
from ..models.brand_assessment import BrandExperienceAssessment
from ..models.brand_coherence import BrandCoherenceScore
from .ethos_scorer import EthosScorer


class BrandExperienceEngine:
    """Main engine that scores brand experience across all dimensions."""

    @staticmethod
    def assess(
        brand: BrandProfile,
        interactions: List = None,
    ) -> BrandExperienceAssessment:
        """
        Assess brand experience across ethos, channels, proof, and interaction performance.

        Args:
            brand: BrandProfile with identity, channels, standards, and trust assets
            interactions: List of InteractionEvent objects (optional). If provided, will score
                         interaction performance. If None, defaults will be used.

        Returns:
            BrandExperienceAssessment with complete scoring across all dimensions.

        Scoring logic:
            1. Score ethos from brand attributes (mission, value props, etc.)
            2. Calculate channel consistency (active channels vs ideal distribution)
            3. Calculate proof-to-promise ratio (proof_assets vs claims)
            4. Calculate trust layer quality (proof + compliance + certs)
            5. Calculate interaction performance vs targets (if interactions provided)
            6. Produce composite brand_experience_score
        """
        if interactions is None:
            interactions = []

        # 1. Score ethos from brand profile attributes
        coherence = BrandExperienceEngine._score_ethos_from_profile(brand)

        # 2. Calculate channel consistency
        channel_consistency_score = BrandExperienceEngine._calculate_channel_consistency(brand)

        # 3. Calculate proof-to-promise ratio
        proof_to_promise_ratio = BrandExperienceEngine._calculate_proof_to_promise_ratio(brand)

        # 4. Calculate trust layer quality
        trust_layer_quality = BrandExperienceEngine._calculate_trust_layer_quality(brand)

        # 5. Calculate interaction performance
        if interactions:
            avg_response_performance = BrandExperienceEngine._calculate_response_performance(
                brand, interactions
            )
            avg_resolution_performance = BrandExperienceEngine._calculate_resolution_performance(
                brand, interactions
            )
            conversion_performance = BrandExperienceEngine._calculate_conversion_performance(
                brand, interactions
            )
        else:
            # Default to moderate performance if no interactions
            avg_response_performance = 0.5
            avg_resolution_performance = 0.5
            conversion_performance = 0.5

        # 6. Composite brand experience score
        brand_experience_score = BrandExperienceEngine._calculate_composite_score(
            coherence=coherence,
            channel_consistency=channel_consistency_score,
            proof_ratio=proof_to_promise_ratio,
            trust_quality=trust_layer_quality,
            response_perf=avg_response_performance,
            resolution_perf=avg_resolution_performance,
            conversion_perf=conversion_performance,
        )

        return BrandExperienceAssessment(
            brand_id=brand.brand_id,
            coherence=coherence,
            channel_consistency_score=channel_consistency_score,
            proof_to_promise_ratio=proof_to_promise_ratio,
            trust_layer_quality=trust_layer_quality,
            avg_response_performance=avg_response_performance,
            avg_resolution_performance=avg_resolution_performance,
            conversion_performance=conversion_performance,
            brand_experience_score=brand_experience_score,
        )

    @staticmethod
    def _score_ethos_from_profile(brand: BrandProfile) -> BrandCoherenceScore:
        """
        Score ethos dimensions based on brand profile attributes.

        Heuristics:
            - truthfulness_explainability: Based on clarity of mission and tagline
            - human_centered_technology: Based on value propositions mentioning human value
            - long_term_value_creation: Based on presence of mission and differentiators
            - cost_roi_discipline: Based on target metrics and goals
            - human_agency_respect: Based on tagline and value propositions
            - trust_contribution: Based on proof assets and certifications
            - manipulation_avoidance: Default baseline (brand provides no negative signals)
        """
        dimensions = {}

        # Truthfulness & Explainability: clarity of mission and tagline
        truth_base = 50.0
        if brand.mission:
            truth_base += 15.0
        if brand.tagline:
            truth_base += 15.0
        if brand.compliance_claims:
            truth_base += 10.0
        dimensions["truthfulness_explainability"] = min(100.0, truth_base)

        # Human-centered technology: value propositions and mission alignment
        human_base = 50.0
        for prop in brand.value_propositions:
            if any(word in prop.lower() for word in ["human", "people", "customer", "user", "simplify"]):
                human_base += 5.0
        dimensions["human_centered_technology"] = min(100.0, human_base)

        # Long-term value creation: mission, differentiators, and strategic focus
        long_term_base = 50.0
        if brand.mission:
            long_term_base += 15.0
        if len(brand.differentiators) > 0:
            long_term_base += 10.0
        if brand.target_resolution_time_seconds < 7200.0:  # Less than 2 hours
            long_term_base += 10.0
        dimensions["long_term_value_creation"] = min(100.0, long_term_base)

        # Cost-ROI discipline: defined targets and metrics
        cost_roi_base = 50.0
        if brand.target_response_time_seconds > 0:
            cost_roi_base += 15.0
        if brand.target_resolution_time_seconds > 0:
            cost_roi_base += 15.0
        if brand.target_conversion_rate > 0:
            cost_roi_base += 10.0
        dimensions["cost_roi_discipline"] = min(100.0, cost_roi_base)

        # Human agency respect: value propositions and channels
        agency_base = 50.0
        if len(brand.active_channels) > 2:  # Multiple channel options = choice
            agency_base += 15.0
        for prop in brand.value_propositions:
            if any(word in prop.lower() for word in ["choice", "control", "freedom", "flexible"]):
                agency_base += 10.0
        dimensions["human_agency_respect"] = min(100.0, agency_base)

        # Trust contribution: proof assets, compliance, certifications
        trust_base = 50.0
        if brand.proof_assets:
            trust_base += min(len(brand.proof_assets), 5) * 5.0  # Up to 25 points
        if brand.compliance_claims:
            trust_base += 15.0
        if brand.certifications:
            trust_base += 10.0
        dimensions["trust_contribution"] = min(100.0, trust_base)

        # Manipulation avoidance: default baseline (no negative signals detected)
        manipulation_base = 70.0  # Assume good faith unless contradicted
        dimensions["manipulation_avoidance"] = min(100.0, manipulation_base)

        return EthosScorer.score(dimensions)

    @staticmethod
    def _calculate_channel_consistency(brand: BrandProfile) -> float:
        """
        Calculate channel consistency score (0-100).

        Logic: Score based on number of active channels and reasonable distribution.
        1-2 channels: 60, 3-4 channels: 75, 5+ channels: 90
        """
        num_channels = len(brand.active_channels)
        if num_channels == 0:
            return 30.0
        elif num_channels == 1:
            return 60.0
        elif num_channels == 2:
            return 65.0
        elif num_channels <= 4:
            return 80.0
        else:
            return 90.0

    @staticmethod
    def _calculate_proof_to_promise_ratio(brand: BrandProfile) -> float:
        """
        Calculate proof-to-promise ratio (0-1).

        Logic: Ratio of proof assets to total claims (value props + differentiators).
        Examples:
            3 proof assets, 5 claims -> 3/5 = 0.6
            0 proof assets -> 0.0
            More proof than claims -> 1.0 (capped)
        """
        total_claims = len(brand.value_propositions) + len(brand.differentiators)
        if total_claims == 0:
            return 0.5  # No claims means no proof needed, neutral score

        proof_count = len(brand.proof_assets)
        ratio = proof_count / total_claims
        return min(1.0, ratio)

    @staticmethod
    def _calculate_trust_layer_quality(brand: BrandProfile) -> float:
        """
        Calculate trust layer quality score (0-100).

        Logic: Composite of proof assets, compliance claims, and certifications.
        Each component weighted equally towards 100.
        """
        proof_score = min(100.0, len(brand.proof_assets) * 15.0)  # Up to 100 with ~7 assets
        compliance_score = 30.0 if brand.compliance_claims else 0.0
        cert_score = min(100.0, len(brand.certifications) * 20.0)  # Up to 100 with ~5 certs

        # Weighted average (equal weight to each dimension)
        trust_quality = (proof_score + compliance_score + cert_score) / 3.0
        return min(100.0, trust_quality)

    @staticmethod
    def _calculate_response_performance(brand: BrandProfile, interactions: List) -> float:
        """
        Calculate average response performance (0-1) against brand target.

        Logic: For each interaction with response_time_seconds, check if it met the target.
        Returns average ratio of target met interactions.
        """
        if not interactions:
            return 0.5

        matching_interactions = [
            i for i in interactions
            if hasattr(i, "response_time_seconds") and i.response_time_seconds is not None
        ]

        if not matching_interactions:
            return 0.5

        met_count = 0
        for interaction in matching_interactions:
            if interaction.response_time_seconds <= brand.target_response_time_seconds:
                met_count += 1

        return met_count / len(matching_interactions)

    @staticmethod
    def _calculate_resolution_performance(brand: BrandProfile, interactions: List) -> float:
        """
        Calculate average resolution performance (0-1) against brand target.

        Logic: For each interaction with resolution_time_seconds, check if it met the target.
        Returns average ratio of target met interactions.
        """
        if not interactions:
            return 0.5

        matching_interactions = [
            i for i in interactions
            if hasattr(i, "resolution_time_seconds") and i.resolution_time_seconds is not None
        ]

        if not matching_interactions:
            return 0.5

        met_count = 0
        for interaction in matching_interactions:
            if interaction.resolution_time_seconds <= brand.target_resolution_time_seconds:
                met_count += 1

        return met_count / len(matching_interactions)

    @staticmethod
    def _calculate_conversion_performance(brand: BrandProfile, interactions: List) -> float:
        """
        Calculate conversion performance (0-1) against brand target conversion rate.

        Logic: Count converted interactions as ratio of total interactions.
        Compare against target_conversion_rate (0-1).
        Returns ratio of actual to target.
        """
        if not interactions:
            return 0.5

        converted_count = sum(1 for i in interactions if hasattr(i, "converted") and i.converted)
        actual_rate = converted_count / len(interactions)

        if brand.target_conversion_rate <= 0:
            return 0.5  # No target defined

        # Return ratio of actual to target, capped at 1.0
        return min(1.0, actual_rate / brand.target_conversion_rate)

    @staticmethod
    def _calculate_composite_score(
        coherence: BrandCoherenceScore,
        channel_consistency: float,
        proof_ratio: float,
        trust_quality: float,
        response_perf: float,
        resolution_perf: float,
        conversion_perf: float,
    ) -> float:
        """
        Calculate composite brand experience score (0-100).

        Weighting:
            30% - coherence (ethos alignment)
            15% - channel consistency
            15% - proof to promise ratio (scaled 0-100)
            15% - trust layer quality
            10% - response performance (scaled 0-100)
            10% - resolution performance (scaled 0-100)
            5%  - conversion performance (scaled 0-100)
        """
        composite = (
            coherence.composite_score * 0.30
            + channel_consistency * 0.15
            + (proof_ratio * 100.0) * 0.15
            + trust_quality * 0.15
            + (response_perf * 100.0) * 0.10
            + (resolution_perf * 100.0) * 0.10
            + (conversion_perf * 100.0) * 0.05
        )

        return min(100.0, max(0.0, composite))
