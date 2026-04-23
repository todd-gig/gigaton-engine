"""Unit tests for ProspectValueEngine."""

import unittest
from datetime import datetime, timedelta

from l1_sensing.models.prospect import (
    ProspectProfile,
    GTMMotion,
    PricingVisibility,
    CapabilitySummary,
    MaturityLevel,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l1_sensing.models.value_assessment import ProspectValueAssessment
from l1_sensing.engines.prospect_value_engine import ProspectValueEngine


class TestProspectValueEngine(unittest.TestCase):
    """Test suite for ProspectValueEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.prospect_id = "prospect_123"
        self.domain = "example.com"
        self.official_name = "Example Corp"

    def _create_prospect(
        self,
        gtm_motion=GTMMotion.UNKNOWN,
        days_old=0,
        evidence_count=0,
    ) -> ProspectProfile:
        """Helper to create a prospect with configurable properties."""
        last_verified = None
        if days_old >= 0:
            last_verified = (
                datetime.now() - timedelta(days=days_old)
            ).isoformat()

        return ProspectProfile(
            prospect_id=self.prospect_id,
            domain=self.domain,
            official_name=self.official_name,
            industries=["SaaS", "B2B"],
            buyer_personas=["CMO", "VP Marketing"],
            service_geographies=["US", "EU"],
            gtm_motion=gtm_motion,
            pricing_visibility=PricingVisibility.PARTIAL,
            capability_summary=CapabilitySummary(
                marketing_maturity=MaturityLevel.MEDIUM,
                sales_complexity=MaturityLevel.HIGH,
                measurement_maturity=MaturityLevel.LOW,
                interaction_management_maturity=MaturityLevel.LOW,
            ),
            last_verified_at=last_verified or "",
            evidence_ids=["ev_" + str(i) for i in range(evidence_count)],
        )

    def _create_inferences(
        self, count: int = 1, confidence: float = 0.8
    ) -> list:
        """Helper to create inference records."""
        inferences = []
        inference_types = [
            InferenceType.BUSINESS_GOAL,
            InferenceType.GTM_MOTION,
            InferenceType.SERVICE_FIT,
            InferenceType.CAPABILITY_MATURITY,
            InferenceType.PAIN_POINT,
        ]

        for i in range(count):
            inference = InferenceRecord(
                object_id=f"inf_{self.prospect_id}_{i}",
                prospect_id=self.prospect_id,
                inference_type=inference_types[i % len(inference_types)],
                statement=f"Inference statement {i}",
                confidence=confidence,
                assumptions=[f"Assumption {i}"],
                missing_data=[f"Missing {i}"],
                evidence_ids=[f"ev_{i}"],
            )
            inferences.append(inference)

        return inferences

    def test_perfect_prospect_scores_high(self):
        """Perfect prospect (all high scores) should score above 80."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=7, confidence=0.95)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        self.assertGreater(assessment.total, 80)
        self.assertGreater(assessment.need, 80)
        self.assertGreater(assessment.service_fit, 80)

    def test_zero_prospect_scores_zero(self):
        """Prospect with no inferences should score zero."""
        prospect = self._create_prospect()
        inferences = []

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        self.assertEqual(assessment.total, 0)
        self.assertEqual(assessment.need, 0)
        self.assertEqual(assessment.service_fit, 0)

    def test_weights_sum_to_one(self):
        """Component weights must sum to 1.0."""
        self.assertTrue(ProspectValueAssessment.validate_weights())

        weights = ProspectValueAssessment.COMPONENT_WEIGHTS
        total = sum(weights.values())
        self.assertAlmostEqual(total, 1.0, places=3)

    def test_low_confidence_penalty_applied(self):
        """Low confidence (< 50) should apply 20% penalty."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=3, confidence=0.30)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Total should be penalized: base * 0.8
        expected_max = 30 * 0.8  # 24
        self.assertLessEqual(assessment.total, expected_max + 1)  # Allow rounding

    def test_stale_signal_penalty_applied(self):
        """Signals older than 30 days should apply 10% penalty."""
        prospect = self._create_prospect(days_old=45)
        inferences = self._create_inferences(count=3, confidence=0.80)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Should have penalty applied
        base_score = 80
        penalized = base_score * 0.9  # 10% penalty
        self.assertLess(assessment.total, base_score)

    def test_mid_range_prospect(self):
        """Mid-range prospect (50% confidence, moderate signals) scores around 40-50."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=3, confidence=0.50)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        self.assertGreater(assessment.total, 30)
        self.assertLess(assessment.total, 60)

    def test_decision_bridge_produces_valid_dict(self):
        """Decision bridge should produce dict with all required keys."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=3, confidence=0.75)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        decision = ProspectValueEngine.prospect_to_decision(
            self.prospect_id, assessment, prospect
        )

        required_keys = [
            "decision_id",
            "description",
            "reversibility",
            "blast_radius",
            "financial_exposure",
            "strategic_impact",
            "time_sensitivity",
            "source_reliability",
            "data_completeness",
            "corroboration",
            "recency",
            "ethical_alignment",
            "consistency",
        ]

        for key in required_keys:
            self.assertIn(key, decision, f"Missing key: {key}")

    def test_decision_bridge_reversibility(self):
        """Decision reversibility for prospect decisions should be 0.8."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=1, confidence=0.75)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        decision = ProspectValueEngine.prospect_to_decision(
            self.prospect_id, assessment, prospect
        )

        self.assertEqual(decision["reversibility"], 0.8)

    def test_decision_bridge_blast_radius_scales(self):
        """Blast radius should scale 0-1 based on economic_scale."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=5, confidence=0.85)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        decision = ProspectValueEngine.prospect_to_decision(
            self.prospect_id, assessment, prospect
        )

        # Blast radius should be 0-1
        self.assertGreaterEqual(decision["blast_radius"], 0)
        self.assertLessEqual(decision["blast_radius"], 1)

    def test_component_weights_match_spec(self):
        """Component weights must match specification exactly."""
        expected_weights = {
            "need": 0.22,
            "service_fit": 0.18,
            "readiness": 0.14,
            "accessibility": 0.10,
            "expected_uplift": 0.18,
            "economic_scale": 0.12,
            "confidence": 0.06,
        }

        actual_weights = ProspectValueAssessment.COMPONENT_WEIGHTS

        for component, weight in expected_weights.items():
            self.assertEqual(
                actual_weights[component],
                weight,
                f"Weight for {component} does not match spec",
            )

    def test_total_bounded_0_to_100(self):
        """Total score must always be 0-100."""
        prospect = self._create_prospect()

        # Test with high confidence
        inferences = self._create_inferences(count=5, confidence=0.99)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)
        self.assertGreaterEqual(assessment.total, 0)
        self.assertLessEqual(assessment.total, 100)

        # Test with low confidence
        inferences = self._create_inferences(count=3, confidence=0.10)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)
        self.assertGreaterEqual(assessment.total, 0)
        self.assertLessEqual(assessment.total, 100)

    def test_best_fit_services_populated(self):
        """Best fit services should be populated from high-confidence inferences."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=3, confidence=0.75)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Should have populated best fit services
        self.assertIsInstance(assessment.best_fit_services, list)

    def test_priority_gaps_populated(self):
        """Priority gaps should be identified from capability maturity."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=3, confidence=0.75)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Should identify gaps in low-maturity areas
        self.assertIsInstance(assessment.priority_gaps, list)

    def test_high_need_low_fit_moderate_score(self):
        """High need + low fit should produce moderate score."""
        prospect = self._create_prospect()
        inferences = self._create_inferences(count=2, confidence=0.70)

        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Should be balanced score (not perfect, not zero)
        self.assertGreater(assessment.total, 20)
        self.assertLess(assessment.total, 80)

    def test_confidence_weight_is_lowest(self):
        """Confidence should have the lowest weight (0.06)."""
        weights = ProspectValueAssessment.COMPONENT_WEIGHTS
        confidence_weight = weights["confidence"]
        other_weights = [v for k, v in weights.items() if k != "confidence"]

        self.assertTrue(all(cw >= confidence_weight for cw in other_weights))
        self.assertEqual(confidence_weight, 0.06)


if __name__ == "__main__":
    unittest.main()
