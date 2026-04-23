"""Unit tests for Interaction Scorer."""

import unittest

from l4_execution.engines.interaction_scorer import InteractionScorer
from l4_execution.models.interaction import InteractionEvent


class TestInteractionScorer(unittest.TestCase):
    """Tests for InteractionScorer."""

    def test_fast_response_high_time_leverage(self):
        """Fast response times should yield high time_leverage scores."""
        interaction = InteractionEvent(
            interaction_id="int_1",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=100.0,  # Very fast
            resolution_time_seconds=500.0,
            converted=True,
        )
        benchmark = InteractionScorer.score(interaction)

        self.assertGreater(benchmark.time_leverage, 70.0)

    def test_slow_response_low_time_leverage(self):
        """Slow response times should yield low time_leverage scores."""
        interaction = InteractionEvent(
            interaction_id="int_2",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=7200.0,  # 2 hours
            resolution_time_seconds=86400.0,  # 1 day
            converted=False,
        )
        benchmark = InteractionScorer.score(interaction)

        self.assertLess(benchmark.time_leverage, 30.0)

    def test_converted_interaction_high_quality(self):
        """Converted interactions should have high output_quality."""
        interaction = InteractionEvent(
            interaction_id="int_3",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            converted=True,
            abandoned=False,
            escalated=False,
        )
        benchmark = InteractionScorer.score(interaction)

        self.assertGreater(benchmark.output_quality, 70.0)

    def test_abandoned_interaction_low_quality(self):
        """Abandoned interactions should have lower output_quality."""
        interaction = InteractionEvent(
            interaction_id="int_4",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="abandoned",
            response_time_seconds=300.0,
            resolution_time_seconds=3600.0,
            converted=False,
            abandoned=True,
            escalated=False,
        )
        benchmark = InteractionScorer.score(interaction)

        self.assertLess(benchmark.output_quality, 50.0)

    def test_escalated_interaction_scored(self):
        """Escalated interactions should be appropriately penalized."""
        interaction = InteractionEvent(
            interaction_id="int_5",
            entity_id="entity_1",
            channel="voice",
            timestamp="2026-04-21T00:00:00Z",
            status="escalated",
            response_time_seconds=600.0,
            resolution_time_seconds=7200.0,
            converted=False,
            abandoned=False,
            escalated=True,
        )
        benchmark = InteractionScorer.score(interaction)

        # Should be penalized
        self.assertLess(benchmark.output_quality, 60.0)
        self.assertLess(benchmark.risk_reduction, 50.0)
        self.assertLess(benchmark.ethos_alignment, 70.0)

    def test_positive_sentiment_boosts_relational(self):
        """Positive sentiment should boost relational_capital."""
        interaction_positive = InteractionEvent(
            interaction_id="int_6a",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            sentiment_score=0.9,  # Very positive
            trust_shift_score=0.5,
        )
        interaction_neutral = InteractionEvent(
            interaction_id="int_6b",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            sentiment_score=0.5,  # Neutral
            trust_shift_score=0.0,
        )

        benchmark_positive = InteractionScorer.score(interaction_positive)
        benchmark_neutral = InteractionScorer.score(interaction_neutral)

        self.assertGreater(benchmark_positive.relational_capital, benchmark_neutral.relational_capital)

    def test_negative_trust_shift_penalizes(self):
        """Negative trust shift should lower relational_capital."""
        interaction_positive_trust = InteractionEvent(
            interaction_id="int_7a",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            sentiment_score=0.5,
            trust_shift_score=0.8,  # High trust increase
        )
        interaction_negative_trust = InteractionEvent(
            interaction_id="int_7b",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            sentiment_score=0.5,
            trust_shift_score=-0.8,  # High trust decrease
        )

        benchmark_positive = InteractionScorer.score(interaction_positive_trust)
        benchmark_negative = InteractionScorer.score(interaction_negative_trust)

        self.assertGreater(benchmark_positive.relational_capital, benchmark_negative.relational_capital)

    def test_all_dimensions_populated(self):
        """All 12 benchmark dimensions should be populated."""
        interaction = InteractionEvent(
            interaction_id="int_8",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            converted=True,
        )
        benchmark = InteractionScorer.score(interaction)

        expected_dimensions = {
            "time_leverage",
            "effort_intensity",
            "output_quality",
            "uniqueness",
            "relational_capital",
            "risk_reduction",
            "probability_lift",
            "multiplicative_effect",
            "brand_adherence",
            "interaction_effectiveness",
            "economic_productivity",
            "ethos_alignment",
        }
        benchmark_dims = benchmark.get_all_dimensions()
        self.assertEqual(set(benchmark_dims.keys()), expected_dimensions)

    def test_scores_bounded_0_to_100(self):
        """All dimension scores should be bounded 0-100."""
        interaction = InteractionEvent(
            interaction_id="int_9",
            entity_id="entity_1",
            channel="email",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=100.0,
            resolution_time_seconds=500.0,
            converted=True,
            abandoned=False,
            escalated=False,
            sentiment_score=0.95,
            trust_shift_score=0.95,
        )
        benchmark = InteractionScorer.score(interaction)

        dims = benchmark.get_all_dimensions()
        for dimension, score in dims.items():
            self.assertGreaterEqual(score, 0.0, f"{dimension} below 0")
            self.assertLessEqual(score, 100.0, f"{dimension} above 100")

    def test_default_channel_accepted(self):
        """Scorer should handle various channel types."""
        channels = ["voice", "sms", "whatsapp", "web", "email", "in_person"]

        for channel in channels:
            interaction = InteractionEvent(
                interaction_id=f"int_{channel}",
                entity_id="entity_1",
                channel=channel,
                timestamp="2026-04-21T00:00:00Z",
                status="resolved",
                response_time_seconds=300.0,
                resolution_time_seconds=1800.0,
                converted=True,
            )
            benchmark = InteractionScorer.score(interaction)

            # Verify basic structure
            self.assertEqual(benchmark.action_type, f"interaction_{channel}")
            self.assertIn(interaction.interaction_id, benchmark.attribution_links)

    def test_attribution_links_preserved(self):
        """Attribution links should include the interaction ID."""
        interaction = InteractionEvent(
            interaction_id="int_special_123",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
        )
        benchmark = InteractionScorer.score(interaction)

        self.assertIn("int_special_123", benchmark.attribution_links)

    def test_confidence_reflects_data_completeness(self):
        """Confidence should be higher with complete data."""
        interaction_complete = InteractionEvent(
            interaction_id="int_10a",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            response_time_seconds=300.0,
            resolution_time_seconds=1800.0,
            converted=True,
            sentiment_score=0.7,
            trust_shift_score=0.3,
        )
        interaction_sparse = InteractionEvent(
            interaction_id="int_10b",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="open",
            response_time_seconds=None,
            resolution_time_seconds=None,
            converted=False,
        )

        benchmark_complete = InteractionScorer.score(interaction_complete)
        benchmark_sparse = InteractionScorer.score(interaction_sparse)

        self.assertGreater(benchmark_complete.confidence, benchmark_sparse.confidence)

    def test_actor_id_default_to_entity_id(self):
        """If no actor_id provided, should default to entity_id."""
        interaction = InteractionEvent(
            interaction_id="int_11",
            entity_id="entity_specific_456",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
        )
        benchmark = InteractionScorer.score(interaction)

        self.assertEqual(benchmark.actor_id, "entity_specific_456")

    def test_actor_id_override(self):
        """Actor ID should be overridable."""
        interaction = InteractionEvent(
            interaction_id="int_12",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
        )
        benchmark = InteractionScorer.score(interaction, actor_id="actor_override")

        self.assertEqual(benchmark.actor_id, "actor_override")

    def test_web_email_higher_brand_adherence(self):
        """Web and email channels should have higher brand_adherence."""
        interaction_web = InteractionEvent(
            interaction_id="int_13a",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
        )
        interaction_voice = InteractionEvent(
            interaction_id="int_13b",
            entity_id="entity_1",
            channel="voice",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
        )

        benchmark_web = InteractionScorer.score(interaction_web)
        benchmark_voice = InteractionScorer.score(interaction_voice)

        self.assertGreater(benchmark_web.brand_adherence, benchmark_voice.brand_adherence)

    def test_converted_interaction_high_probability_lift(self):
        """Converted interactions should have high probability_lift."""
        interaction_converted = InteractionEvent(
            interaction_id="int_14a",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            converted=True,
        )
        interaction_not_converted = InteractionEvent(
            interaction_id="int_14b",
            entity_id="entity_1",
            channel="web",
            timestamp="2026-04-21T00:00:00Z",
            status="resolved",
            converted=False,
        )

        benchmark_converted = InteractionScorer.score(interaction_converted)
        benchmark_not_converted = InteractionScorer.score(interaction_not_converted)

        self.assertGreater(benchmark_converted.probability_lift, benchmark_not_converted.probability_lift)


if __name__ == "__main__":
    unittest.main()
