"""
Comprehensive tests for Weighted Scoring Engine

Tests cover:
- Weighted value scoring with configurable weights
- Weighted trust scoring with tier multipliers
- Per-dimension contributions
- Weight application correctness
- Edge cases: all-zero, all-max scores
"""

import unittest
import sys
import os

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _PROJECT_ROOT)

from l3_qualification.engines.weighted_scoring import (
    WeightedScoringEngine,
    WeightedValueResult,
    WeightedTrustResult,
    ValueWeights,
    PenaltyWeights,
    EngineConfig,
)
from l3_qualification.models.decision_object import ValueScores, TrustScores, TrustTier


class TestWeightedValueScoring(unittest.TestCase):
    """Test weighted value scoring engine."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = WeightedScoringEngine()

    def test_weighted_value_basic(self):
        """Test basic weighted value calculation."""
        value_scores = ValueScores(
            revenue_impact=5,
            cost_efficiency=4,
            time_leverage=3,
            strategic_alignment=5,
            customer_human_benefit=4,
            knowledge_asset_creation=2,
            compounding_potential=4,
            reversibility=3,
            downside_risk=1,
            execution_drag=1,
            uncertainty=1,
            ethical_misalignment=0,
        )

        result = self.engine.compute_weighted_value(value_scores)

        # Verify it's a WeightedValueResult
        self.assertIsInstance(result, WeightedValueResult)

        # Verify weighted_gross is calculated
        self.assertGreater(result.weighted_gross, 0)

        # Verify weighted_penalty is calculated
        self.assertGreaterEqual(result.weighted_penalty, 0)

        # Verify weighted_net = gross - penalty
        self.assertAlmostEqual(
            result.weighted_net,
            result.weighted_gross - result.weighted_penalty,
            places=1,
        )

    def test_weighted_value_all_zeros(self):
        """Test weighted value with all-zero scores."""
        value_scores = ValueScores()

        result = self.engine.compute_weighted_value(value_scores)

        self.assertEqual(result.weighted_gross, 0.0)
        self.assertEqual(result.weighted_penalty, 0.0)
        self.assertEqual(result.weighted_net, 0.0)

    def test_weighted_value_all_max(self):
        """Test weighted value with all-max scores."""
        value_scores = ValueScores(
            revenue_impact=5,
            cost_efficiency=5,
            time_leverage=5,
            strategic_alignment=5,
            customer_human_benefit=5,
            knowledge_asset_creation=5,
            compounding_potential=5,
            reversibility=5,
            downside_risk=5,
            execution_drag=5,
            uncertainty=5,
            ethical_misalignment=5,
        )

        result = self.engine.compute_weighted_value(value_scores)

        # weighted_gross should be sum of (5 × weight) for 8 dimensions
        # weighted_penalty should be sum of (5 × penalty_weight) for 4 dimensions
        self.assertGreater(result.weighted_gross, 0)
        self.assertGreater(result.weighted_penalty, 0)

    def test_weighted_value_dimension_contributions(self):
        """Test that per-dimension contributions are calculated."""
        value_scores = ValueScores(
            revenue_impact=5,
            cost_efficiency=3,
            time_leverage=2,
            strategic_alignment=4,
            customer_human_benefit=1,
            knowledge_asset_creation=2,
            compounding_potential=3,
            reversibility=1,
            downside_risk=2,
            execution_drag=1,
            uncertainty=1,
            ethical_misalignment=0,
        )

        result = self.engine.compute_weighted_value(value_scores)

        # Check positive contributions
        self.assertIn("revenue_impact", result.positive_contributions)
        self.assertIn("strategic_alignment", result.positive_contributions)
        self.assertIn("compounding_potential", result.positive_contributions)

        # Check penalty contributions
        self.assertIn("downside_risk", result.penalty_contributions)
        self.assertIn("execution_drag", result.penalty_contributions)
        self.assertIn("ethical_misalignment", result.penalty_contributions)

    def test_weighted_value_high_strategic_alignment_weight(self):
        """Test that strategic alignment has 2.0 weight (highest)."""
        # Create two scenarios differing only in strategic_alignment
        value_scores_low = ValueScores(
            revenue_impact=3,
            cost_efficiency=3,
            time_leverage=3,
            strategic_alignment=0,  # No alignment
            customer_human_benefit=3,
            knowledge_asset_creation=3,
            compounding_potential=3,
            reversibility=3,
        )

        value_scores_high = ValueScores(
            revenue_impact=3,
            cost_efficiency=3,
            time_leverage=3,
            strategic_alignment=5,  # Full alignment
            customer_human_benefit=3,
            knowledge_asset_creation=3,
            compounding_potential=3,
            reversibility=3,
        )

        result_low = self.engine.compute_weighted_value(value_scores_low)
        result_high = self.engine.compute_weighted_value(value_scores_high)

        # Difference should be 5 * 2.0 = 10.0
        difference = result_high.weighted_gross - result_low.weighted_gross
        self.assertAlmostEqual(difference, 10.0, places=1)

    def test_weighted_value_high_ethical_penalty_weight(self):
        """Test that ethical_misalignment has 2.0 penalty weight (highest)."""
        value_scores_ok = ValueScores(
            downside_risk=1,
            execution_drag=1,
            uncertainty=1,
            ethical_misalignment=0,  # No ethical issue
        )

        value_scores_bad = ValueScores(
            downside_risk=1,
            execution_drag=1,
            uncertainty=1,
            ethical_misalignment=5,  # Severe ethical issue
        )

        result_ok = self.engine.compute_weighted_value(value_scores_ok)
        result_bad = self.engine.compute_weighted_value(value_scores_bad)

        # Difference should be 5 * 2.0 = 10.0
        difference = result_bad.weighted_penalty - result_ok.weighted_penalty
        self.assertAlmostEqual(difference, 10.0, places=1)

    def test_weighted_value_raw_compatibility(self):
        """Test that raw_net and raw_gross are provided for backward compat."""
        value_scores = ValueScores(
            revenue_impact=4,
            cost_efficiency=3,
            time_leverage=2,
            strategic_alignment=5,
            customer_human_benefit=2,
            knowledge_asset_creation=1,
            compounding_potential=3,
            reversibility=2,
            downside_risk=1,
            execution_drag=1,
            uncertainty=0,
            ethical_misalignment=0,
        )

        result = self.engine.compute_weighted_value(value_scores)

        # raw_gross should equal value_scores.gross_value()
        self.assertEqual(result.raw_gross, value_scores.gross_value())

        # raw_penalty should equal value_scores.penalty()
        self.assertEqual(result.raw_penalty, value_scores.penalty())

        # raw_net should equal value_scores.net_value()
        self.assertEqual(result.raw_net, value_scores.net_value())


class TestWeightedTrustScoring(unittest.TestCase):
    """Test weighted trust scoring engine."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = WeightedScoringEngine()

    def test_weighted_trust_basic(self):
        """Test basic weighted trust calculation."""
        trust_scores = TrustScores(
            evidence_quality=5,
            logic_integrity=4,
            outcome_history=3,
            context_fit=4,
            stakeholder_clarity=5,
            risk_containment=2,
            auditability=3,
        )

        result = self.engine.compute_weighted_trust(
            trust_scores, trust_tier_str="T2_QUALIFIED"
        )

        # trust_total should be sum of 7 scores
        self.assertEqual(result.trust_total, 26)

        # trust_average should be 26/7 ≈ 3.714
        self.assertAlmostEqual(result.trust_average, 26 / 7, places=2)

        # tier_multiplier for T2_QUALIFIED should be 0.8
        self.assertEqual(result.tier_multiplier, 0.8)

        # adjusted_trust_score = average * tier_multiplier
        expected_adjusted = round((26 / 7) * 0.8, 3)
        self.assertEqual(result.adjusted_trust_score, expected_adjusted)

    def test_weighted_trust_all_max(self):
        """Test weighted trust with all perfect scores."""
        trust_scores = TrustScores(5, 5, 5, 5, 5, 5, 5)

        result = self.engine.compute_weighted_trust(
            trust_scores, trust_tier_str="T4_DELEGATED"
        )

        # trust_total should be 35
        self.assertEqual(result.trust_total, 35)

        # trust_average should be 5.0
        self.assertEqual(result.trust_average, 5.0)

        # tier_multiplier for T4_DELEGATED should be 1.2
        self.assertEqual(result.tier_multiplier, 1.2)

        # adjusted_trust_score = 5.0 * 1.2 = 6.0
        self.assertEqual(result.adjusted_trust_score, 6.0)

    def test_weighted_trust_all_zero(self):
        """Test weighted trust with all zero scores."""
        trust_scores = TrustScores()

        result = self.engine.compute_weighted_trust(
            trust_scores, trust_tier_str="T0_UNQUALIFIED"
        )

        # trust_total should be 0
        self.assertEqual(result.trust_total, 0)

        # trust_average should be 0.0
        self.assertEqual(result.trust_average, 0.0)

        # tier_multiplier for T0_UNQUALIFIED should be 0.2
        self.assertEqual(result.tier_multiplier, 0.2)

        # adjusted_trust_score = 0.0 * 0.2 = 0.0
        self.assertEqual(result.adjusted_trust_score, 0.0)

    def test_weighted_trust_tier_enum(self):
        """Test weighted trust with TrustTier enum."""
        trust_scores = TrustScores(3, 3, 3, 3, 3, 3, 3)

        result = self.engine.compute_weighted_trust(
            trust_scores, trust_tier=TrustTier.T3_CERTIFIED
        )

        # tier_multiplier for T3_CERTIFIED should be 1.0
        self.assertEqual(result.tier_multiplier, 1.0)

    def test_weighted_trust_all_tiers(self):
        """Test trust tier multipliers for all tiers."""
        trust_scores = TrustScores(2, 2, 2, 2, 2, 2, 2)  # total = 14, avg ≈ 2.0

        tiers_and_multipliers = {
            "T0_UNQUALIFIED": 0.2,
            "T1_OBSERVED": 0.5,
            "T2_QUALIFIED": 0.8,
            "T3_CERTIFIED": 1.0,
            "T4_DELEGATED": 1.2,
        }

        for tier_str, expected_mult in tiers_and_multipliers.items():
            result = self.engine.compute_weighted_trust(
                trust_scores, trust_tier_str=tier_str
            )
            self.assertEqual(result.tier_multiplier, expected_mult)

    def test_weighted_trust_default_tier(self):
        """Test default tier when none specified."""
        trust_scores = TrustScores(1, 1, 1, 1, 1, 1, 1)

        result = self.engine.compute_weighted_trust(trust_scores)

        # Default should be T0_UNQUALIFIED with multiplier 0.2
        self.assertEqual(result.trust_tier, "T0_UNQUALIFIED")
        self.assertEqual(result.tier_multiplier, 0.2)


class TestWeightedScoringConfiguration(unittest.TestCase):
    """Test weight configuration and updates."""

    def test_custom_weight_configuration(self):
        """Test engine with custom weight configuration."""
        custom_config = EngineConfig(
            value_weights=ValueWeights(
                revenue_impact=2.0,  # Increased
                strategic_alignment=1.0,  # Decreased
            ),
            penalty_weights=PenaltyWeights(
                ethical_misalignment=1.0,  # Decreased
            ),
        )

        engine = WeightedScoringEngine(config=custom_config)

        value_scores = ValueScores(
            revenue_impact=5,
            strategic_alignment=5,
            ethical_misalignment=5,
        )

        result = engine.compute_weighted_value(value_scores)

        # revenue_impact contribution = 5 * 2.0 = 10.0
        self.assertEqual(result.positive_contributions["revenue_impact"], 10.0)

        # strategic_alignment contribution = 5 * 1.0 = 5.0
        self.assertEqual(result.positive_contributions["strategic_alignment"], 5.0)

        # ethical_misalignment penalty = 5 * 1.0 = 5.0
        self.assertEqual(result.penalty_contributions["ethical_misalignment"], 5.0)

    def test_weight_update(self):
        """Test updating weights on existing engine."""
        engine = WeightedScoringEngine()

        new_value_weights = ValueWeights(revenue_impact=3.0)
        new_penalty_weights = PenaltyWeights(ethical_misalignment=3.0)

        engine.update_weights(
            value_weights=new_value_weights,
            penalty_weights=new_penalty_weights,
        )

        # Create new engine with updated config to verify
        value_scores = ValueScores(revenue_impact=2, ethical_misalignment=1)
        result = engine.compute_weighted_value(value_scores)

        # revenue_impact = 2 * 3.0 = 6.0
        self.assertEqual(result.positive_contributions["revenue_impact"], 6.0)

        # ethical_misalignment = 1 * 3.0 = 3.0
        self.assertEqual(result.penalty_contributions["ethical_misalignment"], 3.0)

    def test_weight_comparison(self):
        """Test weight comparison shows raw vs weighted."""
        engine = WeightedScoringEngine()

        value_scores = ValueScores(
            revenue_impact=4,
            strategic_alignment=5,
            ethical_misalignment=2,
        )

        comparison = engine.weight_comparison(value_scores)

        # Check structure
        self.assertIn("revenue_impact", comparison)
        self.assertIn("strategic_alignment", comparison)

        # Check that comparison has raw, weight, and weighted
        for dim, stats in comparison.items():
            self.assertIn("raw", stats)
            self.assertIn("weight", stats)
            self.assertIn("weighted", stats)

        # Verify calculations
        ri_stats = comparison["revenue_impact"]
        self.assertEqual(ri_stats["raw"], 4)
        self.assertEqual(ri_stats["weight"], 1.5)
        self.assertEqual(ri_stats["weighted"], 6.0)


if __name__ == "__main__":
    unittest.main()
