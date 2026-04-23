"""
Weighted Value & Trust Scoring

Applies configurable asymmetric weights to value and trust scoring dimensions.
Unlike raw scoring, weighted scoring produces differentially important dimension
contributions based on organizational priorities.

Weighted scoring formula per dimension:
- contribution = raw_score × weight
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from ..models.decision_object import TrustTier


# ─────────────────────────────────────────────
# WEIGHT CONFIGURATIONS
# ─────────────────────────────────────────────

@dataclass
class ValueWeights:
    """Asymmetric weights for positive value dimensions."""
    revenue_impact: float = 1.5
    cost_efficiency: float = 1.2
    time_leverage: float = 1.3
    strategic_alignment: float = 2.0  # Double weight (most important)
    customer_benefit: float = 1.4
    knowledge_creation: float = 1.1
    compounding_potential: float = 1.8
    reversibility: float = 1.0


@dataclass
class PenaltyWeights:
    """Asymmetric weights for penalty dimensions."""
    downside_risk: float = 1.5
    execution_drag: float = 1.3
    uncertainty: float = 1.2
    ethical_misalignment: float = 2.0  # High penalty for ethical issues


@dataclass
class EngineConfig:
    """Engine configuration with weights and trust multipliers."""
    value_weights: ValueWeights = field(default_factory=ValueWeights)
    penalty_weights: PenaltyWeights = field(default_factory=PenaltyWeights)

    # Trust tier multipliers (from models)
    trust_multiplier: Dict[str, float] = field(
        default_factory=lambda: {
            "T0_UNQUALIFIED": 0.2,
            "T1_OBSERVED": 0.5,
            "T2_QUALIFIED": 0.8,
            "T3_CERTIFIED": 1.0,
            "T4_DELEGATED": 1.2,
        }
    )


# ─────────────────────────────────────────────
# SCORING RESULTS
# ─────────────────────────────────────────────

@dataclass
class WeightedValueResult:
    """Result of weighted value scoring."""
    weighted_gross: float
    weighted_penalty: float
    weighted_net: float
    raw_net: float
    raw_gross: float
    raw_penalty: float
    positive_contributions: Dict[str, float] = field(default_factory=dict)
    penalty_contributions: Dict[str, float] = field(default_factory=dict)


@dataclass
class WeightedTrustResult:
    """Result of weighted trust scoring."""
    trust_total: int
    trust_average: float
    trust_tier: str
    tier_multiplier: float
    adjusted_trust_score: float


# ─────────────────────────────────────────────
# SCORING ENGINE
# ─────────────────────────────────────────────

class WeightedScoringEngine:
    """
    Weighted value and trust scoring using configurable asymmetric weights.
    """

    def __init__(self, config: Optional[EngineConfig] = None):
        """Initialize with optional custom config."""
        self.config = config or EngineConfig()

    def compute_weighted_value(self, value_scores) -> WeightedValueResult:
        """
        Compute weighted value scores using engine config weights.

        Returns:
        - weighted_gross: sum of (dimension × weight)
        - weighted_penalty: sum of (penalty × weight)
        - weighted_net: gross - penalty
        - raw_net: unweighted net (for backward compatibility)
        - dimension_contributions: per-dimension weighted scores
        """
        vw = self.config.value_weights
        pw = self.config.penalty_weights

        # Positive dimensions × weights
        positive_contributions = {
            "revenue_impact": value_scores.revenue_impact * vw.revenue_impact,
            "cost_efficiency": value_scores.cost_efficiency * vw.cost_efficiency,
            "time_leverage": value_scores.time_leverage * vw.time_leverage,
            "strategic_alignment": value_scores.strategic_alignment
            * vw.strategic_alignment,
            "customer_benefit": value_scores.customer_human_benefit
            * vw.customer_benefit,
            "knowledge_creation": value_scores.knowledge_asset_creation
            * vw.knowledge_creation,
            "compounding_potential": value_scores.compounding_potential
            * vw.compounding_potential,
            "reversibility": value_scores.reversibility * vw.reversibility,
        }

        # Penalty dimensions × weights
        penalty_contributions = {
            "downside_risk": value_scores.downside_risk * pw.downside_risk,
            "execution_drag": value_scores.execution_drag * pw.execution_drag,
            "uncertainty": value_scores.uncertainty * pw.uncertainty,
            "ethical_misalignment": value_scores.ethical_misalignment
            * pw.ethical_misalignment,
        }

        weighted_gross = sum(positive_contributions.values())
        weighted_penalty = sum(penalty_contributions.values())
        weighted_net = weighted_gross - weighted_penalty

        return WeightedValueResult(
            weighted_gross=round(weighted_gross, 2),
            weighted_penalty=round(weighted_penalty, 2),
            weighted_net=round(weighted_net, 2),
            raw_net=value_scores.net_value(),
            raw_gross=value_scores.gross_value(),
            raw_penalty=value_scores.penalty(),
            positive_contributions={k: round(v, 2) for k, v in positive_contributions.items()},
            penalty_contributions={k: round(v, 2) for k, v in penalty_contributions.items()},
        )

    def compute_weighted_trust(
        self, trust_scores, trust_tier: Optional[TrustTier] = None, trust_tier_str: Optional[str] = None
    ) -> WeightedTrustResult:
        """
        Compute trust score adjusted by tier multiplier from config.

        Returns:
        - trust_total: raw sum of 7 inputs
        - trust_average: raw average
        - tier_multiplier: from config
        - adjusted_trust_score: average × tier_multiplier
        """
        total = trust_scores.total()
        average = trust_scores.average()

        # Handle both TrustTier enum and string versions
        if trust_tier:
            tier_str = trust_tier.value
        elif trust_tier_str:
            tier_str = trust_tier_str
        else:
            tier_str = "T0_UNQUALIFIED"

        tier_mult = self.config.trust_multiplier.get(tier_str, 0.2)

        return WeightedTrustResult(
            trust_total=total,
            trust_average=round(average, 3),
            trust_tier=tier_str,
            tier_multiplier=tier_mult,
            adjusted_trust_score=round(average * tier_mult, 3),
        )

    def update_weights(
        self,
        value_weights: Optional[ValueWeights] = None,
        penalty_weights: Optional[PenaltyWeights] = None,
        trust_multipliers: Optional[Dict[str, float]] = None,
    ) -> None:
        """Update engine weights."""
        if value_weights:
            self.config.value_weights = value_weights
        if penalty_weights:
            self.config.penalty_weights = penalty_weights
        if trust_multipliers:
            self.config.trust_multiplier = trust_multipliers

    def weight_comparison(self, value_scores) -> Dict[str, Dict[str, float]]:
        """
        Compare raw vs weighted scores to show impact of weights.

        Returns dict with raw and weighted values for each dimension.
        """
        vw = self.config.value_weights
        pw = self.config.penalty_weights

        raw_values = {
            "revenue_impact": value_scores.revenue_impact,
            "cost_efficiency": value_scores.cost_efficiency,
            "time_leverage": value_scores.time_leverage,
            "strategic_alignment": value_scores.strategic_alignment,
            "customer_benefit": value_scores.customer_human_benefit,
            "knowledge_creation": value_scores.knowledge_asset_creation,
            "compounding_potential": value_scores.compounding_potential,
            "reversibility": value_scores.reversibility,
            "downside_risk": value_scores.downside_risk,
            "execution_drag": value_scores.execution_drag,
            "uncertainty": value_scores.uncertainty,
            "ethical_misalignment": value_scores.ethical_misalignment,
        }

        weights = {
            "revenue_impact": vw.revenue_impact,
            "cost_efficiency": vw.cost_efficiency,
            "time_leverage": vw.time_leverage,
            "strategic_alignment": vw.strategic_alignment,
            "customer_benefit": vw.customer_benefit,
            "knowledge_creation": vw.knowledge_creation,
            "compounding_potential": vw.compounding_potential,
            "reversibility": vw.reversibility,
            "downside_risk": pw.downside_risk,
            "execution_drag": pw.execution_drag,
            "uncertainty": pw.uncertainty,
            "ethical_misalignment": pw.ethical_misalignment,
        }

        comparison = {}
        for dim, raw_val in raw_values.items():
            weight = weights[dim]
            weighted_val = raw_val * weight
            comparison[dim] = {
                "raw": round(raw_val, 2),
                "weight": weight,
                "weighted": round(weighted_val, 2),
            }

        return comparison
