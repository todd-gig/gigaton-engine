"""Unit tests for Compensation Engine."""

import unittest

from l4_execution.engines.compensation_engine import CompensationEngine
from l4_execution.engines.nocs_engine import NOCSEngine, NOCSResult
from l4_execution.models.action_benchmark import ActionBenchmark
from l4_execution.models.role_profile import RoleProfile


class TestCompensationEngine(unittest.TestCase):
    """Tests for CompensationEngine."""

    def setUp(self):
        """Set up common test fixtures."""
        self.engine = CompensationEngine(payout_conversion_rate=50.0)
        self.base_role = RoleProfile.create_default("test", "Test")

    def test_base_only_no_variable(self):
        """With zero NOCS, only base compensation should be paid."""
        benchmark = ActionBenchmark(
            action_id="test_1",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=0.0,
            effort_intensity=0.0,
            output_quality=0.0,
            uniqueness=0.0,
            relational_capital=0.0,
            risk_reduction=0.0,
            probability_lift=0.0,
            multiplicative_effect=0.0,
            brand_adherence=0.0,
            interaction_effectiveness=0.0,
            economic_productivity=0.0,
            ethos_alignment=0.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )

        self.assertEqual(comp_event.base_amount, 1000.0)
        self.assertAlmostEqual(comp_event.variable_amount, 0.0, places=1)
        self.assertAlmostEqual(comp_event.total_amount, 1000.0, places=1)

    def test_full_formula_calculation(self):
        """Full formula calculation with all components."""
        benchmark = ActionBenchmark(
            action_id="test_2",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.5,
            ethos_alignment_score=90.0,
            penalties=100.0,
        )

        # With perfect NOCS, ethos 90 (1.25 coeff), multiplier 1.5
        # variable = (100/100) * 50 * 1.5 * 1.25 = 93.75
        # total = 1000 + 93.75 - 100 = 993.75
        self.assertGreater(comp_event.variable_amount, 0.0)
        self.assertAlmostEqual(comp_event.total_amount, 993.75, places=1)

    def test_ethos_disqualification_below_50(self):
        """Ethos alignment < 50 should disqualify variable compensation."""
        benchmark = ActionBenchmark(
            action_id="test_3",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=40.0,  # Below 50
            penalties=0.0,
        )

        self.assertEqual(comp_event.variable_amount, 0.0)
        self.assertEqual(comp_event.ethos_coefficient, 0.0)
        self.assertEqual(comp_event.total_amount, 1000.0)

    def test_ethos_bonus_above_90(self):
        """Ethos alignment >= 90 should apply 1.25 coefficient."""
        benchmark = ActionBenchmark(
            action_id="test_4",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=95.0,  # >= 90
            penalties=0.0,
        )

        self.assertEqual(comp_event.ethos_coefficient, 1.25)
        self.assertGreater(comp_event.variable_amount, 0.0)

    def test_ethos_standard_at_70(self):
        """Ethos alignment >= 70 should apply 1.0 coefficient."""
        benchmark = ActionBenchmark(
            action_id="test_5",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,  # >= 70, < 90
            penalties=0.0,
        )

        self.assertEqual(comp_event.ethos_coefficient, 1.0)

    def test_penalties_reduce_total(self):
        """Penalties should reduce total compensation."""
        benchmark = ActionBenchmark(
            action_id="test_6",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)

        comp_no_penalty = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )
        comp_with_penalty = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=200.0,
        )

        self.assertGreater(comp_no_penalty.total_amount, comp_with_penalty.total_amount)

    def test_penalties_cannot_make_total_negative(self):
        """Total compensation should never go below 0."""
        benchmark = ActionBenchmark(
            action_id="test_7",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=100.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=500.0,  # Much larger than base
        )

        self.assertGreaterEqual(comp_event.total_amount, 0.0)

    def test_strategic_multiplier_amplifies(self):
        """Strategic multiplier should amplify variable compensation."""
        benchmark = ActionBenchmark(
            action_id="test_8",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)

        comp_low_mult = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )
        comp_high_mult = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=2.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )

        self.assertGreater(comp_high_mult.variable_amount, comp_low_mult.variable_amount)
        self.assertEqual(comp_high_mult.variable_amount, comp_low_mult.variable_amount * 2)

    def test_zero_nocs_yields_base_only(self):
        """Zero NOCS should yield base compensation only."""
        benchmark = ActionBenchmark(
            action_id="test_9",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=0.0,
            effort_intensity=0.0,
            output_quality=0.0,
            uniqueness=0.0,
            relational_capital=0.0,
            risk_reduction=0.0,
            probability_lift=0.0,
            multiplicative_effect=0.0,
            brand_adherence=0.0,
            interaction_effectiveness=0.0,
            economic_productivity=0.0,
            ethos_alignment=0.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1500.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.5,
            ethos_alignment_score=80.0,
            penalties=0.0,
        )

        self.assertAlmostEqual(comp_event.total_amount, 1500.0, places=1)

    def test_high_nocs_high_payout(self):
        """High NOCS with good ethos should yield substantial variable component."""
        benchmark = ActionBenchmark(
            action_id="test_10",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=90.0,
            effort_intensity=90.0,
            output_quality=90.0,
            uniqueness=90.0,
            relational_capital=90.0,
            risk_reduction=90.0,
            probability_lift=90.0,
            multiplicative_effect=90.0,
            brand_adherence=90.0,
            interaction_effectiveness=90.0,
            economic_productivity=90.0,
            ethos_alignment=90.0,
            confidence=0.95,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.5,
            ethos_alignment_score=92.0,
            penalties=0.0,
        )

        # Should have significant variable component
        self.assertGreater(comp_event.variable_amount, 50.0)
        self.assertGreater(comp_event.total_amount, 1050.0)

    def test_explanation_populated(self):
        """Compensation event should have explanation text."""
        benchmark = ActionBenchmark(
            action_id="test_11",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )

        self.assertGreater(len(comp_event.explanation), 0)
        self.assertIn("Base", comp_event.explanation)

    def test_comp_event_id_generated(self):
        """Compensation event ID should be auto-generated."""
        benchmark = ActionBenchmark(
            action_id="test_12",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )

        self.assertTrue(comp_event.comp_event_id.startswith("comp_"))
        self.assertGreater(len(comp_event.comp_event_id), 5)

    def test_period_id_preserved(self):
        """Period ID should be preserved in compensation event."""
        benchmark = ActionBenchmark(
            action_id="test_13",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
            period_id="2026_q2",
        )

        self.assertEqual(comp_event.period_id, "2026_q2")

    def test_deferred_accrual_not_implemented_yet(self):
        """Deferred accrual should return 0.0 (not implemented)."""
        benchmark = ActionBenchmark(
            action_id="test_14",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)
        comp_event = self.engine.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )

        self.assertEqual(comp_event.deferred_accrual, 0.0)

    def test_payout_rate_configurable(self):
        """Payout rate should be configurable."""
        engine_high_rate = CompensationEngine(payout_conversion_rate=100.0)
        engine_low_rate = CompensationEngine(payout_conversion_rate=25.0)

        benchmark = ActionBenchmark(
            action_id="test_15",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
            effort_intensity=100.0,
            output_quality=100.0,
            uniqueness=100.0,
            relational_capital=100.0,
            risk_reduction=100.0,
            probability_lift=100.0,
            multiplicative_effect=100.0,
            brand_adherence=100.0,
            interaction_effectiveness=100.0,
            economic_productivity=100.0,
            ethos_alignment=100.0,
            confidence=1.0,
        )
        nocs_result = NOCSEngine.calculate(benchmark, self.base_role)

        comp_high = engine_high_rate.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )
        comp_low = engine_low_rate.calculate(
            base_amount=1000.0,
            nocs_result=nocs_result,
            strategic_multiplier=1.0,
            ethos_alignment_score=75.0,
            penalties=0.0,
        )

        self.assertGreater(comp_high.variable_amount, comp_low.variable_amount)


if __name__ == "__main__":
    unittest.main()
