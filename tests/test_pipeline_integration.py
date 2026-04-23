"""
Integration tests for the full L1→L3→L4 Gigaton Engine pipeline.

Tests verify:
  1. L1→L3 bridge produces valid decisions
  2. Full pipeline produces complete PipelineResults
  3. Verdict correctness for known scenarios
  4. Score bounds and invariants
  5. Edge cases (no interactions, no inferences, etc.)
"""
import sys
import os
import unittest
from datetime import datetime, timedelta

# Ensure project root is on path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from l1_sensing.models.prospect import (
    ProspectProfile, CapabilitySummary, MaturityLevel, GTMMotion, PricingVisibility,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l1_sensing.engines.prospect_value_engine import ProspectValueEngine
from l4_execution.models.interaction import InteractionEvent
from pipeline.engine import GigatonEngine, PipelineResult


def _iso(days_ago: int = 0) -> str:
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


def _make_prospect(
    pid="TEST01",
    name="Test Corp",
    domain="test.com",
    verified_days_ago=2,
    evidence_count=5,
    **cap_overrides,
) -> ProspectProfile:
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


def _make_inferences(pid="TEST01", confidence=0.85, count=3) -> list:
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


def _make_interactions(count=2, converted=True, fast=True) -> list:
    return [
        InteractionEvent(
            interaction_id=f"INT_{i}",
            entity_id="actor_01",
            channel="email" if i % 2 == 0 else "voice",
            timestamp=_iso(i),
            status="resolved",
            response_time_seconds=120 if fast else 3600,
            resolution_time_seconds=1800 if fast else 86400,
            converted=converted,
            sentiment_score=0.8 if converted else 0.4,
            trust_shift_score=0.3 if converted else -0.1,
        )
        for i in range(count)
    ]


class TestL1ToL3Bridge(unittest.TestCase):
    """Test L1 sensing → L3 qualification bridge."""

    def test_bridge_produces_required_keys(self):
        prospect = _make_prospect()
        inferences = _make_inferences()
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)
        bridge = ProspectValueEngine.prospect_to_decision("TEST01", assessment, prospect)

        required = {"decision_id", "description", "reversibility", "blast_radius",
                     "financial_exposure", "strategic_impact", "source_reliability",
                     "data_completeness", "corroboration", "recency", "ethical_alignment"}
        self.assertTrue(required.issubset(set(bridge.keys())))

    def test_bridge_values_in_bounds(self):
        prospect = _make_prospect()
        inferences = _make_inferences()
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)
        bridge = ProspectValueEngine.prospect_to_decision("TEST01", assessment, prospect)

        for key in ["reversibility", "blast_radius", "source_reliability",
                     "data_completeness", "corroboration", "recency", "ethical_alignment"]:
            self.assertGreaterEqual(bridge[key], 0, f"{key} below 0")
            self.assertLessEqual(bridge[key], 1.0, f"{key} above 1")

    def test_bridge_decision_id_format(self):
        prospect = _make_prospect()
        inferences = _make_inferences()
        assessment = ProspectValueEngine.score_prospect(prospect, inferences)
        bridge = ProspectValueEngine.prospect_to_decision("TEST01", assessment, prospect)
        self.assertTrue(bridge["decision_id"].startswith("prospect_"))


class TestFullPipeline(unittest.TestCase):
    """Test complete L1→L3→L4 pipeline."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_full_pipeline_returns_pipeline_result(self):
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
        )
        self.assertIsInstance(result, PipelineResult)

    def test_pipeline_populates_all_sections(self):
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
        )
        # L1
        self.assertIsNotNone(result.prospect_assessment)
        self.assertGreater(result.prospect_assessment.total, 0)
        # L3
        self.assertIsNotNone(result.verdict)
        self.assertGreater(result.value_score, 0)
        self.assertGreater(result.trust_score, 0)
        # L4
        self.assertGreater(result.interaction_count, 0)
        self.assertGreater(result.avg_nocs, 0)

    def test_high_confidence_prospect_auto_executes(self):
        """High-confidence prospect with strong signals, recent verification,
        and full evidence chain → value ≤ 6.0, trust ≥ 7.5, full RTQL →
        all certificates issue → auto_execute."""
        result = self.engine.run(
            prospect=_make_prospect(evidence_count=5, verified_days_ago=1),
            inferences=_make_inferences(confidence=0.90, count=3),
            interactions=_make_interactions(count=2, converted=True, fast=True),
        )
        self.assertEqual(result.verdict, "auto_execute")
        self.assertTrue(result.certificates["EC"])

    def test_weak_signal_needs_data(self):
        """Low confidence inferences → low data completeness → needs_data."""
        prospect = ProspectProfile(
            prospect_id="WEAK01",
            domain="mystery.io",
            official_name="Mystery Corp",
            industries=[],
            buyer_personas=[],
            service_geographies=[],
            last_verified_at="",
            evidence_ids=[],
        )
        inferences = _make_inferences(pid="WEAK01", confidence=0.25, count=1)
        interactions = _make_interactions(count=1, converted=False, fast=False)

        result = self.engine.run(
            prospect=prospect,
            inferences=inferences,
            interactions=interactions,
        )
        self.assertEqual(result.verdict, "needs_data")

    def test_zero_interactions_produces_empty_l4(self):
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=[],
        )
        self.assertEqual(result.interaction_count, 0)
        self.assertEqual(len(result.interaction_results), 0)
        self.assertEqual(result.total_compensation, 0.0)

    def test_multiple_interactions_aggregate(self):
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(count=5),
        )
        self.assertEqual(result.interaction_count, 5)
        self.assertEqual(len(result.interaction_results), 5)
        self.assertGreater(result.total_compensation, 0)

    def test_summary_dict_structure(self):
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
        )
        summary = result.summary()
        self.assertIn("prospect", summary)
        self.assertIn("qualification", summary)
        self.assertIn("execution", summary)
        self.assertIn("verdict", summary["qualification"])

    def test_different_roles_produce_different_nocs(self):
        prospect = _make_prospect()
        inferences = _make_inferences()
        interactions = _make_interactions()

        result_sales = self.engine.run(
            prospect=prospect, inferences=inferences,
            interactions=interactions, role_key="sales_operator",
        )
        result_ops = self.engine.run(
            prospect=prospect, inferences=inferences,
            interactions=interactions, role_key="operations_manager",
        )
        # Different role weights should produce different NOCS
        self.assertNotAlmostEqual(result_sales.avg_nocs, result_ops.avg_nocs, places=1)

    def test_strategic_multiplier_affects_compensation(self):
        prospect = _make_prospect()
        inferences = _make_inferences()
        interactions = _make_interactions()

        result_1x = self.engine.run(
            prospect=prospect, inferences=inferences,
            interactions=interactions, strategic_multiplier=1.0,
        )
        result_2x = self.engine.run(
            prospect=prospect, inferences=inferences,
            interactions=interactions, strategic_multiplier=2.0,
        )
        self.assertGreater(result_2x.total_compensation, result_1x.total_compensation)

    def test_certificates_populated(self):
        result = self.engine.run(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
            interactions=_make_interactions(),
        )
        certs = result.certificates
        self.assertIn("QC", certs)
        self.assertIn("VC", certs)
        self.assertIn("TC", certs)
        self.assertIn("EC", certs)

    def test_pipeline_deterministic(self):
        prospect = _make_prospect()
        inferences = _make_inferences()
        interactions = _make_interactions()

        r1 = self.engine.run(prospect=prospect, inferences=inferences, interactions=interactions)
        r2 = self.engine.run(prospect=prospect, inferences=inferences, interactions=interactions)

        self.assertEqual(r1.verdict, r2.verdict)
        self.assertAlmostEqual(r1.value_score, r2.value_score, places=5)
        self.assertAlmostEqual(r1.trust_score, r2.trust_score, places=5)


class TestL1Only(unittest.TestCase):
    """Test L1-only mode."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_l1_only_returns_assessment(self):
        from l1_sensing.models.value_assessment import ProspectValueAssessment
        result = self.engine.run_l1_only(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
        )
        self.assertIsInstance(result, ProspectValueAssessment)

    def test_l1_only_bounded(self):
        result = self.engine.run_l1_only(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
        )
        self.assertGreaterEqual(result.total, 0)
        self.assertLessEqual(result.total, 100)


class TestL1L3Mode(unittest.TestCase):
    """Test L1→L3 mode (no L4)."""

    def setUp(self):
        self.engine = GigatonEngine()

    def test_l1_l3_returns_dict_with_both(self):
        result = self.engine.run_l1_l3(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
        )
        self.assertIn("assessment", result)
        self.assertIn("decision", result)

    def test_l1_l3_decision_has_verdict(self):
        result = self.engine.run_l1_l3(
            prospect=_make_prospect(),
            inferences=_make_inferences(),
        )
        self.assertIsNotNone(result["decision"].verdict)


if __name__ == "__main__":
    unittest.main()
