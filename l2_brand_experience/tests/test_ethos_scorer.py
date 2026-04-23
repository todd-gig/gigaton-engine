"""Unit tests for EthosScorer."""

import unittest
from l2_brand_experience.engines.ethos_scorer import EthosScorer


class TestEthosScorer(unittest.TestCase):
    """Tests for EthosScorer."""

    def test_dimension_weights_sum_to_one(self):
        """Verify dimension weights sum to exactly 1.0."""
        total = sum(EthosScorer.DIMENSION_WEIGHTS.values())
        self.assertAlmostEqual(total, 1.0, places=5)

    def test_all_dimensions_at_100_yields_coefficient_1_25(self):
        """All dimensions at 100 should yield composite 100 and coefficient 1.25."""
        dimensions = {
            "truthfulness_explainability": 100.0,
            "human_centered_technology": 100.0,
            "long_term_value_creation": 100.0,
            "cost_roi_discipline": 100.0,
            "human_agency_respect": 100.0,
            "trust_contribution": 100.0,
            "manipulation_avoidance": 100.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertEqual(score.composite_score, 100.0)
        self.assertEqual(score.coefficient, 1.25)

    def test_all_dimensions_at_90_yields_coefficient_1_25(self):
        """All dimensions at 90 should yield composite 90 and coefficient 1.25."""
        dimensions = {
            "truthfulness_explainability": 90.0,
            "human_centered_technology": 90.0,
            "long_term_value_creation": 90.0,
            "cost_roi_discipline": 90.0,
            "human_agency_respect": 90.0,
            "trust_contribution": 90.0,
            "manipulation_avoidance": 90.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertAlmostEqual(score.composite_score, 90.0, places=1)
        self.assertEqual(score.coefficient, 1.25)

    def test_all_dimensions_at_80_yields_coefficient_1_0(self):
        """All dimensions at 80 should yield composite 80 and coefficient 1.0."""
        dimensions = {
            "truthfulness_explainability": 80.0,
            "human_centered_technology": 80.0,
            "long_term_value_creation": 80.0,
            "cost_roi_discipline": 80.0,
            "human_agency_respect": 80.0,
            "trust_contribution": 80.0,
            "manipulation_avoidance": 80.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertAlmostEqual(score.composite_score, 80.0, places=1)
        self.assertEqual(score.coefficient, 1.0)

    def test_all_dimensions_at_70_yields_coefficient_1_0(self):
        """All dimensions at 70 should yield composite 70 and coefficient 1.0."""
        dimensions = {
            "truthfulness_explainability": 70.0,
            "human_centered_technology": 70.0,
            "long_term_value_creation": 70.0,
            "cost_roi_discipline": 70.0,
            "human_agency_respect": 70.0,
            "trust_contribution": 70.0,
            "manipulation_avoidance": 70.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertAlmostEqual(score.composite_score, 70.0, places=1)
        self.assertEqual(score.coefficient, 1.0)

    def test_all_dimensions_at_60_yields_coefficient_0_75(self):
        """All dimensions at 60 should yield composite 60 and coefficient 0.75."""
        dimensions = {
            "truthfulness_explainability": 60.0,
            "human_centered_technology": 60.0,
            "long_term_value_creation": 60.0,
            "cost_roi_discipline": 60.0,
            "human_agency_respect": 60.0,
            "trust_contribution": 60.0,
            "manipulation_avoidance": 60.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertAlmostEqual(score.composite_score, 60.0, places=1)
        self.assertEqual(score.coefficient, 0.75)

    def test_all_dimensions_at_50_yields_coefficient_0_75(self):
        """All dimensions at 50 should yield composite 50 and coefficient 0.75."""
        dimensions = {
            "truthfulness_explainability": 50.0,
            "human_centered_technology": 50.0,
            "long_term_value_creation": 50.0,
            "cost_roi_discipline": 50.0,
            "human_agency_respect": 50.0,
            "trust_contribution": 50.0,
            "manipulation_avoidance": 50.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertAlmostEqual(score.composite_score, 50.0, places=1)
        self.assertEqual(score.coefficient, 0.75)

    def test_all_dimensions_at_40_yields_coefficient_0_0(self):
        """All dimensions at 40 should yield composite 40 and coefficient 0.0 (disqualifying)."""
        dimensions = {
            "truthfulness_explainability": 40.0,
            "human_centered_technology": 40.0,
            "long_term_value_creation": 40.0,
            "cost_roi_discipline": 40.0,
            "human_agency_respect": 40.0,
            "trust_contribution": 40.0,
            "manipulation_avoidance": 40.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertAlmostEqual(score.composite_score, 40.0, places=1)
        self.assertEqual(score.coefficient, 0.0)

    def test_mixed_dimensions_weight_correctly(self):
        """Test that mixed dimension scores weight correctly to produce composite."""
        dimensions = {
            "truthfulness_explainability": 100.0,  # 0.20 weight
            "human_centered_technology": 50.0,  # 0.15 weight
            "long_term_value_creation": 50.0,  # 0.18 weight
            "cost_roi_discipline": 50.0,  # 0.12 weight
            "human_agency_respect": 50.0,  # 0.10 weight
            "trust_contribution": 50.0,  # 0.15 weight
            "manipulation_avoidance": 50.0,  # 0.10 weight
        }
        score = EthosScorer.score(dimensions)
        # Expected: 100*0.20 + 50*0.15 + 50*0.18 + 50*0.12 + 50*0.10 + 50*0.15 + 50*0.10
        #         = 20 + 7.5 + 9 + 6 + 5 + 7.5 + 5 = 60
        expected_composite = 60.0
        self.assertAlmostEqual(score.composite_score, expected_composite, places=1)

    def test_default_values_when_missing_dimensions(self):
        """Missing dimension keys should default to 50."""
        dimensions = {
            "truthfulness_explainability": 100.0,
        }
        score = EthosScorer.score(dimensions)
        # All other dimensions should default to 50
        self.assertEqual(score.human_centered_technology, 50.0)
        self.assertEqual(score.long_term_value_creation, 50.0)

    def test_dimension_bounds_validation(self):
        """Verify that scored dimensions respect 0-100 bounds."""
        dimensions = {
            "truthfulness_explainability": 75.0,
            "human_centered_technology": 85.0,
            "long_term_value_creation": 65.0,
            "cost_roi_discipline": 70.0,
            "human_agency_respect": 80.0,
            "trust_contribution": 55.0,
            "manipulation_avoidance": 90.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertTrue(score.validate_bounds())

    def test_disqualifying_score_detection(self):
        """Composite score < 50 should be flagged as disqualifying."""
        dimensions = {
            "truthfulness_explainability": 40.0,
            "human_centered_technology": 40.0,
            "long_term_value_creation": 40.0,
            "cost_roi_discipline": 40.0,
            "human_agency_respect": 40.0,
            "trust_contribution": 40.0,
            "manipulation_avoidance": 40.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertTrue(score.is_disqualifying())

    def test_non_disqualifying_score(self):
        """Composite score >= 50 should not be disqualifying."""
        dimensions = {
            "truthfulness_explainability": 50.0,
            "human_centered_technology": 50.0,
            "long_term_value_creation": 50.0,
            "cost_roi_discipline": 50.0,
            "human_agency_respect": 50.0,
            "trust_contribution": 50.0,
            "manipulation_avoidance": 50.0,
        }
        score = EthosScorer.score(dimensions)
        self.assertFalse(score.is_disqualifying())


if __name__ == "__main__":
    unittest.main()
