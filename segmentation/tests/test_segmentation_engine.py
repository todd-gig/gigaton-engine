"""Unit tests for SegmentationEngine."""

import unittest
from l1_sensing.models.prospect import (
    ProspectProfile,
    GTMMotion,
    PricingVisibility,
    CapabilitySummary,
    MaturityLevel,
)
from l1_sensing.models.value_assessment import ProspectValueAssessment
from l2_brand_experience.models.brand_assessment import BrandExperienceAssessment
from l2_brand_experience.models.brand_coherence import BrandCoherenceScore
from segmentation.engines.segmentation_engine import SegmentationEngine
from segmentation.segment_library import SEGMENT_LIBRARY


class TestSegmentationEngine(unittest.TestCase):
    """Test suite for SegmentationEngine."""

    def setUp(self):
        """Set up test fixtures."""
        self.engine = SegmentationEngine()

    def _create_prospect(
        self,
        gtm_motion=GTMMotion.UNKNOWN,
        marketing_maturity=MaturityLevel.UNKNOWN,
        sales_complexity=MaturityLevel.UNKNOWN,
        measurement_maturity=MaturityLevel.UNKNOWN,
        interaction_management_maturity=MaturityLevel.UNKNOWN,
    ) -> ProspectProfile:
        """Helper to create a prospect with configurable capabilities."""
        return ProspectProfile(
            prospect_id="prospect_test_123",
            domain="example.com",
            official_name="Example Corp",
            industries=["SaaS", "Technology"],
            buyer_personas=["CMO", "VP Marketing"],
            service_geographies=["US", "EU"],
            gtm_motion=gtm_motion,
            pricing_visibility=PricingVisibility.PARTIAL,
            capability_summary=CapabilitySummary(
                marketing_maturity=marketing_maturity,
                sales_complexity=sales_complexity,
                measurement_maturity=measurement_maturity,
                interaction_management_maturity=interaction_management_maturity,
            ),
            last_verified_at="2026-04-21T00:00:00Z",
            evidence_ids=["ev_1", "ev_2"],
        )

    def _create_assessment(
        self,
        economic_scale=50,
        fit_score=50,
        need=50,
        service_fit=50,
        readiness=50,
        accessibility=50,
        expected_uplift=50,
        confidence=50,
    ) -> ProspectValueAssessment:
        """Helper to create a value assessment with configurable scores."""
        total = (
            need * 0.22
            + service_fit * 0.18
            + readiness * 0.14
            + accessibility * 0.10
            + expected_uplift * 0.18
            + economic_scale * 0.12
            + confidence * 0.06
        )
        return ProspectValueAssessment(
            need=need,
            service_fit=service_fit,
            readiness=readiness,
            accessibility=accessibility,
            expected_uplift=expected_uplift,
            economic_scale=economic_scale,
            confidence=confidence,
            total=total,
            best_fit_services=["Service A", "Service B"],
            priority_gaps=["Gap 1", "Gap 2"],
        )

    def test_classify_high_growth_prospect(self):
        """Test classifying a high-growth prospect → matches SEG_001."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        matches = self.engine.classify(prospect, assessment)

        # Should match SEG_001
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].segment_id, "SEG_001")

    def test_classify_enterprise_prospect(self):
        """Test classifying enterprise prospect → matches SEG_002."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            sales_complexity=MaturityLevel.HIGH,
            marketing_maturity=MaturityLevel.HIGH,
            measurement_maturity=MaturityLevel.MEDIUM,
        )
        assessment = self._create_assessment(economic_scale=80, fit_score=60)

        matches = self.engine.classify(prospect, assessment)

        # Should match SEG_002
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].segment_id, "SEG_002")

    def test_classify_content_rich_prospect(self):
        """Test classifying content-rich prospect → matches SEG_003."""
        prospect = self._create_prospect(
            marketing_maturity=MaturityLevel.MEDIUM,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=60, fit_score=50)

        matches = self.engine.classify(prospect, assessment)

        # Should match SEG_003
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].segment_id, "SEG_003")

    def test_classify_plg_prospect(self):
        """Test classifying PLG prospect → matches SEG_004."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.PLG,
            marketing_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=50, fit_score=50)

        matches = self.engine.classify(prospect, assessment)

        # Should match SEG_004
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].segment_id, "SEG_004")

    def test_classify_brand_narrative_prospect(self):
        """Test classifying brand narrative prospect → matches SEG_005."""
        prospect = self._create_prospect(
            sales_complexity=MaturityLevel.HIGH,
            marketing_maturity=MaturityLevel.HIGH,
            interaction_management_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=50, fit_score=60)

        matches = self.engine.classify(prospect, assessment)

        # Should match SEG_005
        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].segment_id, "SEG_005")

    def test_classify_weak_prospect_matches_nothing(self):
        """Test weak prospect with low scores matches nothing."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.UNKNOWN,
            marketing_maturity=MaturityLevel.UNKNOWN,
        )
        assessment = self._create_assessment(
            economic_scale=20, fit_score=15, need=10, readiness=5
        )

        matches = self.engine.classify(prospect, assessment)

        # Should match nothing
        self.assertEqual(len(matches), 0)

    def test_classify_multiple_segment_matches(self):
        """Test prospect that matches multiple segments returns sorted list."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.HYBRID,
            marketing_maturity=MaturityLevel.MEDIUM,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=65, fit_score=60)

        matches = self.engine.classify(prospect, assessment)

        # Should match multiple segments, sorted by priority_tier first
        self.assertTrue(len(matches) >= 2)
        # Check that priority_tier is ascending
        for i in range(len(matches) - 1):
            self.assertLessEqual(matches[i].priority_tier, matches[i + 1].priority_tier)

    def test_classify_single_returns_best_match(self):
        """Test classify_single returns best-fit segment only."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        segment = self.engine.classify_single(prospect, assessment)

        # Should return single segment
        self.assertIsNotNone(segment)
        self.assertEqual(segment.segment_id, "SEG_001")

    def test_classify_single_returns_none_if_no_match(self):
        """Test classify_single returns None if no segment matches."""
        prospect = self._create_prospect(gtm_motion=GTMMotion.UNKNOWN)
        assessment = self._create_assessment(economic_scale=15, fit_score=10)

        segment = self.engine.classify_single(prospect, assessment)

        self.assertIsNone(segment)

    def test_get_apollo_targeting_returns_valid_filters(self):
        """Test get_apollo_targeting returns valid Apollo filter dict."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        filters = self.engine.get_apollo_targeting(prospect, assessment)

        # Should return dict with filters
        self.assertIsNotNone(filters)
        self.assertIsInstance(filters, dict)

    def test_apollo_targeting_contains_expected_keys(self):
        """Test Apollo targeting filters contain expected keys."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        filters = self.engine.get_apollo_targeting(prospect, assessment)

        # SEG_001 should have these keys
        self.assertIn("organization_industry_tag_ids", filters)
        self.assertIn("person_titles", filters)
        self.assertIn("person_seniorities", filters)
        self.assertIn("person_departments", filters)

    def test_apollo_targeting_returns_none_if_no_match(self):
        """Test get_apollo_targeting returns None if no segment matches."""
        prospect = self._create_prospect(gtm_motion=GTMMotion.UNKNOWN)
        assessment = self._create_assessment(economic_scale=15, fit_score=10)

        filters = self.engine.get_apollo_targeting(prospect, assessment)

        self.assertIsNone(filters)

    def test_numeric_range_criteria_matching(self):
        """Test numeric range criteria matching works correctly."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        # economic_scale must be 60-100 for SEG_001
        assessment_low = self._create_assessment(economic_scale=55, fit_score=70)
        assessment_high = self._create_assessment(economic_scale=75, fit_score=70)
        assessment_exact_min = self._create_assessment(economic_scale=60, fit_score=70)
        assessment_exact_max = self._create_assessment(economic_scale=100, fit_score=70)

        # These should NOT match (below range)
        matches_low = self.engine.classify(prospect, assessment_low)
        self.assertEqual(len(matches_low), 0)

        # These SHOULD match (in range)
        matches_high = self.engine.classify(prospect, assessment_high)
        self.assertTrue(len(matches_high) > 0)

        matches_exact_min = self.engine.classify(prospect, assessment_exact_min)
        self.assertTrue(len(matches_exact_min) > 0)

        matches_exact_max = self.engine.classify(prospect, assessment_exact_max)
        self.assertTrue(len(matches_exact_max) > 0)

    def test_enum_value_criteria_matching(self):
        """Test enum value criteria matching works correctly."""
        prospect_sales_led = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        prospect_hybrid = self._create_prospect(
            gtm_motion=GTMMotion.HYBRID,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        prospect_plg = self._create_prospect(
            gtm_motion=GTMMotion.PLG,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )

        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        # SEG_001 accepts ("sales_led", "hybrid")
        matches_sales_led = self.engine.classify(prospect_sales_led, assessment)
        self.assertTrue(any(s.segment_id == "SEG_001" for s in matches_sales_led))

        matches_hybrid = self.engine.classify(prospect_hybrid, assessment)
        self.assertTrue(any(s.segment_id == "SEG_001" for s in matches_hybrid))

        # PLG should NOT match SEG_001
        matches_plg = self.engine.classify(prospect_plg, assessment)
        self.assertFalse(any(s.segment_id == "SEG_001" for s in matches_plg))

    def test_brand_assessment_context_doesnt_break_classification(self):
        """Test that optional brand assessment doesn't break classification."""
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
            measurement_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        # Create brand assessment
        brand_assessment = BrandExperienceAssessment(
            brand_id="brand_123",
            coherence=BrandCoherenceScore(
                truthfulness_explainability=70,
                human_centered_technology=80,
                long_term_value_creation=75,
                cost_roi_discipline=60,
                human_agency_respect=65,
                trust_contribution=70,
                manipulation_avoidance=70,
                composite_score=70,
            ),
        )

        # Should still work with brand assessment
        matches = self.engine.classify(prospect, assessment, brand_assessment)

        self.assertTrue(len(matches) > 0)
        self.assertEqual(matches[0].segment_id, "SEG_001")

    def test_empty_segment_library_returns_no_matches(self):
        """Test empty segment library returns no matches."""
        engine_empty = SegmentationEngine({})

        prospect = self._create_prospect(
            gtm_motion=GTMMotion.SALES_LED,
            marketing_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=75, fit_score=70)

        matches = engine_empty.classify(prospect, assessment)

        self.assertEqual(len(matches), 0)

    def test_segment_sorting_by_priority_and_value(self):
        """Test that matching segments are sorted by priority_tier then value."""
        # Create a prospect that could match multiple segments
        prospect = self._create_prospect(
            gtm_motion=GTMMotion.HYBRID,
            marketing_maturity=MaturityLevel.MEDIUM,
            sales_complexity=MaturityLevel.HIGH,
            measurement_maturity=MaturityLevel.LOW,
            interaction_management_maturity=MaturityLevel.LOW,
        )
        assessment = self._create_assessment(economic_scale=65, fit_score=60)

        matches = self.engine.classify(prospect, assessment)

        if len(matches) >= 2:
            # Check priority_tier ordering (lower numbers first)
            for i in range(len(matches) - 1):
                self.assertLessEqual(
                    matches[i].priority_tier,
                    matches[i + 1].priority_tier,
                )

                # If same priority_tier, check value midpoint ordering (higher first)
                if matches[i].priority_tier == matches[i + 1].priority_tier:
                    midpoint_i = (
                        matches[i].expected_value_range[0]
                        + matches[i].expected_value_range[1]
                    ) / 2
                    midpoint_i_plus_1 = (
                        matches[i + 1].expected_value_range[0]
                        + matches[i + 1].expected_value_range[1]
                    ) / 2
                    self.assertGreaterEqual(midpoint_i, midpoint_i_plus_1)


if __name__ == "__main__":
    unittest.main()
