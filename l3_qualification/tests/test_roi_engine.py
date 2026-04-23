"""
Comprehensive tests for ROI Engine and OVS Engine

Tests cover:
- ROI calculation with known inputs
- Priority score formula components
- Trust multiplier tiers
- ROI thresholds
- OVS multiplicative scoring
- Portfolio ranking and resource allocation
"""

import unittest
import sys
import os

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _PROJECT_ROOT)

from l3_qualification.engines.roi_engine import (
    ROIEngine,
    OVSEngine,
    ROIInput,
    ROIResult,
    ImplementationCost,
    LeverageScope,
    HealthStatus,
    MaturityLevel,
    PeopleDimensions,
    ProcessDimensions,
    TechnologyDimensions,
    LearningDimensions,
)


class TestROIEngine(unittest.TestCase):
    """Test ROI calculation engine."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ROIEngine()

    def test_roi_calculation_basic(self):
        """Test basic ROI calculation with known inputs."""
        cost = ImplementationCost(
            personnel_cost=50000,
            capital_cost=30000,
            coordination_cost=10000,
            opportunity_cost=10000,
        )
        inp = ROIInput(
            name="Initiative A",
            annual_leakage_loss=100000,
            expected_performance_after=0.3,
            implementation_cost=cost,
            leverage_scope=LeverageScope.SINGLE_SYSTEM,
            confidence=0.8,
            complexity_score=0.3,
            org_readiness_gap=0.2,
            required_hours=1000,
            strategic_urgency=0.7,
        )
        result = self.engine.calculate(inp)

        # Expected values:
        # impact_value = 100000 * (1 - 0.3) = 70000
        # total_cost = 50000 + 30000 + 10000 + 10000 = 100000
        # risk_factor = (1 - 0.8) * 0.3 + 0.3 * 0.4 + 0.2 * 0.3 = 0.24
        # leverage_factor = 0.1 (SINGLE_SYSTEM)
        # roi_score = (70000 / 100000) * (1 + 0.1) * (1 - 0.24) = 0.7 * 1.1 * 0.76 ≈ 0.586

        self.assertEqual(result.name, "Initiative A")
        self.assertEqual(result.impact_value, 70000.0)
        self.assertEqual(result.total_cost, 100000.0)
        self.assertAlmostEqual(result.roi_score, 0.586, places=2)
        self.assertEqual(result.leverage_factor, 0.1)

    def test_roi_calculation_high_leverage(self):
        """Test ROI with three-systems leverage scope."""
        cost = ImplementationCost(personnel_cost=50000)
        inp = ROIInput(
            name="Multi-system Initiative",
            annual_leakage_loss=200000,
            expected_performance_after=0.2,
            implementation_cost=cost,
            leverage_scope=LeverageScope.THREE_SYSTEMS,
            confidence=0.9,
            complexity_score=0.2,
            org_readiness_gap=0.1,
            required_hours=500,
        )
        result = self.engine.calculate(inp)

        # leverage_factor = 0.6 (THREE_SYSTEMS)
        # impact_value = 200000 * 0.8 = 160000
        # risk_factor = (1 - 0.9) * 0.3 + 0.2 * 0.4 + 0.1 * 0.3 = 0.03 + 0.08 + 0.03 = 0.14
        # roi_score = (160000 / 50000) * (1 + 0.6) * (1 - 0.14)

        self.assertEqual(result.leverage_factor, 0.6)
        self.assertEqual(result.impact_value, 160000.0)
        self.assertAlmostEqual(result.risk_factor, 0.14, places=2)

    def test_roi_zero_cost_prevention(self):
        """Test that zero cost is prevented with minimum value of 1.0."""
        cost = ImplementationCost()  # All zeros
        inp = ROIInput(
            name="Zero Cost Initiative",
            annual_leakage_loss=50000,
            expected_performance_after=0.5,
            implementation_cost=cost,
        )
        result = self.engine.calculate(inp)

        # total_cost should be set to 1.0 to prevent division by zero
        self.assertEqual(result.total_cost, 1.0)

    def test_roi_negative_leakage_handled(self):
        """Test ROI with zero leakage (impact becomes zero)."""
        cost = ImplementationCost(personnel_cost=50000)
        inp = ROIInput(
            name="No Leakage",
            annual_leakage_loss=0,
            expected_performance_after=0.5,
            implementation_cost=cost,
        )
        result = self.engine.calculate(inp)

        # impact_value should be 0
        self.assertEqual(result.impact_value, 0.0)
        # ROI should be very low
        self.assertLess(result.roi_score, 0.1)

    def test_roi_passes_threshold(self):
        """Test that high ROI passes threshold."""
        cost = ImplementationCost(personnel_cost=10000)
        inp = ROIInput(
            name="High ROI",
            annual_leakage_loss=100000,
            expected_performance_after=0.1,
            implementation_cost=cost,
            leverage_scope=LeverageScope.THREE_SYSTEMS,
            confidence=0.95,
            complexity_score=0.1,
        )
        result = self.engine.calculate(inp)

        self.assertTrue(result.passes_threshold)
        self.assertGreaterEqual(result.roi_score, ROIEngine.ROI_THRESHOLD)

    def test_roi_fails_threshold(self):
        """Test that low ROI fails threshold."""
        cost = ImplementationCost(personnel_cost=100000)
        inp = ROIInput(
            name="Low ROI",
            annual_leakage_loss=50000,
            expected_performance_after=0.3,
            implementation_cost=cost,
            leverage_scope=LeverageScope.SINGLE_SYSTEM,
            confidence=0.5,
            complexity_score=0.8,
            org_readiness_gap=0.7,
        )
        result = self.engine.calculate(inp)

        self.assertFalse(result.passes_threshold)

    def test_value_per_hour_calculation(self):
        """Test value per hour metric."""
        cost = ImplementationCost(personnel_cost=50000)
        inp = ROIInput(
            name="Test Initiative",
            annual_leakage_loss=100000,
            expected_performance_after=0.5,
            implementation_cost=cost,
            required_hours=2000,
        )
        result = self.engine.calculate(inp)

        # impact_value = 100000 * 0.5 = 50000
        # value_per_hour = 50000 / 2000 = 25.0
        self.assertEqual(result.value_per_hour, 25.0)

    def test_value_per_hour_zero_hours(self):
        """Test value per hour with zero hours."""
        cost = ImplementationCost(personnel_cost=50000)
        inp = ROIInput(
            name="Zero Hours",
            annual_leakage_loss=100000,
            expected_performance_after=0.5,
            implementation_cost=cost,
            required_hours=0,
        )
        result = self.engine.calculate(inp)

        self.assertEqual(result.value_per_hour, 0.0)


class TestROIPortfolio(unittest.TestCase):
    """Test ROI portfolio ranking and resource allocation."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ROIEngine()

    def test_portfolio_ranking_basic(self):
        """Test portfolio ranking by ROI score."""
        inputs = [
            ROIInput(
                name="Initiative A",
                annual_leakage_loss=100000,
                expected_performance_after=0.3,
                implementation_cost=ImplementationCost(personnel_cost=50000),
                is_dependency_blocker=False,
                strategic_urgency=0.5,
            ),
            ROIInput(
                name="Initiative B",
                annual_leakage_loss=200000,
                expected_performance_after=0.2,
                implementation_cost=ImplementationCost(personnel_cost=50000),
                is_dependency_blocker=False,
                strategic_urgency=0.5,
            ),
        ]

        portfolio = self.engine.rank_portfolio(inputs)

        # B should rank higher (higher leakage = higher impact)
        self.assertEqual(len(portfolio.results), 2)
        self.assertEqual(portfolio.results[0].name, "Initiative B")
        self.assertEqual(portfolio.results[1].name, "Initiative A")

    def test_portfolio_ranking_dependency_blocker_first(self):
        """Test that dependency blockers rank first."""
        inputs = [
            ROIInput(
                name="High ROI",
                annual_leakage_loss=500000,
                expected_performance_after=0.1,
                implementation_cost=ImplementationCost(personnel_cost=100000),
                is_dependency_blocker=False,
                strategic_urgency=0.5,
            ),
            ROIInput(
                name="Blocker",
                annual_leakage_loss=50000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=50000),
                is_dependency_blocker=True,
                strategic_urgency=0.5,
            ),
        ]

        portfolio = self.engine.rank_portfolio(inputs)

        # Blocker should rank first
        self.assertEqual(portfolio.results[0].name, "Blocker")

    def test_portfolio_totals(self):
        """Test portfolio total calculations."""
        inputs = [
            ROIInput(
                name="A",
                annual_leakage_loss=100000,
                expected_performance_after=0.3,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
            ROIInput(
                name="B",
                annual_leakage_loss=100000,
                expected_performance_after=0.3,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
        ]

        portfolio = self.engine.rank_portfolio(inputs)

        # Each initiative: impact = 70000, cost = 50000
        self.assertEqual(portfolio.total_impact, 140000.0)
        self.assertEqual(portfolio.total_cost, 100000.0)
        self.assertAlmostEqual(portfolio.portfolio_roi, 1.4, places=1)

    def test_resource_allocation_basic(self):
        """Test greedy resource allocation."""
        inputs = [
            ROIInput(
                name="A",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=30000),
            ),
            ROIInput(
                name="B",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=40000),
            ),
            ROIInput(
                name="C",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
        ]

        portfolio = self.engine.rank_portfolio(inputs)
        allocation = self.engine.allocate_resources(portfolio, 75000)

        # Should allocate: A=30000, B=40000, C=5000 (partial)
        self.assertEqual(allocation["A"], 30000.0)
        self.assertEqual(allocation["B"], 40000.0)
        self.assertEqual(allocation["C"], 5000.0)

    def test_resource_allocation_exhausted_budget(self):
        """Test allocation when budget is fully exhausted."""
        inputs = [
            ROIInput(
                name="A",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
            ROIInput(
                name="B",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
        ]

        portfolio = self.engine.rank_portfolio(inputs)
        allocation = self.engine.allocate_resources(portfolio, 100000)

        # Both initiatives should get full allocation
        self.assertEqual(allocation["A"], 50000.0)
        self.assertEqual(allocation["B"], 50000.0)

    def test_resource_allocation_partial_last(self):
        """Test partial allocation of last initiative."""
        inputs = [
            ROIInput(
                name="A",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
            ROIInput(
                name="B",
                annual_leakage_loss=100000,
                expected_performance_after=0.5,
                implementation_cost=ImplementationCost(personnel_cost=50000),
            ),
        ]

        portfolio = self.engine.rank_portfolio(inputs)
        allocation = self.engine.allocate_resources(portfolio, 75000)

        # First gets 50000, second gets 25000
        self.assertEqual(allocation["A"], 50000.0)
        self.assertEqual(allocation["B"], 25000.0)


class TestOVSEngine(unittest.TestCase):
    """Test Organizational Value Score (OVS) engine."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = OVSEngine()

    def test_people_dimension_scoring(self):
        """Test people dimension score calculation."""
        dims = PeopleDimensions(
            cultural_diversity=0.8,
            decision_making_quality=0.9,
            relationship_cohesion=0.7,
            information_availability=0.6,
            learning_velocity=0.8,
        )

        score = self.engine.score_people(dims)

        # CD×0.25 + DMQ×0.25 + RC×0.20 + IA×0.20 + LV×0.10
        # = 0.8*0.25 + 0.9*0.25 + 0.7*0.20 + 0.6*0.20 + 0.8*0.10
        # = 0.2 + 0.225 + 0.14 + 0.12 + 0.08 = 0.765
        self.assertAlmostEqual(score, 0.765, places=2)

    def test_process_dimension_scoring(self):
        """Test process dimension score calculation."""
        dims = ProcessDimensions(
            standardization=0.7,
            efficiency=0.8,
            quality=0.6,
            automation=0.5,
            discipline=0.9,
        )

        score = self.engine.score_process(dims)

        # PS×0.25 + PE×0.25 + PQ×0.20 + PA×0.15 + PD×0.15
        # = 0.7*0.25 + 0.8*0.25 + 0.6*0.20 + 0.5*0.15 + 0.9*0.15
        # = 0.175 + 0.2 + 0.12 + 0.075 + 0.135 = 0.705
        self.assertAlmostEqual(score, 0.705, places=2)

    def test_technology_dimension_scoring(self):
        """Test technology dimension with inverted technical debt."""
        dims = TechnologyDimensions(
            reliability=0.8,
            capability=0.7,
            data_quality=0.9,
            technical_debt=0.3,  # Inverted: 1 - 0.3 = 0.7
            security=0.85,
        )

        score = self.engine.score_technology(dims)

        # SR×0.25 + SC×0.25 + DQ×0.25 + (1-TD)×0.15 + S×0.10
        # = 0.8*0.25 + 0.7*0.25 + 0.9*0.25 + 0.7*0.15 + 0.85*0.10
        # = 0.2 + 0.175 + 0.225 + 0.105 + 0.085 = 0.79
        self.assertAlmostEqual(score, 0.79, places=2)

    def test_learning_dimension_scoring(self):
        """Test learning dimension score calculation."""
        dims = LearningDimensions(
            learning_culture=0.8,
            knowledge_capture=0.75,
            knowledge_distribution=0.7,
            knowledge_application=0.85,
            learning_velocity=0.6,
        )

        score = self.engine.score_learning(dims)

        # LC×0.25 + KC×0.25 + KD×0.20 + KA×0.20 + LV×0.10
        # = 0.8*0.25 + 0.75*0.25 + 0.7*0.20 + 0.85*0.20 + 0.6*0.10
        # = 0.2 + 0.1875 + 0.14 + 0.17 + 0.06 = 0.7575
        self.assertAlmostEqual(score, 0.7575, places=2)

    def test_health_status_green(self):
        """Test health status classification for GREEN."""
        status = self.engine._health_status(0.8)
        self.assertEqual(status, HealthStatus.GREEN)

    def test_health_status_yellow(self):
        """Test health status classification for YELLOW."""
        status = self.engine._health_status(0.6)
        self.assertEqual(status, HealthStatus.YELLOW)

    def test_health_status_red(self):
        """Test health status classification for RED."""
        status = self.engine._health_status(0.4)
        self.assertEqual(status, HealthStatus.RED)

    def test_maturity_level_strategic(self):
        """Test maturity level classification for STRATEGIC_OPTIMIZATION."""
        level = self.engine._maturity_level(95.0)
        self.assertEqual(level, MaturityLevel.STRATEGIC_OPTIMIZATION)

    def test_maturity_level_integrated(self):
        """Test maturity level classification for INTEGRATED_CONTINUOUS_IMPROVEMENT."""
        level = self.engine._maturity_level(75.0)
        self.assertEqual(level, MaturityLevel.INTEGRATED_CONTINUOUS_IMPROVEMENT)

    def test_maturity_level_basic(self):
        """Test maturity level classification for BASIC_BASELINE."""
        level = self.engine._maturity_level(15.0)
        self.assertEqual(level, MaturityLevel.BASIC_BASELINE)

    def test_ovs_calculate_all_perfect(self):
        """Test OVS calculation with all perfect scores."""
        people = PeopleDimensions(1.0, 1.0, 1.0, 1.0, 1.0)
        process = ProcessDimensions(1.0, 1.0, 1.0, 1.0, 1.0)
        technology = TechnologyDimensions(1.0, 1.0, 1.0, 0.0, 1.0)
        learning = LearningDimensions(1.0, 1.0, 1.0, 1.0, 1.0)

        result = self.engine.calculate(people, process, technology, learning)

        # All dimensions = 1.0, so composite_ovs = 100.0
        # organizational_value = 1.0 * 1.0 * 1.0 * 1.0 = 1.0
        self.assertEqual(result.composite_ovs, 100.0)
        self.assertEqual(result.organizational_value, 1.0)
        self.assertEqual(result.maturity_level, MaturityLevel.STRATEGIC_OPTIMIZATION)

    def test_ovs_calculate_all_zero(self):
        """Test OVS calculation with all zero scores."""
        people = PeopleDimensions()
        process = ProcessDimensions()
        # Set technical_debt to 1.0 to invert to 0 contribution
        technology = TechnologyDimensions(0.0, 0.0, 0.0, 1.0, 0.0)
        learning = LearningDimensions()

        result = self.engine.calculate(people, process, technology, learning)

        # All dimensions = 0.0, so composite_ovs = 0.0
        # organizational_value = 0.0
        self.assertEqual(result.composite_ovs, 0.0)
        self.assertEqual(result.organizational_value, 0.0)
        self.assertEqual(result.maturity_level, MaturityLevel.BASIC_BASELINE)

    def test_ovs_multiplicative_property(self):
        """Test that organizational value is multiplicative."""
        people = PeopleDimensions(0.8, 0.8, 0.8, 0.8, 0.8)
        process = ProcessDimensions(0.9, 0.9, 0.9, 0.9, 0.9)
        technology = TechnologyDimensions(0.7, 0.7, 0.7, 0.3, 0.7)
        learning = LearningDimensions(0.6, 0.6, 0.6, 0.6, 0.6)

        result = self.engine.calculate(people, process, technology, learning)

        # Organizational value should be product of component scores
        # not sum or average
        self.assertLess(result.organizational_value, min(
            result.people_score,
            result.process_score,
            result.technology_score,
            result.learning_score,
        ))

    def test_ovs_dimension_details(self):
        """Test that dimension details are properly populated."""
        people = PeopleDimensions(0.8, 0.7, 0.6, 0.5, 0.9)
        process = ProcessDimensions(0.9, 0.8, 0.7, 0.6, 0.5)
        technology = TechnologyDimensions(0.8, 0.7, 0.6, 0.2, 0.9)
        learning = LearningDimensions(0.7, 0.6, 0.5, 0.8, 0.9)

        result = self.engine.calculate(people, process, technology, learning)

        # Check dimension details structure
        self.assertIn("people", result.dimension_details)
        self.assertIn("process", result.dimension_details)
        self.assertIn("technology", result.dimension_details)
        self.assertIn("learning", result.dimension_details)

        # Check that each dimension has proper structure
        people_detail = result.dimension_details["people"]
        self.assertEqual(people_detail.score, result.people_score)
        self.assertEqual(people_detail.status, HealthStatus.YELLOW)


if __name__ == "__main__":
    unittest.main()
