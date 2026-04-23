"""BrandExperienceAssessment model for comprehensive brand experience scoring."""

from dataclasses import dataclass
from .brand_coherence import BrandCoherenceScore


@dataclass
class BrandExperienceAssessment:
    """Comprehensive assessment of brand experience across all dimensions."""

    brand_id: str
    coherence: BrandCoherenceScore

    # Channel metrics
    channel_consistency_score: float = 0.0  # 0-100 — how consistent is experience across channels
    proof_to_promise_ratio: float = 0.0  # 0-1 — how much proof backs the claims
    trust_layer_quality: float = 0.0  # 0-100 — composite of proof + compliance + certs

    # Interaction quality baselines
    avg_response_performance: float = 0.0  # 0-1 where 1 = meeting target
    avg_resolution_performance: float = 0.0  # 0-1
    conversion_performance: float = 0.0  # 0-1 where 1 = meeting target rate

    # Overall
    brand_experience_score: float = 0.0  # 0-100 composite

    def is_compliant(self, minimum_ethos_score: float = 50.0) -> bool:
        """Check if brand meets minimum ethos compliance threshold."""
        return self.coherence.composite_score >= minimum_ethos_score
