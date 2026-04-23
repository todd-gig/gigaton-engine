"""Unit tests for expanded role profiles (7 total roles)."""

import unittest

from l4_execution.engines.nocs_engine import NOCSEngine
from l4_execution.models.action_benchmark import ActionBenchmark
from l4_execution.models.role_profile import ROLE_PROFILES, ROLE_PROFILES_DATA, RoleProfile


class TestExpandedRoleWeights(unittest.TestCase):
    """Test that all 7 roles have valid weights summing to 1.0."""

    def test_all_roles_present(self):
        """Test that all 7 roles are defined."""
        expected_roles = [
            "sales_operator",
            "cx_marketing_operator",
            "founder_exec",
            "operations_manager",
            "brand_manager",
            "automation_system_builder",
            "analyst_forecaster",
        ]
        for role_key in expected_roles:
            self.assertIn(role_key, ROLE_PROFILES_DATA)

    def test_sales_operator_weights_sum_to_one(self):
        """Test sales_operator weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["sales_operator"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_cx_marketing_operator_weights_sum_to_one(self):
        """Test cx_marketing_operator weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["cx_marketing_operator"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_founder_exec_weights_sum_to_one(self):
        """Test founder_exec weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["founder_exec"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_operations_manager_weights_sum_to_one(self):
        """Test operations_manager weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["operations_manager"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_brand_manager_weights_sum_to_one(self):
        """Test brand_manager weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["brand_manager"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_automation_system_builder_weights_sum_to_one(self):
        """Test automation_system_builder weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["automation_system_builder"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)

    def test_analyst_forecaster_weights_sum_to_one(self):
        """Test analyst_forecaster weights sum to 1.0."""
        weights = ROLE_PROFILES_DATA["analyst_forecaster"]
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=10)


class TestRoleProfileCreation(unittest.TestCase):
    """Test that all roles can be created and accessed."""

    def test_create_predefined_sales_operator(self):
        """Test creating sales_operator from predefined."""
        role = RoleProfile.create_predefined("sales_operator")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "sales_operator")
        self.assertTrue(role.validate_weights())

    def test_create_predefined_cx_marketing_operator(self):
        """Test creating cx_marketing_operator from predefined."""
        role = RoleProfile.create_predefined("cx_marketing_operator")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "cx_marketing_operator")
        self.assertTrue(role.validate_weights())

    def test_create_predefined_founder_exec(self):
        """Test creating founder_exec from predefined."""
        role = RoleProfile.create_predefined("founder_exec")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "founder_exec")
        self.assertTrue(role.validate_weights())

    def test_create_predefined_operations_manager(self):
        """Test creating operations_manager from predefined."""
        role = RoleProfile.create_predefined("operations_manager")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "operations_manager")
        self.assertTrue(role.validate_weights())

    def test_create_predefined_brand_manager(self):
        """Test creating brand_manager from predefined."""
        role = RoleProfile.create_predefined("brand_manager")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "brand_manager")
        self.assertTrue(role.validate_weights())

    def test_create_predefined_automation_system_builder(self):
        """Test creating automation_system_builder from predefined."""
        role = RoleProfile.create_predefined("automation_system_builder")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "automation_system_builder")
        self.assertTrue(role.validate_weights())

    def test_create_predefined_analyst_forecaster(self):
        """Test creating analyst_forecaster from predefined."""
        role = RoleProfile.create_predefined("analyst_forecaster")
        self.assertIsNotNone(role)
        self.assertEqual(role.role_id, "analyst_forecaster")
        self.assertTrue(role.validate_weights())

    def test_all_roles_accessible_via_dictionary(self):
        """Test all roles accessible via ROLE_PROFILES dictionary."""
        expected_keys = [
            "sales_operator",
            "cx_marketing_operator",
            "founder_exec",
            "operations_manager",
            "brand_manager",
            "automation_system_builder",
            "analyst_forecaster",
        ]
        for key in expected_keys:
            self.assertIn(key, ROLE_PROFILES)
            self.assertIsInstance(ROLE_PROFILES[key], RoleProfile)


class TestRoleCharacteristics(unittest.TestCase):
    """Test role-specific emphasis on dimensions."""

    def test_cx_marketing_operator_emphasizes_brand_adherence(self):
        """Test CX marketing operator has high brand_adherence weight."""
        role = ROLE_PROFILES["cx_marketing_operator"]
        # brand_adherence should be among the highest for this role
        weights = role.benchmark_weights
        self.assertEqual(weights["brand_adherence"], 0.18)

    def test_cx_marketing_operator_emphasizes_interaction_effectiveness(self):
        """Test CX marketing operator emphasizes interaction_effectiveness."""
        role = ROLE_PROFILES["cx_marketing_operator"]
        weights = role.benchmark_weights
        self.assertEqual(weights["interaction_effectiveness"], 0.14)

    def test_cx_marketing_operator_emphasizes_relational_capital(self):
        """Test CX marketing operator emphasizes relational_capital."""
        role = ROLE_PROFILES["cx_marketing_operator"]
        weights = role.benchmark_weights
        self.assertEqual(weights["relational_capital"], 0.14)

    def test_founder_exec_emphasizes_probability_lift(self):
        """Test founder_exec emphasizes probability_lift."""
        role = ROLE_PROFILES["founder_exec"]
        weights = role.benchmark_weights
        self.assertEqual(weights["probability_lift"], 0.16)

    def test_founder_exec_emphasizes_risk_reduction(self):
        """Test founder_exec emphasizes risk_reduction."""
        role = ROLE_PROFILES["founder_exec"]
        weights = role.benchmark_weights
        self.assertEqual(weights["risk_reduction"], 0.16)

    def test_founder_exec_emphasizes_multiplicative_effect(self):
        """Test founder_exec emphasizes multiplicative_effect."""
        role = ROLE_PROFILES["founder_exec"]
        weights = role.benchmark_weights
        self.assertEqual(weights["multiplicative_effect"], 0.14)

    def test_founder_exec_emphasizes_economic_productivity(self):
        """Test founder_exec emphasizes economic_productivity."""
        role = ROLE_PROFILES["founder_exec"]
        weights = role.benchmark_weights
        self.assertEqual(weights["economic_productivity"], 0.12)

    def test_brand_manager_emphasizes_brand_adherence(self):
        """Test brand_manager has highest brand_adherence weight."""
        role = ROLE_PROFILES["brand_manager"]
        weights = role.benchmark_weights
        self.assertEqual(weights["brand_adherence"], 0.22)

    def test_brand_manager_emphasizes_output_quality(self):
        """Test brand_manager emphasizes output_quality."""
        role = ROLE_PROFILES["brand_manager"]
        weights = role.benchmark_weights
        self.assertEqual(weights["output_quality"], 0.14)

    def test_brand_manager_emphasizes_ethos_alignment(self):
        """Test brand_manager emphasizes ethos_alignment."""
        role = ROLE_PROFILES["brand_manager"]
        weights = role.benchmark_weights
        self.assertEqual(weights["ethos_alignment"], 0.12)

    def test_analyst_forecaster_emphasizes_output_quality(self):
        """Test analyst_forecaster emphasizes output_quality."""
        role = ROLE_PROFILES["analyst_forecaster"]
        weights = role.benchmark_weights
        self.assertEqual(weights["output_quality"], 0.16)

    def test_analyst_forecaster_emphasizes_risk_reduction(self):
        """Test analyst_forecaster emphasizes risk_reduction."""
        role = ROLE_PROFILES["analyst_forecaster"]
        weights = role.benchmark_weights
        self.assertEqual(weights["risk_reduction"], 0.14)

    def test_analyst_forecaster_emphasizes_probability_lift(self):
        """Test analyst_forecaster emphasizes probability_lift."""
        role = ROLE_PROFILES["analyst_forecaster"]
        weights = role.benchmark_weights
        self.assertEqual(weights["probability_lift"], 0.14)

    def test_analyst_forecaster_emphasizes_economic_productivity(self):
        """Test analyst_forecaster emphasizes economic_productivity."""
        role = ROLE_PROFILES["analyst_forecaster"]
        weights = role.benchmark_weights
        self.assertEqual(weights["economic_productivity"], 0.14)


class TestNOCSScoresVaryByRole(unittest.TestCase):
    """Test that NOCS scores differ across roles for same benchmark."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a benchmark with mixed scores
        self.benchmark = ActionBenchmark(
            action_id="test_1",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=60.0,
            effort_intensity=70.0,
            output_quality=80.0,
            uniqueness=50.0,
            relational_capital=75.0,
            risk_reduction=65.0,
            probability_lift=85.0,
            multiplicative_effect=55.0,
            brand_adherence=90.0,
            interaction_effectiveness=80.0,
            economic_productivity=70.0,
            ethos_alignment=60.0,
            confidence=0.85,
        )

    def test_sales_vs_analyst_nocs_differs(self):
        """Test that sales_operator and analyst_forecaster yield different NOCS."""
        sales_role = ROLE_PROFILES["sales_operator"]
        analyst_role = ROLE_PROFILES["analyst_forecaster"]

        sales_result = NOCSEngine.calculate(self.benchmark, sales_role)
        analyst_result = NOCSEngine.calculate(self.benchmark, analyst_role)

        # Scores should differ due to different weight emphasis
        self.assertNotAlmostEqual(
            sales_result.final_nocs, analyst_result.final_nocs, places=1
        )

    def test_cx_marketing_vs_founder_nocs_differs(self):
        """Test that cx_marketing_operator and founder_exec yield different NOCS."""
        cx_role = ROLE_PROFILES["cx_marketing_operator"]
        founder_role = ROLE_PROFILES["founder_exec"]

        cx_result = NOCSEngine.calculate(self.benchmark, cx_role)
        founder_result = NOCSEngine.calculate(self.benchmark, founder_role)

        # Scores should differ due to different weight emphasis
        self.assertNotAlmostEqual(
            cx_result.final_nocs, founder_result.final_nocs, places=1
        )

    def test_brand_manager_emphasizes_brand_adherence_in_score(self):
        """Test that brand_manager scores higher on brand_adherence-heavy benchmark."""
        # Create benchmark with high brand_adherence but low probability_lift
        brand_benchmark = ActionBenchmark(
            action_id="brand_test",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=30.0,
            effort_intensity=30.0,
            output_quality=50.0,
            uniqueness=30.0,
            relational_capital=30.0,
            risk_reduction=30.0,
            probability_lift=20.0,
            multiplicative_effect=30.0,
            brand_adherence=95.0,  # Very high brand adherence
            interaction_effectiveness=50.0,
            economic_productivity=30.0,
            ethos_alignment=80.0,
            confidence=0.9,
        )

        brand_manager = ROLE_PROFILES["brand_manager"]
        founder_exec = ROLE_PROFILES["founder_exec"]

        brand_score = NOCSEngine.calculate(brand_benchmark, brand_manager)
        founder_score = NOCSEngine.calculate(brand_benchmark, founder_exec)

        # Brand manager should score higher due to brand_adherence emphasis
        self.assertGreater(brand_score.final_nocs, founder_score.final_nocs)

    def test_founder_exec_emphasizes_probability_lift_in_score(self):
        """Test that founder_exec scores higher on probability_lift-heavy benchmark."""
        # Create benchmark with high probability_lift but low brand_adherence
        prob_benchmark = ActionBenchmark(
            action_id="prob_test",
            actor_id="actor_1",
            timestamp="2026-04-21T00:00:00Z",
            action_type="test",
            time_leverage=30.0,
            effort_intensity=30.0,
            output_quality=50.0,
            uniqueness=30.0,
            relational_capital=30.0,
            risk_reduction=85.0,
            probability_lift=95.0,  # Very high probability lift
            multiplicative_effect=80.0,
            brand_adherence=20.0,
            interaction_effectiveness=50.0,
            economic_productivity=85.0,
            ethos_alignment=40.0,
            confidence=0.9,
        )

        brand_manager = ROLE_PROFILES["brand_manager"]
        founder_exec = ROLE_PROFILES["founder_exec"]

        brand_score = NOCSEngine.calculate(prob_benchmark, brand_manager)
        founder_score = NOCSEngine.calculate(prob_benchmark, founder_exec)

        # Founder exec should score higher due to probability_lift emphasis
        self.assertGreater(founder_score.final_nocs, brand_score.final_nocs)


if __name__ == "__main__":
    unittest.main()
