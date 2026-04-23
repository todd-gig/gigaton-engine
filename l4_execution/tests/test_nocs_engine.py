"""Unit tests for NOCS Engine."""

import unittest

from l4_execution.engines.nocs_engine import NOCSEngine
from l4_execution.models.action_benchmark import ActionBenchmark
from l4_execution.models.role_profile import DEFAULT_WEIGHTS, ROLE_PROFILES, RoleProfile


class TestNOCSEngine(unittest.TestCase):
    """Tests for NOCSEngine."""

    def test_perfect_scores_yield_100(self):
        """All dimensions at 100 with confidence 1.0 should yield NOCS ~100."""
        benchmark = ActionBenchmark(
            action_id="test_1",
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
        role = RoleProfile.create_default("test_role", "Test Role")
        result = NOCSEngine.calculate(benchmark, role)
        self.assertAlmostEqual(result.final_nocs, 100.0, places=1)

    def test_zero_scores_yield_zero(self):
        """All dimensions at 0 with confidence 1.0 should yield NOCS 0."""
        benchmark = ActionBenchmark(
            action_id="test_2",
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
        role = RoleProfile.create_default("test_role", "Test Role")
        result = NOCSEngine.calculate(benchmark, role)
        self.assertAlmostEqual(result.final_nocs, 0.0, places=1)

    def test_role_weights_sum_to_one_default(self):
        """Default role weights should sum to ~1.0."""
        role = RoleProfile.create_default("test", "Test")
        self.assertTrue(role.validate_weights())

    def test_role_weights_sum_to_one_sales_operator(self):
        """Sales operator role weights should sum to ~1.0."""
        role = ROLE_PROFILES["sales_operator"]
        self.assertTrue(role.validate_weights())

    def test_role_weights_sum_to_one_ops_manager(self):
        """Operations manager role weights should sum to ~1.0."""
        role = ROLE_PROFILES["operations_manager"]
        self.assertTrue(role.validate_weights())

    def test_role_weights_sum_to_one_automation_builder(self):
        """Automation system builder role weights should sum to ~1.0."""
        role = ROLE_PROFILES["automation_system_builder"]
        self.assertTrue(role.validate_weights())

    def test_sales_operator_emphasizes_relational(self):
        """Sales operator should weight relational_capital highly."""
        # Create a benchmark where relational_capital is the only high dimension
        benchmark = ActionBenchmark(
            action_id="test_3",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            relational_capital=100.0,
            confidence=1.0,
        )
        role = ROLE_PROFILES["sales_operator"]
        result = NOCSEngine.calculate(benchmark, role)

        # Check that relational_capital weight is highest
        relational_weight = role.benchmark_weights["relational_capital"]
        interaction_weight = role.benchmark_weights["interaction_effectiveness"]
        self.assertGreater(relational_weight, 0.14)

    def test_ops_manager_emphasizes_risk_reduction(self):
        """Operations manager should weight risk_reduction highly."""
        benchmark = ActionBenchmark(
            action_id="test_4",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            risk_reduction=100.0,
            confidence=1.0,
        )
        role = ROLE_PROFILES["operations_manager"]
        result = NOCSEngine.calculate(benchmark, role)

        # Check that risk_reduction weight is highest
        risk_weight = role.benchmark_weights["risk_reduction"]
        self.assertGreater(risk_weight, 0.17)

    def test_automation_builder_emphasizes_multiplicative(self):
        """Automation builder should weight multiplicative_effect highly."""
        benchmark = ActionBenchmark(
            action_id="test_5",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            multiplicative_effect=100.0,
            confidence=1.0,
        )
        role = ROLE_PROFILES["automation_system_builder"]
        result = NOCSEngine.calculate(benchmark, role)

        # Check that multiplicative_effect weight is highest
        mult_weight = role.benchmark_weights["multiplicative_effect"]
        self.assertGreater(mult_weight, 0.2)

    def test_confidence_factor_applied(self):
        """Confidence factor should reduce final NOCS."""
        benchmark_high_conf = ActionBenchmark(
            action_id="test_6a",
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
        benchmark_low_conf = ActionBenchmark(
            action_id="test_6b",
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
            confidence=0.5,
        )
        role = RoleProfile.create_default("test", "Test")
        result_high = NOCSEngine.calculate(benchmark_high_conf, role)
        result_low = NOCSEngine.calculate(benchmark_low_conf, role)

        self.assertGreater(result_high.final_nocs, result_low.final_nocs)

    def test_low_confidence_reduces_nocs(self):
        """Low confidence should significantly reduce final NOCS."""
        benchmark = ActionBenchmark(
            action_id="test_7",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=80.0,
            effort_intensity=80.0,
            output_quality=80.0,
            uniqueness=80.0,
            relational_capital=80.0,
            risk_reduction=80.0,
            probability_lift=80.0,
            multiplicative_effect=80.0,
            brand_adherence=80.0,
            interaction_effectiveness=80.0,
            economic_productivity=80.0,
            ethos_alignment=80.0,
            confidence=0.2,
        )
        role = RoleProfile.create_default("test", "Test")
        result = NOCSEngine.calculate(benchmark, role)
        # With 0.2 confidence, final should be about 20% of raw
        self.assertLess(result.final_nocs, 50.0)

    def test_nocs_bounded_0_to_100(self):
        """NOCS results should always be between 0 and 100."""
        benchmark = ActionBenchmark(
            action_id="test_8",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=150.0,  # Exceeds bounds
            effort_intensity=150.0,
            confidence=2.0,  # Exceeds bounds
        )
        role = RoleProfile.create_default("test", "Test")
        result = NOCSEngine.calculate(benchmark, role)
        self.assertGreaterEqual(result.final_nocs, 0.0)
        self.assertLessEqual(result.final_nocs, 100.0)

    def test_component_scores_dict_populated(self):
        """Component scores should contain all 12 dimensions."""
        benchmark = ActionBenchmark(
            action_id="test_9",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=50.0,
            effort_intensity=50.0,
            output_quality=50.0,
            uniqueness=50.0,
            relational_capital=50.0,
            risk_reduction=50.0,
            probability_lift=50.0,
            multiplicative_effect=50.0,
            brand_adherence=50.0,
            interaction_effectiveness=50.0,
            economic_productivity=50.0,
            ethos_alignment=50.0,
            confidence=1.0,
        )
        role = RoleProfile.create_default("test", "Test")
        result = NOCSEngine.calculate(benchmark, role)

        expected_dimensions = {
            "time_leverage",
            "effort_intensity",
            "output_quality",
            "uniqueness",
            "relational_capital",
            "risk_reduction",
            "probability_lift",
            "multiplicative_effect",
            "brand_adherence",
            "interaction_effectiveness",
            "economic_productivity",
            "ethos_alignment",
        }
        self.assertEqual(set(result.component_scores.keys()), expected_dimensions)

    def test_default_weights_produce_balanced_score(self):
        """Default weights on uniform benchmark should yield score ~50."""
        benchmark = ActionBenchmark(
            action_id="test_10",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=50.0,
            effort_intensity=50.0,
            output_quality=50.0,
            uniqueness=50.0,
            relational_capital=50.0,
            risk_reduction=50.0,
            probability_lift=50.0,
            multiplicative_effect=50.0,
            brand_adherence=50.0,
            interaction_effectiveness=50.0,
            economic_productivity=50.0,
            ethos_alignment=50.0,
            confidence=1.0,
        )
        role = RoleProfile.create_default("test", "Test")
        result = NOCSEngine.calculate(benchmark, role)
        self.assertAlmostEqual(result.final_nocs, 50.0, places=0)

    def test_single_dimension_high_rest_zero(self):
        """Single high dimension with rest zero should reflect weight of that dimension."""
        benchmark = ActionBenchmark(
            action_id="test_11",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=100.0,
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
        role = RoleProfile.create_default("test", "Test")
        result = NOCSEngine.calculate(benchmark, role)
        # time_leverage weight is 0.08, so final_nocs should be ~8.0
        expected = 100.0 * DEFAULT_WEIGHTS["time_leverage"]
        self.assertAlmostEqual(result.final_nocs, expected, places=1)

    def test_mid_range_all_dimensions(self):
        """Mid-range scores on all dimensions should yield mid-range NOCS."""
        benchmark = ActionBenchmark(
            action_id="test_12",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=60.0,
            effort_intensity=60.0,
            output_quality=60.0,
            uniqueness=60.0,
            relational_capital=60.0,
            risk_reduction=60.0,
            probability_lift=60.0,
            multiplicative_effect=60.0,
            brand_adherence=60.0,
            interaction_effectiveness=60.0,
            economic_productivity=60.0,
            ethos_alignment=60.0,
            confidence=1.0,
        )
        role = RoleProfile.create_default("test", "Test")
        result = NOCSEngine.calculate(benchmark, role)
        self.assertGreater(result.final_nocs, 55.0)
        self.assertLess(result.final_nocs, 65.0)

    def test_role_id_preserved(self):
        """Role ID should be preserved in NOCS result."""
        benchmark = ActionBenchmark(
            action_id="test_13",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            confidence=1.0,
        )
        role = RoleProfile.create_predefined("sales_operator")
        result = NOCSEngine.calculate(benchmark, role)
        self.assertEqual(result.role_id, "sales_operator")

    def test_deterministic_same_input_same_output(self):
        """Same inputs should always produce same output."""
        benchmark = ActionBenchmark(
            action_id="test_14",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=75.0,
            effort_intensity=65.0,
            output_quality=80.0,
            uniqueness=55.0,
            relational_capital=70.0,
            risk_reduction=72.0,
            probability_lift=68.0,
            multiplicative_effect=60.0,
            brand_adherence=78.0,
            interaction_effectiveness=82.0,
            economic_productivity=71.0,
            ethos_alignment=79.0,
            confidence=0.85,
        )
        role = RoleProfile.create_predefined("operations_manager")

        result1 = NOCSEngine.calculate(benchmark, role)
        result2 = NOCSEngine.calculate(benchmark, role)

        self.assertEqual(result1.final_nocs, result2.final_nocs)
        self.assertEqual(result1.raw_nocs, result2.raw_nocs)
        self.assertEqual(result1.component_scores, result2.component_scores)


if __name__ == "__main__":
    unittest.main()
