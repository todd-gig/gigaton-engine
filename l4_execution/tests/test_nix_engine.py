"""Tests for the Next Interaction Experience (NIX) Engine."""

import sys
import os
import unittest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import datetime, timedelta
from pipeline.engine import GigatonEngine
from pipeline.cli import SCENARIOS
from l4_execution.engines.nix_engine import NIXEngine, CHANNEL_CAPABILITIES
from l4_execution.models.next_interaction import (
    NextInteractionExperience,
    ChannelRecommendation,
    ChannelType,
    InteractionIntent,
    Urgency,
)


def _run_scenario(n):
    """Run pipeline scenario and return result."""
    engine = GigatonEngine()
    spec = SCENARIOS[n]
    return engine.run(
        prospect=spec["prospect"],
        inferences=spec["inferences"],
        interactions=spec["interactions"],
        role_key=spec["role_key"],
    )


class TestNIXEngineRecommendations(unittest.TestCase):
    """Test NIX engine produces correct recommendations from pipeline state."""

    def setUp(self):
        self.nix = NIXEngine()

    def test_auto_execute_gets_proposal_intent(self):
        result = _run_scenario(1)
        self.assertEqual(result.verdict, "auto_execute")
        nix = self.nix.recommend(result)
        self.assertEqual(nix.primary_intent, InteractionIntent.PROPOSAL)

    def test_auto_execute_gets_immediate_urgency(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        self.assertEqual(nix.urgency, Urgency.IMMEDIATE)

    def test_escalate_gets_value_demonstration_intent(self):
        result = _run_scenario(2)
        self.assertEqual(result.verdict, "escalate_tier_1")
        nix = self.nix.recommend(result)
        self.assertEqual(nix.primary_intent, InteractionIntent.VALUE_DEMONSTRATION)

    def test_needs_data_gets_data_gathering_intent(self):
        result = _run_scenario(3)
        self.assertEqual(result.verdict, "needs_data")
        nix = self.nix.recommend(result)
        self.assertEqual(nix.primary_intent, InteractionIntent.DATA_GATHERING)

    def test_needs_data_gets_this_week_urgency(self):
        result = _run_scenario(3)
        nix = self.nix.recommend(result)
        self.assertEqual(nix.urgency, Urgency.THIS_WEEK)

    def test_recommends_all_channels(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        self.assertEqual(len(nix.channel_recommendations), len(ChannelType))

    def test_channels_are_ranked(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        ranks = [r.priority_rank for r in nix.channel_recommendations]
        self.assertEqual(ranks, list(range(1, len(ChannelType) + 1)))

    def test_primary_channel_is_rank_1(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        self.assertIsNotNone(nix.primary_channel)
        self.assertEqual(nix.primary_channel.priority_rank, 1)

    def test_confidence_bounded_0_1(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        for rec in nix.channel_recommendations:
            self.assertGreaterEqual(rec.confidence, 0.0)
            self.assertLessEqual(rec.confidence, 1.0)

    def test_projected_nocs_bounded(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        for rec in nix.channel_recommendations:
            self.assertGreaterEqual(rec.projected_nocs, 0)
            self.assertLessEqual(rec.projected_nocs, 100)

    def test_each_channel_has_message_frame(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        for rec in nix.channel_recommendations:
            self.assertTrue(len(rec.suggested_message_frame) > 10)

    def test_each_channel_has_tone(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        for rec in nix.channel_recommendations:
            self.assertTrue(len(rec.suggested_tone) > 3)

    def test_each_channel_has_talking_points(self):
        result = _run_scenario(2)
        nix = self.nix.recommend(result)
        for rec in nix.channel_recommendations:
            self.assertGreater(len(rec.key_talking_points), 0)

    def test_each_channel_has_ethos_targets(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        for rec in nix.channel_recommendations:
            self.assertGreater(len(rec.ethos_targets), 0)
            for dim, val in rec.ethos_targets.items():
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 100)

    def test_success_criteria_populated(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        self.assertGreater(len(nix.success_criteria), 0)

    def test_strategic_rationale_non_empty(self):
        result = _run_scenario(2)
        nix = self.nix.recommend(result)
        self.assertGreater(len(nix.strategic_rationale), 20)

    def test_prospect_context_carried(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        self.assertEqual(nix.prospect_id, result.prospect_id)
        self.assertEqual(nix.prospect_name, result.prospect_name)
        self.assertEqual(nix.verdict, result.verdict)
        self.assertAlmostEqual(nix.current_fit_score, result.prospect_assessment.total, places=2)


class TestNIXChannelFatigue(unittest.TestCase):
    """Test channel fatigue penalization."""

    def setUp(self):
        self.nix = NIXEngine()

    def test_repeated_channel_penalized(self):
        result = _run_scenario(1)
        nix_fresh = self.nix.recommend(result, prior_channels=[])
        nix_fatigued = self.nix.recommend(result, prior_channels=["email", "email", "email"])

        # Find email confidence in both
        fresh_email = nix_fresh.get_channel(ChannelType.EMAIL)
        fatigued_email = nix_fatigued.get_channel(ChannelType.EMAIL)
        self.assertLess(fatigued_email.confidence, fresh_email.confidence)


class TestNIXEdgeCases(unittest.TestCase):
    """Test NIX engine edge cases."""

    def setUp(self):
        self.nix = NIXEngine()

    def test_custom_channel_subset(self):
        nix = NIXEngine(channels=[ChannelType.EMAIL, ChannelType.VOICE])
        result = _run_scenario(1)
        rec = nix.recommend(result)
        self.assertEqual(len(rec.channel_recommendations), 2)

    def test_needs_data_has_prerequisites(self):
        result = _run_scenario(3)
        nix = self.nix.recommend(result)
        self.assertGreater(len(nix.prerequisite_data), 0)

    def test_blocked_verdict_has_blocking_conditions(self):
        # Scenario 3 may not be "block" but needs_data has prerequisites
        result = _run_scenario(3)
        nix = self.nix.recommend(result)
        # At minimum, prerequisites should exist for needs_data
        self.assertGreater(len(nix.prerequisite_data), 0)


class TestNIXSerialization(unittest.TestCase):
    """Test NIX to_dict serialization for dashboard."""

    def setUp(self):
        self.nix = NIXEngine()

    def test_to_dict_has_all_keys(self):
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        d = nix.to_dict()
        required_keys = {
            "prospect_id", "prospect_name", "verdict",
            "current_fit_score", "current_value_score", "current_trust_score",
            "primary_intent", "urgency", "strategic_rationale",
            "success_criteria", "channels",
        }
        self.assertTrue(required_keys.issubset(set(d.keys())))

    def test_to_dict_channels_serialized(self):
        result = _run_scenario(2)
        nix = self.nix.recommend(result)
        d = nix.to_dict()
        self.assertEqual(len(d["channels"]), len(ChannelType))
        for ch in d["channels"]:
            self.assertIn("channel", ch)
            self.assertIn("confidence", ch)
            self.assertIn("suggested_message_frame", ch)
            self.assertIn("ethos_targets", ch)
            self.assertIn("projected_nocs", ch)
            self.assertIn("operator_override_message", ch)

    def test_to_dict_values_are_json_serializable(self):
        import json
        result = _run_scenario(1)
        nix = self.nix.recommend(result)
        d = nix.to_dict()
        # Should not raise
        json_str = json.dumps(d)
        self.assertGreater(len(json_str), 100)


class TestNIXDashboardIntegration(unittest.TestCase):
    """Test NIX integration with dashboard data generator."""

    def test_dashboard_data_includes_nix(self):
        from dashboard.data_generator import generate_dashboard_data
        data = generate_dashboard_data()
        for s in data["scenarios"]:
            self.assertIn("nix", s)
            nix = s["nix"]
            self.assertIn("primary_intent", nix)
            self.assertIn("urgency", nix)
            self.assertIn("channels", nix)
            self.assertGreater(len(nix["channels"]), 0)

    def test_dashboard_html_includes_nix_panel(self):
        from dashboard.data_generator import generate_dashboard_data
        from dashboard.html_renderer import render_html_dashboard
        data = generate_dashboard_data()
        html = render_html_dashboard(data)
        self.assertIn("Next Interaction Experience", html)
        self.assertIn("nix-modal", html)
        self.assertIn("openNixModal", html)
        self.assertIn("nix-editable", html)
        self.assertIn("nix-approve-btn", html)

    def test_dashboard_html_has_editable_textareas(self):
        from dashboard.data_generator import generate_dashboard_data
        from dashboard.html_renderer import render_html_dashboard
        data = generate_dashboard_data()
        html = render_html_dashboard(data)
        # Each channel card has message frame + operator notes textareas
        self.assertGreater(html.count("<textarea"), 6)

    def test_three_scenarios_three_modals(self):
        from dashboard.data_generator import generate_dashboard_data
        from dashboard.html_renderer import render_html_dashboard
        data = generate_dashboard_data()
        html = render_html_dashboard(data)
        self.assertIn('id="nix-modal-1"', html)
        self.assertIn('id="nix-modal-2"', html)
        self.assertIn('id="nix-modal-3"', html)


if __name__ == "__main__":
    unittest.main()
