"""ProspectValueEngine for scoring and decision-making."""

from datetime import datetime, timedelta
from typing import List, Dict, Any

from l1_sensing.models.prospect import ProspectProfile
from l1_sensing.models.inference import InferenceRecord
from l1_sensing.models.value_assessment import ProspectValueAssessment


class ProspectValueEngine:
    """Engine for scoring prospects and generating decisions.

    Implements weighted component scoring with penalties for low confidence
    and stale signals. Bridges L1 sensing to L3 qualification decisions.
    """

    # Penalty configurations
    LOW_CONFIDENCE_THRESHOLD = 50
    LOW_CONFIDENCE_PENALTY = 0.20  # 20% penalty
    STALE_SIGNAL_DAYS = 30
    STALE_SIGNAL_PENALTY = 0.10  # 10% penalty

    @staticmethod
    def score_prospect(
        prospect: ProspectProfile,
        inferences: List[InferenceRecord],
    ) -> ProspectValueAssessment:
        """Score a prospect based on profile and inferences.

        Args:
            prospect: ProspectProfile with business context
            inferences: List of InferenceRecords from signal analysis

        Returns:
            ProspectValueAssessment with component scores and total
        """
        # Extract component scores from inferences
        components = ProspectValueEngine._extract_components(inferences)

        # Calculate overall confidence
        overall_confidence = ProspectValueEngine._calculate_confidence(inferences)

        # Calculate component scores with validation
        need = ProspectValueEngine._clamp(components.get("need", 0))
        service_fit = ProspectValueEngine._clamp(components.get("service_fit", 0))
        readiness = ProspectValueEngine._clamp(components.get("readiness", 0))
        accessibility = ProspectValueEngine._clamp(components.get("accessibility", 0))
        expected_uplift = ProspectValueEngine._clamp(components.get("expected_uplift", 0))
        economic_scale = ProspectValueEngine._clamp(components.get("economic_scale", 0))
        confidence = ProspectValueEngine._clamp(overall_confidence)

        # Calculate weighted total
        weights = ProspectValueAssessment.COMPONENT_WEIGHTS
        total = (
            need * weights["need"]
            + service_fit * weights["service_fit"]
            + readiness * weights["readiness"]
            + accessibility * weights["accessibility"]
            + expected_uplift * weights["expected_uplift"]
            + economic_scale * weights["economic_scale"]
            + confidence * weights["confidence"]
        )

        # Apply penalties
        total = ProspectValueEngine._apply_penalties(total, confidence, prospect)
        total = ProspectValueEngine._clamp(total)

        # Derive best fit services and priority gaps
        best_fit_services = ProspectValueEngine._derive_best_fit_services(
            prospect, inferences
        )
        priority_gaps = ProspectValueEngine._derive_priority_gaps(
            prospect, inferences
        )

        return ProspectValueAssessment(
            need=need,
            service_fit=service_fit,
            readiness=readiness,
            accessibility=accessibility,
            expected_uplift=expected_uplift,
            economic_scale=economic_scale,
            confidence=confidence,
            total=total,
            best_fit_services=best_fit_services,
            priority_gaps=priority_gaps,
        )

    @staticmethod
    def _extract_components(inferences: List[InferenceRecord]) -> Dict[str, float]:
        """Extract component scores from inference records."""
        components = {
            "need": 0,
            "service_fit": 0,
            "readiness": 0,
            "accessibility": 0,
            "expected_uplift": 0,
            "economic_scale": 0,
        }

        # Sum confidence-weighted inference data for each component
        # In practice, inferences would contain structured score data
        # For now, use equal weighting of available inferences per component
        if inferences:
            avg_confidence = sum(inf.confidence for inf in inferences) / len(inferences)
            for component in components:
                components[component] = avg_confidence * 100

        return components

    @staticmethod
    def _calculate_confidence(inferences: List[InferenceRecord]) -> float:
        """Calculate overall confidence from inference records."""
        if not inferences:
            return 0

        avg_confidence = sum(inf.confidence for inf in inferences) / len(inferences)
        return avg_confidence * 100

    @staticmethod
    def _apply_penalties(
        total: float, confidence: float, prospect: ProspectProfile
    ) -> float:
        """Apply penalties for low confidence and stale signals."""
        penalized_total = total

        # Apply low confidence penalty
        if confidence < ProspectValueEngine.LOW_CONFIDENCE_THRESHOLD:
            penalized_total *= (1 - ProspectValueEngine.LOW_CONFIDENCE_PENALTY)

        # Apply stale signal penalty
        if prospect.last_verified_at:
            try:
                last_verified = datetime.fromisoformat(prospect.last_verified_at)
                age = datetime.now() - last_verified
                if age > timedelta(days=ProspectValueEngine.STALE_SIGNAL_DAYS):
                    penalized_total *= (1 - ProspectValueEngine.STALE_SIGNAL_PENALTY)
            except (ValueError, TypeError):
                # If date parsing fails, skip penalty
                pass

        return penalized_total

    @staticmethod
    def _clamp(value: float, min_val: float = 0, max_val: float = 100) -> float:
        """Clamp value to bounds."""
        return max(min_val, min(max_val, value))

    @staticmethod
    def _derive_best_fit_services(
        prospect: ProspectProfile, inferences: List[InferenceRecord]
    ) -> List[str]:
        """Derive best fit services from prospect profile and inferences."""
        services = []

        # Extract service fit inferences
        for inference in inferences:
            if "service" in inference.inference_type.value.lower():
                if inference.confidence > 0.6:  # High confidence
                    services.append(inference.statement)

        return services[:3]  # Return top 3

    @staticmethod
    def _derive_priority_gaps(
        prospect: ProspectProfile, inferences: List[InferenceRecord]
    ) -> List[str]:
        """Derive priority gaps from prospect profile and inferences."""
        gaps = []

        # Extract capability gaps from inferences
        capabilities = prospect.capability_summary
        if capabilities.marketing_maturity.value == "low":
            gaps.append("Marketing automation and measurement")
        if capabilities.sales_complexity.value == "high":
            gaps.append("Sales process complexity")
        if capabilities.measurement_maturity.value == "low":
            gaps.append("Performance measurement and attribution")
        if capabilities.interaction_management_maturity.value == "low":
            gaps.append("Interaction management infrastructure")

        return gaps

    @staticmethod
    def prospect_to_decision(
        prospect_id: str,
        assessment: ProspectValueAssessment,
        prospect: ProspectProfile,
    ) -> Dict[str, Any]:
        """Bridge prospect assessment to decision structure.

        Converts ProspectValueAssessment into decision fields for L3 qualification.

        Args:
            prospect_id: The prospect identifier
            assessment: The ProspectValueAssessment
            prospect: The original ProspectProfile

        Returns:
            Dict with decision structure for L3 integration
        """
        # Derive blast radius from economic scale (0-1)
        blast_radius = assessment.economic_scale / 100

        # Derive strategic impact (0-1 scale: need and service_fit are 0-100 each)
        strategic_impact = (assessment.need / 100) * (assessment.service_fit / 100)

        # Derive financial exposure as dollar estimate
        # economic_scale 0-100 maps to $0-$50,000 for prospect acquisition decisions
        # (below $50k threshold to avoid automatic financial escalation for prospects)
        financial_exposure = (assessment.economic_scale / 100) * 25_000

        # Calculate data completeness
        fields_provided = sum(
            [
                bool(prospect.official_name),
                bool(prospect.domain),
                bool(prospect.industries),
                bool(prospect.buyer_personas),
                bool(prospect.service_geographies),
                bool(prospect.last_verified_at),
            ]
        )
        data_completeness = fields_provided / 6  # 6 key fields

        # Derive recency (0-1, where 1 is very recent)
        recency = 0.5  # Default
        if prospect.last_verified_at:
            try:
                last_verified = datetime.fromisoformat(prospect.last_verified_at)
                age_days = (datetime.now() - last_verified).days
                if age_days <= 7:
                    recency = 1.0
                elif age_days <= 30:
                    recency = 0.8
                elif age_days <= 90:
                    recency = 0.6
                else:
                    recency = 0.4
            except (ValueError, TypeError):
                pass

        return {
            "decision_id": f"prospect_{prospect_id}",
            "description": f"Acquire {prospect.official_name} ({prospect.domain}) - {assessment.total:.0f} fit score",
            "reversibility": 0.8,
            "blast_radius": blast_radius,
            "financial_exposure": financial_exposure,
            "strategic_impact": strategic_impact,
            "time_sensitivity": 0.5,
            "source_reliability": assessment.confidence / 100,
            "data_completeness": data_completeness,
            "corroboration": min(1.0, len(prospect.evidence_ids) / 5),  # Max 5
            "recency": recency,
            "ethical_alignment": 1.0,
            "consistency": 0.8,
        }
