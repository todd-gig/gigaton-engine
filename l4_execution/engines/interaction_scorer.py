"""Interaction scorer that converts InteractionEvent to ActionBenchmark."""

import uuid
from datetime import datetime

from l4_execution.models.action_benchmark import ActionBenchmark
from l4_execution.models.interaction import InteractionEvent


class InteractionScorer:
    """Converts InteractionEvents into ActionBenchmarks with scored dimensions."""

    @staticmethod
    def score(interaction: InteractionEvent, actor_id: str = None) -> ActionBenchmark:
        """
        Convert an InteractionEvent to an ActionBenchmark with scored dimensions.

        Scoring heuristics:
            - time_leverage: Inverse of response_time (faster = higher)
            - effort_intensity: Inverse of resolution_time (faster = higher, capped)
            - output_quality: Based on converted, not abandoned, not escalated
            - relational_capital: Based on sentiment_score and trust_shift
            - interaction_effectiveness: Composite of conversion, response speed, resolution
            - brand_adherence: Default 70 unless overridden
            - Other dimensions: Reasonable defaults

        Args:
            interaction: InteractionEvent to score
            actor_id: Actor ID for benchmark (defaults to interaction.entity_id)

        Returns:
            ActionBenchmark with all 12 dimensions scored
        """
        if actor_id is None:
            actor_id = interaction.entity_id

        # Time leverage: scale from response_time_seconds
        # Assume ideal response is < 5 minutes (300 seconds)
        if interaction.response_time_seconds is not None:
            # Fast response (300s) -> 90, Medium (1800s) -> 50, Slow (3600s) -> 10
            time_leverage = max(10.0, min(90.0, 100.0 - (interaction.response_time_seconds / 40.0)))
        else:
            time_leverage = 50.0

        # Effort intensity: inverse of resolution_time
        # Assume ideal resolution is < 1 hour (3600 seconds)
        if interaction.resolution_time_seconds is not None:
            # Fast resolution (3600s) -> 85, Medium (86400s) -> 50, Slow (172800s) -> 20
            effort_intensity = max(10.0, min(90.0, 100.0 - (interaction.resolution_time_seconds / 2000.0)))
        else:
            effort_intensity = 50.0

        # Output quality: based on conversion, abandonment, escalation
        quality_score = 50.0
        if interaction.converted:
            quality_score += 30.0
        if interaction.abandoned:
            quality_score -= 25.0
        if interaction.escalated:
            quality_score -= 15.0
        output_quality = max(0.0, min(100.0, quality_score))

        # Uniqueness: default to moderate (interaction is a common action)
        uniqueness = 45.0

        # Relational capital: based on sentiment and trust shift
        relational_base = 50.0
        # Sentiment score (0-1) -> +/-25 points
        relational_base += (interaction.sentiment_score - 0.5) * 50.0
        # Trust shift (-1 to +1) -> +/-25 points
        relational_base += interaction.trust_shift_score * 25.0
        relational_capital = max(0.0, min(100.0, relational_base))

        # Risk reduction: higher if no escalation
        risk_base = 60.0 if not interaction.escalated else 30.0
        risk_reduction = max(0.0, min(100.0, risk_base))

        # Probability lift: interaction contributed to conversion
        probability_lift = 85.0 if interaction.converted else 40.0

        # Multiplicative effect: interaction-by-interaction may have low direct effect
        multiplicative_effect = 35.0

        # Brand adherence: default unless overridden by channel
        # Email/web interactions are more controlled, voice/sms less so
        brand_adherence = 70.0
        if interaction.channel in ["email", "web"]:
            brand_adherence = 75.0
        elif interaction.channel in ["voice", "sms"]:
            brand_adherence = 65.0

        # Interaction effectiveness: composite of conversion, time, resolution
        effectiveness_base = 50.0
        if interaction.converted:
            effectiveness_base += 25.0
        if interaction.response_time_seconds is not None and interaction.response_time_seconds < 300:
            effectiveness_base += 15.0
        if interaction.resolution_time_seconds is not None and interaction.resolution_time_seconds < 3600:
            effectiveness_base += 10.0
        interaction_effectiveness = max(0.0, min(100.0, effectiveness_base))

        # Economic productivity: tied to conversion and time efficiency
        econ_base = 50.0
        if interaction.converted:
            econ_base += 30.0
        if interaction.response_time_seconds is not None and interaction.response_time_seconds < 600:
            econ_base += 10.0
        economic_productivity = max(0.0, min(100.0, econ_base))

        # Ethos alignment: high by default (interactions follow brand protocol)
        ethos_alignment = 75.0
        if interaction.status == "abandoned":
            ethos_alignment -= 20.0
        if interaction.escalated:
            ethos_alignment -= 10.0
        ethos_alignment = max(0.0, min(100.0, ethos_alignment))

        # Determine confidence based on interaction completeness
        confidence = 0.6  # Base confidence
        if interaction.response_time_seconds is not None:
            confidence += 0.15
        if interaction.resolution_time_seconds is not None:
            confidence += 0.15
        if interaction.status == "resolved":
            confidence += 0.1
        confidence = min(1.0, confidence)

        action_id = f"action_{uuid.uuid4().hex[:12]}"

        return ActionBenchmark(
            action_id=action_id,
            actor_id=actor_id,
            timestamp=interaction.timestamp,
            action_type=f"interaction_{interaction.channel}",
            time_leverage=time_leverage,
            effort_intensity=effort_intensity,
            output_quality=output_quality,
            uniqueness=uniqueness,
            relational_capital=relational_capital,
            risk_reduction=risk_reduction,
            probability_lift=probability_lift,
            multiplicative_effect=multiplicative_effect,
            brand_adherence=brand_adherence,
            interaction_effectiveness=interaction_effectiveness,
            economic_productivity=economic_productivity,
            ethos_alignment=ethos_alignment,
            confidence=confidence,
            attribution_links=[interaction.interaction_id],
            notes=f"Scored from {interaction.channel} interaction {interaction.interaction_id}",
        )
