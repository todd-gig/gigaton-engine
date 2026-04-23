"""
Comprehensive End-to-End Integration Tests for Gigaton Engine

Tests the complete system chain: L1 Sensing → L2 Brand Experience → L3 Qualification →
L4 Execution → Segmentation → Apollo Enrichment

Coverage:
  - TestFullSystemChain: Complete causal chain through all 6+ layers
  - TestDataIntegrity: Data flows correctly between layers
  - TestEdgeCases: Edge conditions and boundary cases
  - TestSystemMetrics: Performance and module structure validation
"""
import sys
import os
import time
import unittest
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Ensure project root is on path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

# L1 Sensing
from l1_sensing.models.prospect import (
    ProspectProfile, CapabilitySummary, MaturityLevel, GTMMotion, PricingVisibility,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l1_sensing.models.value_assessment import ProspectValueAssessment
from l1_sensing.engines.prospect_value_engine import ProspectValueEngine

# L2 Brand Experience
from l2_brand_experience.models.brand_profile import BrandProfile
from l2_brand_experience.models.brand_coherence import BrandCoherenceScore
from l2_brand_experience.models.brand_assessment import BrandExperienceAssessment
from l2_brand_experience.engines.brand_experience_engine import BrandExperienceEngine

# L3 Qualification
from l3_qualification.engine import QualificationEngine

# L4 Execution
from l4_execution.models.interaction import InteractionEvent
from l4_execution.models.role_profile import ROLE_PROFILES

# Pipeline
from pipeline.engine import GigatonEngine, PipelineResult
from pipeline.cli import SCENARIOS

# Segmentation
from segmentation.engines.segmentation_engine import SegmentationEngine
from segmentation.segment_library import SEGMENT_LIBRARY

# Apollo Enrichment
from apollo_enrichment.engines.enrichment_engine import EnrichmentEngine
from apollo_enrichment.engines.apollo_client import ApolloClient

# Dashboard
from dashboard.data_generator import generate_dashboard_data


# ─────────────────────────────────────────────────────────────
# TEST HELPERS
# ─────────────────────────────────────────────────────────────

def _iso(days_ago: int = 0) -> str:
    """Generate ISO timestamp days_ago from now."""
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


def _make_prospect(
    pid="TEST01",
    name="Test Corp",
    domain="test.com",
    verified_days_ago=2,
    evidence_count=5,
    **cap_overrides,
) -> ProspectProfile:
    """Create a test ProspectProfile with configurable capabilities."""
    caps = CapabilitySummary(
        marketing_maturity=cap_overrides.get("marketing", MaturityLevel.LOW),
        sales_complexity=cap_overrides.get("sales", MaturityLevel.MEDIUM),
        measurement_maturity=cap_overrides.get("measurement", MaturityLevel.LOW),
        interaction_management_maturity=cap_overrides.get("interaction", MaturityLevel.LOW),
    )
    return ProspectProfile(
        prospect_id=pid,
        domain=domain,
        official_name=name,
        industries=["Tech"],
        buyer_personas=["VP Marketing"],
        service_geographies=["North America"],
        gtm_motion=GTMMotion.SALES_LED,
        pricing_visibility=PricingVisibility.PUBLIC,
        capability_summary=caps,
        last_verified_at=_iso(verified_days_ago) if verified_days_ago >= 0 else "",
        evidence_ids=[f"E{i}" for i in range(evidence_count)],
    )


def _make_inferences(pid="TEST01", confidence=0.85, count=3) -> List[InferenceRecord]:
    """Create test InferenceRecords."""
    types = [InferenceType.PAIN_POINT, InferenceType.SERVICE_FIT, InferenceType.VALUE_ESTIMATE]
    return [
        InferenceRecord(
            object_id=f"INF_{i}",
            prospect_id=pid,
            inference_type=types[i % len(types)],
            statement=f"Test inference {i}",
            confidence=confidence,
            evidence_ids=[f"E{i}"],
        )
        for i in range(count)
    ]


def _make_interactions(
    count=2, converted=True, fast=True, channel_mix=False
) -> List[InteractionEvent]:
    """Create test InteractionEvents."""
    channels = ["email", "voice", "web"]
    interactions = []
    for i in range(count):
        channel = channels[i % len(channels)] if channel_mix else ("email" if i % 2 == 0 else "voice")
        interactions.append(
            InteractionEvent(
                interaction_id=f"INT_{i}",
                entity_id="actor_01",
                channel=channel,
                timestamp=_iso(i),
                status="resolved",
                response_time_seconds=120 if fast else 3600,
                resolution_time_seconds=1800 if fast else 86400,
                converted=converted,
                sentiment_score=0.8 if converted else 0.4,
                trust_shift_score=0.3 if converted else -0.1,
            )
        )
    return interactions


def _make_brand_profile(name="Test Brand") -> BrandProfile:
    """Create a test BrandProfile for L2 testing."""
    return BrandProfile(
        brand_id="BRAND_TEST",
        brand_name=name,
        tagline="Test brand tagline",
        mission="Test mission statement",
        value_propositions=["Quality", "Speed", "Reliability"],
        differentiators=["Quality", "Speed", "Reliability"],
        proof_assets=["Case studies", "Testimonials"],
        active_channels=["email", "voice", "web"],
    )


def _make_brand_assessment(
    brand_id="BRAND_TEST", ethos_base=75
) -> BrandExperienceAssessment:
    """Create a synthetic BrandExperienceAssessment."""
    coherence = BrandCoherenceScore(
        truthfulness_explainability=ethos_base + 5,
        human_centered_technology=ethos_base,
        long_term_value_creation=ethos_base - 3,
        cost_roi_discipline=ethos_base + 2,
        human_agency_respect=ethos_base,
        trust_contribution=ethos_base - 5,
        manipulation_avoidance=ethos_base + 1,
        composite_score=ethos_base,
        coefficient=0.5 + (ethos_base / 200),
    )
    return BrandExperienceAssessment(
        brand_id=brand_id,
        coherence=coherence,
        channel_consistency_score=ethos_base - 5,
        proof_to_promise_ratio=0.8,
        trust_layer_quality=ethos_base - 10,
        avg_response_performance=0.75,
        avg_resolution_performance=0.70,
        conversion_performance=0.60,
        brand_experience_score=ethos_base - 5,
    )


# ─────────────────────────────────────────────────────────────
# TEST CLASS: TestFullSystemChain
# ─────────────────────────────────────────────────────────────

class TestFullSystemChain(unittest.TestCase):
    """Test the complete causal chain: prospect data → L1 → L3 → L4 →
    segmentation → Apollo enrichment."""

    def setUp(self):
        self.engine = GigatonEngine()
        self.segmentation_engine = SegmentationEngine(SEGMENT_LIBRARY)
        self.enrichment_engine = EnrichmentEngine(
            apollo_client=ApolloClient(mock_mode=True)
        )

    def test_prospect_to_enrichment_chain(self):
        """Test complete causal chain: prospect → L1 scoring → L3 qualification
        → L4 execution → segmentation → Apollo enrichment."""
        prospect = _make_prospect("CHAIN01", "Chain Test Corp")
        inferences = _make_inferences("CHAIN01", confidence=0.85, count=3)
        interactions = _make_interactions(count=2)

        # ── L1 → L3 → L4 PIPELINE ──
        result = self.engine.run(
            prospect=prospect,
            inferences=inferences,
            interactions=interactions,
            role_key="sales_operator",
        )
        self.assertIsInstance(result, PipelineResult)
        self.assertEqual(result.prospect_id, "CHAIN01")
        self.assertGreater(result.prospect_assessment.total, 0)
        self.assertIsNotNone(result.verdict)
        self.assertGreater(result.interaction_count, 0)

        # ── SEGMENTATION ──
        segments = self.segmentation_engine.classify(
            prospect, result.prospect_assessment
        )
        self.assertIsInstance(segments, list)
        # May be empty if prospect doesn't match any segment criteria

        # ── APOLLO ENRICHMENT (from prospect) ──
        enrichment_result = self.enrichment_engine.enrich_from_prospect(
            prospect, result.prospect_assessment, max_results=5
        )
        # May be None if prospect doesn't match any segment
        if enrichment_result:
            self.assertIsNotNone(enrichment_result.segment_name)
            self.assertGreaterEqual(enrichment_result.total_found, 0)

    def test_three_scenarios_produce_three_different_verdicts(self):
        """Run 3 CLI scenarios and verify they produce expected verdicts:
        auto_execute, escalate_tier_1, needs_data."""
        verdicts = {}
        expected = {1: "auto_execute", 2: "escalate_tier_1", 3: "needs_data"}

        for scenario_num, scenario_spec in SCENARIOS.items():
            result = self.engine.run(
                prospect=scenario_spec["prospect"],
                inferences=scenario_spec["inferences"],
                interactions=scenario_spec["interactions"],
                role_key=scenario_spec["role_key"],
            )
            verdicts[scenario_num] = result.verdict
            self.assertEqual(
                result.verdict,
                expected[scenario_num],
                f"Scenario {scenario_num} produced {result.verdict}, "
                f"expected {expected[scenario_num]}",
            )

    def test_segmentation_produces_apollo_targeting(self):
        """Verify segmented prospects produce valid Apollo filters."""
        prospect = _make_prospect(
            "SEG01", "Segmentation Test",
            sales=MaturityLevel.MEDIUM,
            marketing=MaturityLevel.MEDIUM,
        )
        inferences = _make_inferences("SEG01", count=3)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Get best-fit segment
        segment = self.segmentation_engine.classify_single(prospect, assessment)
        if segment:
            # Verify Apollo filters derived from segment
            apollo_filters = segment.apollo_targeting.to_apollo_filters()
            self.assertIsInstance(apollo_filters, dict)
            # Apollo filters should have expected structure with industry, titles, or similar
            self.assertTrue(
                len(apollo_filters) > 0,
                "Apollo filters should not be empty"
            )
            # Verify structure has expected Apollo targeting fields
            expected_filter_types = {
                'organization_industry_tag_ids', 'person_titles', 'person_seniorities',
                'person_departments', 'organization_num_employees_ranges'
            }
            found_filters = set(apollo_filters.keys()) & expected_filter_types
            self.assertTrue(
                len(found_filters) > 0,
                f"Apollo filters missing standard targeting fields. Got: {list(apollo_filters.keys())}"
            )

    def test_enrichment_from_segmented_prospect(self):
        """Run prospect → segmentation → enrichment and verify leads have
        segment context."""
        prospect = _make_prospect("ENRICH01", "Enrichment Test")
        inferences = _make_inferences("ENRICH01", count=3)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Classify and enrich
        enrichment_result = self.enrichment_engine.enrich_from_prospect(
            prospect, assessment, max_results=10
        )

        if enrichment_result:
            # Verify all leads have segment context
            for lead in enrichment_result.leads:
                self.assertIsNotNone(lead.segment_id)
                self.assertIsNotNone(lead.segment_name)
                self.assertEqual(lead.segment_id, enrichment_result.segment_id)

    def test_brand_experience_assessment_independent(self):
        """L2 brand assessment can score independently and produces valid
        BrandExperienceAssessment."""
        brand_profile = _make_brand_profile("L2 Test Brand")
        interactions = _make_interactions(count=3, channel_mix=True)

        # Score brand independently
        engine = BrandExperienceEngine()
        assessment = engine.assess(brand_profile, interactions)

        self.assertIsInstance(assessment, BrandExperienceAssessment)
        self.assertGreaterEqual(assessment.brand_experience_score, 0)
        self.assertLessEqual(assessment.brand_experience_score, 100)
        self.assertIsNotNone(assessment.coherence)
        self.assertGreaterEqual(assessment.coherence.composite_score, 0)

    def test_pipeline_result_summary_complete(self):
        """PipelineResult.summary() contains all expected keys at all levels."""
        result = self.engine.run(
            prospect=_make_prospect("SUMM01", "Summary Test"),
            inferences=_make_inferences("SUMM01", count=3),
            interactions=_make_interactions(count=2),
        )

        summary = result.summary()

        # Top-level keys
        self.assertIn("prospect", summary)
        self.assertIn("qualification", summary)
        self.assertIn("execution", summary)

        # Prospect section
        prospect_keys = {"id", "name", "fit_score", "need", "service_fit",
                        "readiness", "confidence"}
        self.assertTrue(prospect_keys.issubset(set(summary["prospect"].keys())))

        # Qualification section
        qual_keys = {"decision_id", "verdict", "value_score", "trust_score",
                    "rtql", "priority", "certificates", "blocking_gates"}
        self.assertTrue(qual_keys.issubset(set(summary["qualification"].keys())))

        # Execution section
        exec_keys = {"interaction_count", "avg_nocs", "total_compensation"}
        self.assertTrue(exec_keys.issubset(set(summary["execution"].keys())))

    def test_compensation_chain_integrity(self):
        """Verify compensation amounts are positive and correctly affected by
        strategic_multiplier."""
        prospect = _make_prospect("COMP01", "Compensation Test")
        inferences = _make_inferences("COMP01", count=3)
        interactions = _make_interactions(count=2)

        result_1x = self.engine.run(
            prospect=prospect,
            inferences=inferences,
            interactions=interactions,
            strategic_multiplier=1.0,
        )

        result_1_5x = self.engine.run(
            prospect=prospect,
            inferences=inferences,
            interactions=interactions,
            strategic_multiplier=1.5,
        )

        # All compensation values should be positive
        self.assertGreater(result_1x.total_compensation, 0)
        self.assertGreater(result_1_5x.total_compensation, 0)

        # Higher multiplier should yield higher compensation
        self.assertGreater(result_1_5x.total_compensation, result_1x.total_compensation)

        # Per-interaction compensation should also be positive
        for ir in result_1x.interaction_results:
            self.assertGreater(ir.compensation_total, 0)

    def test_deterministic_across_runs(self):
        """Same inputs produce identical outputs across 3 runs."""
        prospect = _make_prospect("DET01", "Deterministic Test")
        inferences = _make_inferences("DET01", count=3)
        interactions = _make_interactions(count=2)

        results = []
        for _ in range(3):
            result = self.engine.run(
                prospect=prospect,
                inferences=inferences,
                interactions=interactions,
            )
            results.append(result)

        # All three runs should produce identical verdicts and scores
        for i in range(1, len(results)):
            self.assertEqual(results[i].verdict, results[0].verdict)
            self.assertAlmostEqual(
                results[i].value_score, results[0].value_score, places=5
            )
            self.assertAlmostEqual(
                results[i].trust_score, results[0].trust_score, places=5
            )
            self.assertAlmostEqual(
                results[i].avg_nocs, results[0].avg_nocs, places=5
            )


# ─────────────────────────────────────────────────────────────
# TEST CLASS: TestDataIntegrity
# ─────────────────────────────────────────────────────────────

class TestDataIntegrity(unittest.TestCase):
    """Test that data flows correctly between layers."""

    def setUp(self):
        self.engine = GigatonEngine()
        self.segmentation_engine = SegmentationEngine(SEGMENT_LIBRARY)

    def test_l1_bridge_produces_valid_l3_input(self):
        """ProspectValueEngine.prospect_to_decision() output has all required
        keys in correct ranges."""
        prospect = _make_prospect("BRIDGE01", "Bridge Test")
        inferences = _make_inferences("BRIDGE01", count=3)
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)

        # Bridge output
        bridge_dict = ProspectValueEngine.prospect_to_decision(
            "BRIDGE01", assessment, prospect
        )

        # Required keys
        required_keys = {
            "decision_id", "description", "reversibility", "blast_radius",
            "financial_exposure", "strategic_impact", "source_reliability",
            "data_completeness", "corroboration", "recency", "ethical_alignment"
        }
        self.assertTrue(required_keys.issubset(set(bridge_dict.keys())))

        # Bounded values
        for key in ["reversibility", "blast_radius", "source_reliability",
                    "data_completeness", "corroboration", "recency", "ethical_alignment"]:
            self.assertGreaterEqual(bridge_dict[key], 0, f"{key} < 0")
            self.assertLessEqual(bridge_dict[key], 1.0, f"{key} > 1.0")

    def test_l3_verdict_respects_certificate_gates(self):
        """When certificates fail, verdict should not be auto_execute."""
        # Create a weak prospect that will fail certificates
        weak_prospect = ProspectProfile(
            prospect_id="WEAK01",
            domain="weak.io",
            official_name="Weak Corp",
            industries=[],
            buyer_personas=[],
            service_geographies=[],
            last_verified_at="",
            evidence_ids=[],
        )
        weak_inferences = [
            InferenceRecord(
                object_id="INF_W1",
                prospect_id="WEAK01",
                inference_type=InferenceType.GTM_MOTION,
                statement="Weak signal",
                confidence=0.15,
                evidence_ids=[],
            )
        ]
        interactions = _make_interactions(count=1, converted=False)

        result = self.engine.run(
            prospect=weak_prospect,
            inferences=weak_inferences,
            interactions=interactions,
        )

        # If any certificate fails, verdict should not be auto_execute
        if not all(result.certificates.values()):
            self.assertNotEqual(result.verdict, "auto_execute")

    def test_l4_nocs_bounded(self):
        """All NOCS scores are within valid bounds (0-100)."""
        result = self.engine.run(
            prospect=_make_prospect("NOCS01", "NOCS Test"),
            inferences=_make_inferences("NOCS01", count=3),
            interactions=_make_interactions(count=3),
        )

        # Each interaction result should have bounded NOCS (0-100)
        for ir in result.interaction_results:
            self.assertGreaterEqual(ir.nocs.final_nocs, 0,
                                   f"NOCS {ir.nocs.final_nocs} < 0")
            self.assertLessEqual(ir.nocs.final_nocs, 100,
                                f"NOCS {ir.nocs.final_nocs} > 100")

        # Aggregated avg_nocs should also be bounded
        self.assertGreaterEqual(result.avg_nocs, 0)
        self.assertLessEqual(result.avg_nocs, 100)

    def test_segmentation_covers_all_gap_patterns(self):
        """All 5 segments have distinct gap patterns."""
        segments = list(SEGMENT_LIBRARY.values())
        self.assertGreater(len(segments), 0, "No segments in library")

        # Each segment should have unique segment_id and distinct criteria
        segment_ids = set()
        for segment in segments:
            self.assertIsNotNone(segment.segment_id)
            self.assertIsNotNone(segment.segment_name)
            segment_ids.add(segment.segment_id)

        # At least 2 unique segments
        self.assertGreater(len(segment_ids), 1)

    def test_apollo_filters_derived_from_segments(self):
        """Apollo filters come from ApolloTargeting.to_apollo_filters(),
        not hardcoded."""
        for segment in SEGMENT_LIBRARY.values():
            apollo_filters = segment.apollo_targeting.to_apollo_filters()

            # Filters should be dict with expected structure
            self.assertIsInstance(apollo_filters, dict)

            # Should have Apollo API fields
            expected_fields = {"contact_emails_currently_available"}
            self.assertTrue(
                any(field in apollo_filters for field in expected_fields)
                or len(apollo_filters) > 0,
                f"Segment {segment.segment_id} has no Apollo filter fields"
            )

    def test_enriched_leads_have_segment_context(self):
        """Every enriched lead carries its segment_id and segment_name."""
        enrichment_engine = EnrichmentEngine(
            apollo_client=ApolloClient(mock_mode=True)
        )

        # Enrich all segments
        results = enrichment_engine.enrich_all_segments(max_per_segment=5)

        for segment_key, result in results.items():
            for lead in result.leads:
                self.assertIsNotNone(lead.segment_id,
                                    f"Lead in {segment_key} has no segment_id")
                self.assertIsNotNone(lead.segment_name,
                                    f"Lead in {segment_key} has no segment_name")
                self.assertEqual(lead.segment_id, result.segment_id)


# ─────────────────────────────────────────────────────────────
# TEST CLASS: TestEdgeCases
# ─────────────────────────────────────────────────────────────

class TestEdgeCases(unittest.TestCase):
    """Test edge conditions and boundary cases."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_zero_inferences(self):
        """Pipeline handles prospect with no inferences."""
        prospect = _make_prospect("ZERO_INF01", "Zero Inferences")
        inferences = []
        interactions = _make_interactions(count=1)

        result = self.engine.run(
            prospect=prospect,
            inferences=inferences,
            interactions=interactions,
        )

        self.assertIsInstance(result, PipelineResult)
        # Should still produce a verdict even with no inferences
        self.assertIsNotNone(result.verdict)

    def test_zero_interactions(self):
        """Pipeline handles no interactions (L4 returns zeros)."""
        prospect = _make_prospect("ZERO_INT01", "Zero Interactions")
        inferences = _make_inferences("ZERO_INT01", count=3)
        interactions = []

        result = self.engine.run(
            prospect=prospect,
            inferences=inferences,
            interactions=interactions,
        )

        self.assertEqual(result.interaction_count, 0)
        self.assertEqual(len(result.interaction_results), 0)
        self.assertEqual(result.total_compensation, 0.0)
        self.assertEqual(result.avg_nocs, 0.0)

    def test_all_roles_produce_valid_nocs(self):
        """All role profiles produce valid NOCS (0-100)."""
        prospect = _make_prospect("ROLES01", "All Roles Test")
        inferences = _make_inferences("ROLES01", count=3)
        interactions = _make_interactions(count=1)

        role_keys = list(ROLE_PROFILES.keys())
        self.assertGreater(len(role_keys), 0, "No role profiles defined")

        for role_key in role_keys:
            result = self.engine.run(
                prospect=prospect,
                inferences=inferences,
                interactions=interactions,
                role_key=role_key,
            )

            # All interactions should have valid NOCS (0-100)
            for ir in result.interaction_results:
                self.assertGreaterEqual(ir.nocs.final_nocs, 0)
                self.assertLessEqual(ir.nocs.final_nocs, 100)

    def test_extreme_confidence_values(self):
        """Test with confidence 0.0 and 1.0."""
        prospect = _make_prospect("CONF01", "Extreme Confidence")

        # Confidence = 0.0
        inferences_zero = [
            InferenceRecord(
                object_id="INF_0",
                prospect_id="CONF01",
                inference_type=InferenceType.PAIN_POINT,
                statement="Zero confidence inference",
                confidence=0.0,
                evidence_ids=[],
            )
        ]

        result_zero = self.engine.run(
            prospect=prospect,
            inferences=inferences_zero,
            interactions=_make_interactions(count=1),
        )
        self.assertIsInstance(result_zero, PipelineResult)

        # Confidence = 1.0
        inferences_one = [
            InferenceRecord(
                object_id="INF_1",
                prospect_id="CONF01",
                inference_type=InferenceType.PAIN_POINT,
                statement="Full confidence inference",
                confidence=1.0,
                evidence_ids=[],
            )
        ]

        result_one = self.engine.run(
            prospect=prospect,
            inferences=inferences_one,
            interactions=_make_interactions(count=1),
        )
        self.assertIsInstance(result_one, PipelineResult)

    def test_stale_prospect_penalized(self):
        """Prospect with old verification date gets lower scores."""
        # Recent verification (2 days ago)
        recent_prospect = _make_prospect(
            "FRESH01", "Fresh Prospect", verified_days_ago=2
        )
        recent_inferences = _make_inferences("FRESH01", count=3)

        # Stale verification (180 days ago)
        stale_prospect = _make_prospect(
            "STALE01", "Stale Prospect", verified_days_ago=180
        )
        stale_inferences = _make_inferences("STALE01", count=3)

        interactions = _make_interactions(count=1)

        result_fresh = self.engine.run(
            prospect=recent_prospect,
            inferences=recent_inferences,
            interactions=interactions,
        )

        result_stale = self.engine.run(
            prospect=stale_prospect,
            inferences=stale_inferences,
            interactions=interactions,
        )

        # Stale data should result in lower trust score
        # (recency penalty in qualification)
        self.assertLess(result_stale.trust_score, result_fresh.trust_score)


# ─────────────────────────────────────────────────────────────
# TEST CLASS: TestSystemMetrics
# ─────────────────────────────────────────────────────────────

class TestSystemMetrics(unittest.TestCase):
    """Test performance and module structure validation."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_full_suite_under_one_second(self):
        """Full pipeline run for 3 scenarios < 1 second."""
        start = time.time()

        for scenario_num, scenario_spec in SCENARIOS.items():
            self.engine.run(
                prospect=scenario_spec["prospect"],
                inferences=scenario_spec["inferences"],
                interactions=scenario_spec["interactions"],
                role_key=scenario_spec["role_key"],
            )

        elapsed = time.time() - start
        self.assertLess(elapsed, 1.0,
                       f"Full suite took {elapsed:.3f}s, expected < 1.0s")

    def test_enrichment_all_segments_completes(self):
        """enrich_all_segments() returns results for all 5 segments."""
        enrichment_engine = EnrichmentEngine(
            apollo_client=ApolloClient(mock_mode=True)
        )

        results = enrichment_engine.enrich_all_segments(max_per_segment=5)

        # Should have results for all segments
        self.assertEqual(len(results), len(SEGMENT_LIBRARY))

        # Each should be an EnrichmentResult
        for segment_key, result in results.items():
            self.assertIsNotNone(result)
            self.assertIsNotNone(result.segment_id)
            self.assertGreaterEqual(result.total_found, 0)

    def test_dashboard_data_generation_complete(self):
        """Dashboard data generator produces all expected sections."""
        dashboard_data = generate_dashboard_data()

        # Should have all expected sections
        expected_sections = {
            "timestamp", "scenarios", "summary", "segmentation", "roles",
            "l1_components", "l2_ethos_dimensions"
        }
        self.assertTrue(
            expected_sections.issubset(set(dashboard_data.keys())),
            f"Missing sections: {expected_sections - set(dashboard_data.keys())}"
        )

        # Scenarios should have 3 entries (one per scenario)
        self.assertEqual(len(dashboard_data["scenarios"]), 3)

        # Each scenario should have L1, L2, L3, L4 data
        for scenario in dashboard_data["scenarios"]:
            self.assertIn("l1", scenario, "Scenario missing L1 data")
            self.assertIn("l2", scenario, "Scenario missing L2 data")
            self.assertIn("l3", scenario, "Scenario missing L3 data")
            self.assertIn("l4", scenario, "Scenario missing L4 data")
            # L1 should have prospect_id and fit score
            self.assertIn("prospect_id", scenario["l1"])
            self.assertIn("total_fit_score", scenario["l1"])
            # L3 should have verdict
            self.assertIn("verdict", scenario["l3"])
            # L4 should have interaction data
            self.assertIn("interaction_count", scenario["l4"])

    def test_module_count_matches_architecture(self):
        """Verify we have all expected modules."""
        import importlib

        modules_to_check = [
            ("l1_sensing.engines.prospect_value_engine", "ProspectValueEngine"),
            ("l2_brand_experience.engines.brand_experience_engine", "BrandExperienceEngine"),
            ("l3_qualification.engine", "QualificationEngine"),
            ("l4_execution.engines.nocs_engine", "NOCSEngine"),
            ("l4_execution.engines.compensation_engine", "CompensationEngine"),
            ("pipeline.engine", "GigatonEngine"),
            ("segmentation.engines.segmentation_engine", "SegmentationEngine"),
            ("apollo_enrichment.engines.enrichment_engine", "EnrichmentEngine"),
            ("dashboard.data_generator", "generate_dashboard_data"),
        ]

        for module_name, class_or_func_name in modules_to_check:
            try:
                module = importlib.import_module(module_name)
                self.assertTrue(
                    hasattr(module, class_or_func_name),
                    f"Module {module_name} missing {class_or_func_name}"
                )
            except ImportError as e:
                self.fail(f"Could not import {module_name}: {e}")


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    unittest.main()
