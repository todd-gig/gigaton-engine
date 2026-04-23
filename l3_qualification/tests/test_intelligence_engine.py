"""
Comprehensive tests for Client Intelligence Engine

Tests cover:
- 15 master category scoring
- Gap analysis and priority ranking
- Category composite scores
- Overall weighted intelligence score
- Action item generation and prioritization
- Report generation
"""

import unittest
import sys
import os

# Add project root to path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _PROJECT_ROOT)

from l3_qualification.engines.intelligence_engine import (
    ClientIntelligenceEngine,
    CategoryScore,
    GapResult,
    ActionItem,
    GapSeverity,
    MASTER_CATEGORIES,
)


class TestCategoryScoring(unittest.TestCase):
    """Test category scoring functionality."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_score_category_valid(self):
        """Test scoring a valid category."""
        score = self.engine.score_category(
            category_key="customer",
            variable_strength=80,
            evidence_quality=70,
            execution_maturity=75,
            consistency=85,
            strategic_fit=90,
        )

        self.assertEqual(score.category_key, "customer")
        self.assertEqual(score.category_label, "Customer")
        self.assertEqual(score.variable_strength, 80)

    def test_score_category_invalid(self):
        """Test that invalid category raises error."""
        with self.assertRaises(ValueError):
            self.engine.score_category(
                category_key="invalid_category",
                variable_strength=50,
                evidence_quality=50,
                execution_maturity=50,
                consistency=50,
                strategic_fit=50,
            )

    def test_score_category_clamping(self):
        """Test that scores are clamped to 0-100 range."""
        score = self.engine.score_category(
            category_key="revenue",
            variable_strength=150,  # Over max
            evidence_quality=-50,  # Under min
            execution_maturity=50,
            consistency=50,
            strategic_fit=50,
        )

        self.assertEqual(score.variable_strength, 100)
        self.assertEqual(score.evidence_quality, 0)

    def test_composite_score_calculation(self):
        """Test category composite score formula."""
        score = self.engine.score_category(
            category_key="value_creation",
            variable_strength=100,
            evidence_quality=100,
            execution_maturity=100,
            consistency=100,
            strategic_fit=100,
        )

        composite = score.composite_score()

        # VS×0.35 + EQ×0.20 + EM×0.20 + CO×0.15 + SF×0.10 = 100
        self.assertEqual(composite, 100.0)

    def test_composite_score_weighted(self):
        """Test composite score with varied inputs."""
        score = self.engine.score_category(
            category_key="trust_credibility",
            variable_strength=80,
            evidence_quality=60,
            execution_maturity=70,
            consistency=50,
            strategic_fit=40,
        )

        composite = score.composite_score()

        # 80×0.35 + 60×0.20 + 70×0.20 + 50×0.15 + 40×0.10
        # = 28 + 12 + 14 + 7.5 + 4 = 65.5
        self.assertAlmostEqual(composite, 65.5, places=1)

    def test_composite_score_all_zeros(self):
        """Test composite score with all-zero inputs."""
        score = self.engine.score_category(
            category_key="market_reality",
            variable_strength=0,
            evidence_quality=0,
            execution_maturity=0,
            consistency=0,
            strategic_fit=0,
        )

        composite = score.composite_score()
        self.assertEqual(composite, 0.0)


class TestGapAnalysis(unittest.TestCase):
    """Test gap analysis functionality."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_analyze_gap_basic(self):
        """Test basic gap analysis."""
        gap = self.engine.analyze_gap(
            category_key="revenue",
            actual=60,
            target=85,
            strategic_importance=1.0,
            trust_penalty_modifier=1.0,
        )

        self.assertEqual(gap.category_key, "revenue")
        self.assertEqual(gap.actual, 60)
        self.assertEqual(gap.target, 85)

    def test_analyze_gap_invalid_category(self):
        """Test that invalid category raises error."""
        with self.assertRaises(ValueError):
            self.engine.analyze_gap(
                category_key="invalid",
                actual=50,
                target=75,
            )

    def test_gap_score_calculation(self):
        """Test gap score formula."""
        gap = self.engine.analyze_gap(
            category_key="customer",
            actual=60,
            target=90,
            strategic_importance=0.8,
            trust_penalty_modifier=1.0,
        )

        # gap_score = max(0, 90 - 60) × 0.8 × 1.0 = 30 × 0.8 = 24.0
        gap_score = gap.gap_score()
        self.assertEqual(gap_score, 24.0)

    def test_gap_score_no_gap(self):
        """Test gap score when actual >= target."""
        gap = self.engine.analyze_gap(
            category_key="growth_leverage",
            actual=80,
            target=75,
        )

        gap_score = gap.gap_score()
        self.assertEqual(gap_score, 0.0)

    def test_gap_severity_minor(self):
        """Test gap severity classification - MINOR."""
        gap = self.engine.analyze_gap(
            category_key="growth_leverage",
            actual=90,
            target=95,
        )

        severity = gap.gap_severity()
        self.assertEqual(severity, GapSeverity.MINOR)

    def test_gap_severity_moderate(self):
        """Test gap severity classification - MODERATE."""
        gap = self.engine.analyze_gap(
            category_key="growth_leverage",
            actual=70,
            target=90,
        )

        severity = gap.gap_severity()
        self.assertEqual(severity, GapSeverity.MODERATE)

    def test_gap_severity_major(self):
        """Test gap severity classification - MAJOR."""
        gap = self.engine.analyze_gap(
            category_key="growth_leverage",
            actual=50,
            target=90,
        )

        severity = gap.gap_severity()
        self.assertEqual(severity, GapSeverity.MAJOR)

    def test_gap_severity_critical(self):
        """Test gap severity classification - CRITICAL."""
        gap = self.engine.analyze_gap(
            category_key="growth_leverage",
            actual=10,
            target=90,
        )

        severity = gap.gap_severity()
        self.assertEqual(severity, GapSeverity.CRITICAL)


class TestActionGeneration(unittest.TestCase):
    """Test action item generation."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_generate_action_from_gap(self):
        """Test action generation from gap."""
        gap = self.engine.analyze_gap(
            category_key="customer",
            actual=50,
            target=80,
            strategic_importance=0.9,
            trust_penalty_modifier=1.0,
        )

        action = self.engine.generate_action(
            gap_result=gap,
            description="Improve customer satisfaction through NPS program",
            leverage=0.8,
            urgency=0.7,
            value_impact=0.85,
        )

        self.assertEqual(action.category_key, "customer")
        self.assertEqual(action.leverage, 0.8)
        self.assertEqual(action.urgency, 0.7)
        self.assertEqual(action.value_impact, 0.85)

    def test_action_priority_score(self):
        """Test action priority score calculation."""
        gap = self.engine.analyze_gap(
            category_key="value_creation",
            actual=50,
            target=90,
        )

        action = self.engine.generate_action(
            gap_result=gap,
            description="Enhance value delivery",
            leverage=0.9,
            urgency=0.8,
            value_impact=0.85,
        )

        priority = action.priority_score()

        # gap_score×0.35 + leverage×0.30 + urgency×0.20 + value_impact×0.15
        # = (40 × 0.35) + (0.9 × 0.30) + (0.8 × 0.20) + (0.85 × 0.15)
        # = 14 + 0.27 + 0.16 + 0.1275 = 14.5575
        self.assertGreater(priority, 0)


class TestActionPrioritization(unittest.TestCase):
    """Test action prioritization functionality."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_prioritize_actions_sorted_descending(self):
        """Test that actions are sorted by priority (descending)."""
        gap1 = self.engine.analyze_gap(
            category_key="customer", actual=50, target=90
        )
        action1 = self.engine.generate_action(
            gap_result=gap1,
            description="Action 1",
            leverage=0.5,
            urgency=0.5,
            value_impact=0.5,
        )

        gap2 = self.engine.analyze_gap(
            category_key="revenue", actual=50, target=90
        )
        action2 = self.engine.generate_action(
            gap_result=gap2,
            description="Action 2",
            leverage=0.9,
            urgency=0.9,
            value_impact=0.9,
        )

        actions = [action1, action2]
        prioritized = self.engine.prioritize_actions(actions)

        # action2 should rank higher
        self.assertEqual(prioritized[0].description, "Action 2")
        self.assertEqual(prioritized[1].description, "Action 1")


class TestOverallScoring(unittest.TestCase):
    """Test overall intelligence score calculation."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_overall_score_all_categories(self):
        """Test overall score calculation across all 15 categories."""
        category_scores = {}

        # Create scores for all 15 categories
        for key, info in MASTER_CATEGORIES.items():
            score = self.engine.score_category(
                category_key=key,
                variable_strength=80,
                evidence_quality=75,
                execution_maturity=70,
                consistency=85,
                strategic_fit=80,
            )
            category_scores[key] = score

        overall_score = self.engine.calculate_overall_score(category_scores)

        # All categories have same composite score, so overall should match
        self.assertGreater(overall_score, 0)
        self.assertLessEqual(overall_score, 100.0)

    def test_overall_score_weighted_by_category(self):
        """Test that categories with higher weights contribute more."""
        category_scores = {}

        # Create perfect scores for high-weight categories
        high_weight_categories = {
            "customer": 100,
            "value_creation": 100,
            "revenue": 100,
        }

        for key, info in MASTER_CATEGORIES.items():
            if key in high_weight_categories:
                # High score for high-weight categories
                value = 100
            else:
                # Low score for other categories
                value = 0

            score = self.engine.score_category(
                category_key=key,
                variable_strength=value,
                evidence_quality=value,
                execution_maturity=value,
                consistency=value,
                strategic_fit=value,
            )
            category_scores[key] = score

        overall_score = self.engine.calculate_overall_score(category_scores)

        # Three categories with 100 and 0.10 weight each = 0.30
        # So overall score should be 30.0
        self.assertAlmostEqual(overall_score, 30.0, places=1)

    def test_overall_score_all_zeros(self):
        """Test overall score with all zero scores."""
        category_scores = {}

        for key in MASTER_CATEGORIES.keys():
            score = self.engine.score_category(
                category_key=key,
                variable_strength=0,
                evidence_quality=0,
                execution_maturity=0,
                consistency=0,
                strategic_fit=0,
            )
            category_scores[key] = score

        overall_score = self.engine.calculate_overall_score(category_scores)

        self.assertEqual(overall_score, 0.0)

    def test_overall_score_all_perfect(self):
        """Test overall score with all perfect scores."""
        category_scores = {}

        for key in MASTER_CATEGORIES.keys():
            score = self.engine.score_category(
                category_key=key,
                variable_strength=100,
                evidence_quality=100,
                execution_maturity=100,
                consistency=100,
                strategic_fit=100,
            )
            category_scores[key] = score

        overall_score = self.engine.calculate_overall_score(category_scores)

        self.assertEqual(overall_score, 100.0)


class TestReportGeneration(unittest.TestCase):
    """Test client intelligence report generation."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_generate_report_complete(self):
        """Test complete report generation."""
        # Create category scores
        category_scores = {}
        for key in ["customer", "revenue", "value_creation"]:
            score = self.engine.score_category(
                category_key=key,
                variable_strength=75,
                evidence_quality=70,
                execution_maturity=80,
                consistency=75,
                strategic_fit=80,
            )
            category_scores[key] = score

        # Create gap results
        gap_results = {}
        for key in ["customer", "revenue"]:
            gap = self.engine.analyze_gap(
                category_key=key, actual=60, target=85
            )
            gap_results[key] = gap

        # Create action items
        action_items = []
        for gap in gap_results.values():
            action = self.engine.generate_action(
                gap_result=gap,
                description=f"Improve {gap.category_label}",
                leverage=0.8,
                urgency=0.7,
                value_impact=0.85,
            )
            action_items.append(action)

        # Generate report
        report = self.engine.generate_report(
            client_name="Acme Corp",
            report_date="2026-04-23",
            category_scores=category_scores,
            gap_results=gap_results,
            action_items=action_items,
            overall_trust_stage="T2_QUALIFIED",
        )

        self.assertEqual(report.client_name, "Acme Corp")
        self.assertEqual(report.report_date, "2026-04-23")
        self.assertEqual(report.overall_trust_stage, "T2_QUALIFIED")
        self.assertEqual(len(report.category_scores), 3)
        self.assertEqual(len(report.gap_results), 2)
        self.assertGreater(len(report.action_items), 0)

    def test_report_actions_prioritized(self):
        """Test that actions in report are prioritized."""
        category_scores = {
            "customer": self.engine.score_category(
                "customer", 50, 50, 50, 50, 50
            ),
        }

        gap1 = self.engine.analyze_gap("customer", actual=50, target=90)
        action1 = self.engine.generate_action(
            gap_result=gap1,
            description="Low priority action",
            leverage=0.3,
            urgency=0.2,
            value_impact=0.2,
        )

        action2 = self.engine.generate_action(
            gap_result=gap1,
            description="High priority action",
            leverage=0.9,
            urgency=0.9,
            value_impact=0.9,
        )

        report = self.engine.generate_report(
            client_name="Test Client",
            report_date="2026-04-23",
            category_scores=category_scores,
            gap_results={"customer": gap1},
            action_items=[action1, action2],
        )

        # High priority action should be first
        self.assertEqual(report.action_items[0].description, "High priority action")


class TestCategoryInfo(unittest.TestCase):
    """Test category information retrieval."""

    def setUp(self):
        """Initialize test fixtures."""
        self.engine = ClientIntelligenceEngine()

    def test_get_category_info_valid(self):
        """Test getting info for valid category."""
        info = self.engine.get_category_info("customer")

        self.assertEqual(info["label"], "Customer")
        self.assertEqual(info["weight"], 0.10)
        self.assertIn("variables", info)

    def test_get_category_info_invalid(self):
        """Test that invalid category raises error."""
        with self.assertRaises(ValueError):
            self.engine.get_category_info("invalid_category")

    def test_list_categories_complete(self):
        """Test listing all 15 categories."""
        categories = self.engine.list_categories()

        self.assertEqual(len(categories), 15)

        # Verify all expected categories present
        keys = [c["key"] for c in categories]
        self.assertIn("customer", keys)
        self.assertIn("revenue", keys)
        self.assertIn("identity_purpose", keys)

    def test_list_categories_structure(self):
        """Test that category list has correct structure."""
        categories = self.engine.list_categories()

        for category in categories:
            self.assertIn("key", category)
            self.assertIn("label", category)
            self.assertIn("weight", category)
            self.assertIn("variables", category)


if __name__ == "__main__":
    unittest.main()
