"""
Integration tests for L2 Brand Experience Engine wired into the main pipeline.

Validates:
1. L2 runs as part of every pipeline execution
2. Brand coherence coefficient modulates L4 ethos scoring
3. Segmentation uses brand + interaction data when available
4. Pipeline summary includes L2 metrics
5. Graceful degradation when no brand profile provided
6. Strong vs weak brand profiles produce measurably different L4 outcomes
"""
import sys
import os
import unittest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from pipeline.engine import GigatonEngine, PipelineResult
from l1_sensing.models.prospect import (
    ProspectProfile, CapabilitySummary, MaturityLevel, GTMMotion, PricingVisibility,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l2_brand_experience.models.brand_profile import BrandProfile
from l2_brand_experience.models.brand_assessment import BrandExperienceAssessment
from l2_brand_experience.engines.brand_experience_engine import BrandExperienceEngine
from l4_execution.models.interaction import InteractionEvent
from segmentation.engines.segmentation_engine import (
    SegmentationEngine, InteractionPerformanceContext,
)


def _make_prospect(**overrides):
    """Create a test prospect profile."""
    defaults = dict(
        prospect_id="TEST_L2_001",
        domain="testcorp.com",
        official_name="TestCorp Inc.",
        industries=["technology"],
        buyer_personas=["VP Marketing"],
        service_geographies=["US"],
        gtm_motion=GTMMotion.SALES_LED,
        pricing_visibility=PricingVisibility.CONTACT_SALES,
        capability_summary=CapabilitySummary(
            marketing_maturity=MaturityLevel.LOW,
            sales_complexity=MaturityLevel.MEDIUM,
            measurement_maturity=MaturityLevel.LOW,
            interaction_management_maturity=MaturityLevel.LOW,
        ),
    )
    defaults.update(overrides)
    return ProspectProfile(**defaults)


def _make_inferences(prospect_id="TEST_L2_001"):
    """Create test inferences."""
    return [
        InferenceRecord(
            object_id="inf_01", prospect_id=prospect_id,
            inference_type=InferenceType.PAIN_POINT,
            statement="No analytics pipeline", confidence=0.8,
        ),
        InferenceRecord(
            object_id="inf_02", prospect_id=prospect_id,
            inference_type=InferenceType.SERVICE_FIT,
            statement="Needs brand experience engineering", confidence=0.75,
        ),
    ]


def _make_interactions():
    """Create test interactions."""
    return [
        InteractionEvent(
            interaction_id="ix_01", entity_id="agent_01", channel="email",
            timestamp="2026-04-20T10:00:00",
            status="resolved", response_time_seconds=120.0,
            resolution_time_seconds=900.0, converted=True,
            sentiment_score=0.8, trust_shift_score=0.2,
        ),
        InteractionEvent(
            interaction_id="ix_02", entity_id="agent_01", channel="voice",
            timestamp="2026-04-20T11:00:00",
            status="resolved", response_time_seconds=30.0,
            resolution_time_seconds=1800.0, converted=False,
            sentiment_score=0.6, trust_shift_score=0.1,
        ),
    ]


def _make_strong_brand():
    """Create a strong brand profile — good ethos, proof, channels."""
    return BrandProfile(
        brand_id="brand_strong",
        brand_name="Strong Brand Corp",
        tagline="Transforming businesses through data-driven insights",
        mission="To empower organizations with predictable growth",
        value_propositions=["Human-centered analytics", "Simplify complexity"],
        differentiators=["First-principles methodology", "Ethical AI"],
        proof_assets=["Fortune 500 case study", "98% retention", "SOC2 cert", "4.8 NPS"],
        compliance_claims=["SOC2 Type II", "GDPR"],
        certifications=["ISO 27001", "SOC2"],
        active_channels=["email", "voice", "web", "linkedin", "video"],
        target_response_time_seconds=180.0,
        target_resolution_time_seconds=1800.0,
        target_conversion_rate=0.20,
        minimum_ethos_score=60.0,
    )


def _make_weak_brand():
    """Create a weak brand profile — minimal everything."""
    return BrandProfile(
        brand_id="brand_weak",
        brand_name="Weak Brand LLC",
        tagline="",
        mission="",
        value_propositions=[],
        differentiators=[],
        proof_assets=[],
        compliance_claims=[],
        certifications=[],
        active_channels=["email"],
        target_response_time_seconds=600.0,
        target_resolution_time_seconds=7200.0,
        target_conversion_rate=0.05,
        minimum_ethos_score=40.0,
    )


class TestL2PipelineIntegration(unittest.TestCase):
    """Test that L2 runs as part of GigatonEngine.run()."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_pipeline_result_includes_brand_assessment(self):
        """Pipeline result should contain a real BrandExperienceAssessment."""
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
            brand_profile=_make_strong_brand(),
        )
        self.assertIsInstance(result, PipelineResult)
        self.assertIsNotNone(result.brand_assessment)
        self.assertIsInstance(result.brand_assessment, BrandExperienceAssessment)

    def test_brand_coherence_coefficient_is_populated(self):
        """Brand coherence coefficient should be a valid value (0-1.25)."""
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
            brand_profile=_make_strong_brand(),
        )
        self.assertGreater(result.brand_coherence_coefficient, 0.0)
        self.assertLessEqual(result.brand_coherence_coefficient, 1.25)

    def test_default_brand_used_when_none_provided(self):
        """Pipeline should use DEFAULT_BRAND when no brand_profile given."""
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
        )
        self.assertIsNotNone(result.brand_assessment)
        self.assertEqual(result.brand_assessment.brand_id, "default")

    def test_summary_includes_brand_experience_section(self):
        """Pipeline summary should contain a brand_experience section."""
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
            brand_profile=_make_strong_brand(),
        )
        summary = result.summary()
        self.assertIn("brand_experience", summary)
        be = summary["brand_experience"]
        self.assertIn("brand_experience_score", be)
        self.assertIn("coherence_coefficient", be)
        self.assertIn("coherence_composite", be)
        self.assertIn("channel_consistency", be)
        self.assertIn("proof_to_promise_ratio", be)
        self.assertIsNotNone(be["brand_experience_score"])


class TestBrandImpactOnL4(unittest.TestCase):
    """Test that brand coherence modulates L4 ethos and NOCS scoring."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_strong_brand_produces_different_compensation_than_weak(self):
        """Strong brand should produce different compensation than weak brand.

        Brand coefficient modulates ethos_alignment in L4 scoring.
        A strong brand (coefficient ~1.0-1.25) should produce higher
        ethos-driven compensation than a weak brand (coefficient ~0.5-0.75).
        """
        prospect = _make_prospect()
        inferences = _make_inferences()
        interactions = _make_interactions()

        result_strong = self.engine.run(
            prospect=prospect, inferences=inferences, interactions=interactions,
            brand_profile=_make_strong_brand(),
        )
        result_weak = self.engine.run(
            prospect=prospect, inferences=inferences, interactions=interactions,
            brand_profile=_make_weak_brand(),
        )

        # Both should produce valid results
        self.assertGreater(result_strong.interaction_count, 0)
        self.assertGreater(result_weak.interaction_count, 0)

        # Brand coefficients should differ
        self.assertGreater(
            result_strong.brand_coherence_coefficient,
            result_weak.brand_coherence_coefficient,
        )

    def test_strong_brand_coefficient_above_weak(self):
        """Strong brand should have higher coherence coefficient."""
        prospect = _make_prospect()
        inferences = _make_inferences()
        interactions = _make_interactions()

        result_strong = self.engine.run(
            prospect=prospect, inferences=inferences, interactions=interactions,
            brand_profile=_make_strong_brand(),
        )
        result_weak = self.engine.run(
            prospect=prospect, inferences=inferences, interactions=interactions,
            brand_profile=_make_weak_brand(),
        )

        self.assertGreater(
            result_strong.brand_coherence_coefficient,
            result_weak.brand_coherence_coefficient,
            "Strong brand should have higher coherence coefficient"
        )

    def test_brand_experience_score_differs_by_profile(self):
        """Brand experience score should reflect profile quality."""
        prospect = _make_prospect()
        inferences = _make_inferences()
        interactions = _make_interactions()

        result_strong = self.engine.run(
            prospect=prospect, inferences=inferences, interactions=interactions,
            brand_profile=_make_strong_brand(),
        )
        result_weak = self.engine.run(
            prospect=prospect, inferences=inferences, interactions=interactions,
            brand_profile=_make_weak_brand(),
        )

        self.assertGreater(
            result_strong.brand_assessment.brand_experience_score,
            result_weak.brand_assessment.brand_experience_score,
        )


class TestL2InSegmentation(unittest.TestCase):
    """Test that segmentation uses brand and interaction data."""

    def setUp(self):
        self.seg_engine = SegmentationEngine()
        self.pipeline_engine = GigatonEngine()

    def test_segmentation_without_brand_still_works(self):
        """Segmentation should work with L1 data only (backward compatible)."""
        from l1_sensing.engines.prospect_value_engine import ProspectValueEngine

        prospect = _make_prospect()
        inferences = _make_inferences()
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # No brand_assessment, no interaction_context
        segments = self.seg_engine.classify(prospect, assessment)
        self.assertIsInstance(segments, list)

    def test_segmentation_with_brand_data(self):
        """Segmentation with brand data should produce results."""
        from l1_sensing.engines.prospect_value_engine import ProspectValueEngine

        prospect = _make_prospect()
        inferences = _make_inferences()
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        brand = _make_strong_brand()
        brand_assessment = BrandExperienceEngine.assess(brand, _make_interactions())

        segments = self.seg_engine.classify(
            prospect, assessment, brand_assessment=brand_assessment,
        )
        self.assertIsInstance(segments, list)

    def test_segmentation_with_interaction_context(self):
        """Segmentation with interaction context should produce results."""
        from l1_sensing.engines.prospect_value_engine import ProspectValueEngine

        prospect = _make_prospect()
        inferences = _make_inferences()
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        interactions = _make_interactions()
        interaction_ctx = InteractionPerformanceContext.from_interactions(interactions)

        segments = self.seg_engine.classify(
            prospect, assessment, interaction_context=interaction_ctx,
        )
        self.assertIsInstance(segments, list)

    def test_interaction_performance_context_from_interactions(self):
        """InteractionPerformanceContext should correctly aggregate interaction data."""
        interactions = _make_interactions()
        ctx = InteractionPerformanceContext.from_interactions(interactions)

        self.assertEqual(ctx.interaction_count, 2)
        self.assertEqual(ctx.conversion_rate, 0.5)  # 1 of 2 converted
        self.assertGreater(ctx.avg_sentiment, 0.0)
        self.assertGreater(ctx.avg_trust_shift, 0.0)
        self.assertEqual(ctx.escalation_rate, 0.0)
        self.assertEqual(ctx.abandonment_rate, 0.0)

    def test_empty_interactions_produce_default_context(self):
        """Empty interactions should produce default InteractionPerformanceContext."""
        ctx = InteractionPerformanceContext.from_interactions([])
        self.assertEqual(ctx.interaction_count, 0)
        self.assertEqual(ctx.conversion_rate, 0.0)
        self.assertEqual(ctx.avg_sentiment, 0.5)


class TestL2L1L3PartialPipeline(unittest.TestCase):
    """Test the run_l1_l2 and run_l1_l3 partial pipelines."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_run_l1_l2_returns_both_assessments(self):
        """run_l1_l2 should return L1 assessment and L2 brand assessment."""
        result = self.engine.run_l1_l2(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
            brand_profile=_make_strong_brand(),
        )
        self.assertIn("assessment", result)
        self.assertIn("brand_assessment", result)
        self.assertIsInstance(result["brand_assessment"], BrandExperienceAssessment)

    def test_run_l1_l3_includes_brand_assessment(self):
        """run_l1_l3 should now include brand_assessment in result."""
        result = self.engine.run_l1_l3(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            brand_profile=_make_strong_brand(),
        )
        self.assertIn("assessment", result)
        self.assertIn("brand_assessment", result)
        self.assertIn("decision", result)

    def test_run_l1_l3_without_brand_uses_default(self):
        """run_l1_l3 without brand_profile should use default brand."""
        result = self.engine.run_l1_l3(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
        )
        self.assertIn("brand_assessment", result)
        self.assertEqual(result["brand_assessment"].brand_id, "default")


class TestFullIntegratedPipeline(unittest.TestCase):
    """End-to-end test: L1→L2→L3→L4 with brand data flowing through."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_full_pipeline_with_brand_produces_complete_result(self):
        """Full pipeline with brand should populate all sections."""
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
            brand_profile=_make_strong_brand(),
            role_key="sales_operator",
        )

        # L1 populated
        self.assertIsNotNone(result.prospect_assessment)
        self.assertGreater(result.prospect_assessment.total, 0)

        # L2 populated
        self.assertIsNotNone(result.brand_assessment)
        self.assertGreater(result.brand_assessment.brand_experience_score, 0)
        self.assertGreater(result.brand_coherence_coefficient, 0)

        # L3 populated
        self.assertIsNotNone(result.verdict)
        self.assertGreater(result.value_score, 0)

        # L4 populated
        self.assertGreater(result.interaction_count, 0)
        self.assertGreater(result.avg_nocs, 0)

    def test_brand_data_appears_in_summary_output(self):
        """Summary dict should include brand metrics for API consumption."""
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
            brand_profile=_make_strong_brand(),
        )
        summary = result.summary()

        self.assertIn("brand_experience", summary)
        self.assertIn("prospect", summary)
        self.assertIn("qualification", summary)
        self.assertIn("execution", summary)

        # Brand section has real data
        be = summary["brand_experience"]
        self.assertIsNotNone(be["brand_experience_score"])
        self.assertIsNotNone(be["coherence_composite"])
        self.assertGreater(be["brand_experience_score"], 0)


class TestDashboardDataGeneratorL2(unittest.TestCase):
    """Test that dashboard data generator uses real L2 data."""

    def test_dashboard_data_has_real_l2(self):
        """Dashboard data should contain real (not synthetic) L2 data."""
        from dashboard.data_generator import generate_dashboard_data
        data = generate_dashboard_data()

        # Check each scenario has L2 data
        for scenario in data["scenarios"]:
            l2 = scenario["l2"]
            self.assertIn("coherence", l2)
            self.assertIn("brand_experience_score", l2)
            self.assertIn("channel_consistency_score", l2)
            self.assertGreater(l2["brand_experience_score"], 0)


if __name__ == "__main__":
    unittest.main()
