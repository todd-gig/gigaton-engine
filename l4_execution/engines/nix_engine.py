"""
Next Interaction Experience (NIX) Engine.

Analyzes the full L1→L3→L4 pipeline state to recommend the optimal
next interaction across ALL channels. Recommendations are causally
derived from:

  1. L3 verdict → determines primary intent and urgency
  2. L1 assessment → identifies gaps to address
  3. L4 interaction history → avoids channel fatigue, builds on momentum
  4. L2 brand coherence → sets ethos targets per channel
  5. Segment context → aligns messaging to gap pattern

The engine produces ranked ChannelRecommendations with projected NOCS,
message framing, tone guidance, and risk factors — all editable by
the operator before execution.
"""

import sys
import os
from typing import List, Dict, Any, Optional

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from l4_execution.models.next_interaction import (
    NextInteractionExperience,
    ChannelRecommendation,
    ChannelType,
    InteractionIntent,
    Urgency,
)
from pipeline.engine import PipelineResult


# ─── Channel capability matrix ───────────────────────────────────────
# Maps channel → intrinsic strengths for scoring
CHANNEL_CAPABILITIES = {
    ChannelType.EMAIL: {
        "brand_adherence_base": 80,
        "scalability": 90,
        "personalization": 70,
        "trust_building": 50,
        "urgency_signal": 30,
        "data_gathering": 60,
        "relationship_depth": 40,
        "duration_minutes": 5,
    },
    ChannelType.VOICE: {
        "brand_adherence_base": 65,
        "scalability": 30,
        "personalization": 90,
        "trust_building": 85,
        "urgency_signal": 70,
        "data_gathering": 80,
        "relationship_depth": 85,
        "duration_minutes": 20,
    },
    ChannelType.VIDEO: {
        "brand_adherence_base": 70,
        "scalability": 40,
        "personalization": 85,
        "trust_building": 80,
        "urgency_signal": 60,
        "data_gathering": 75,
        "relationship_depth": 80,
        "duration_minutes": 30,
    },
    ChannelType.LINKEDIN: {
        "brand_adherence_base": 75,
        "scalability": 85,
        "personalization": 65,
        "trust_building": 55,
        "urgency_signal": 25,
        "data_gathering": 40,
        "relationship_depth": 50,
        "duration_minutes": 3,
    },
    ChannelType.SMS: {
        "brand_adherence_base": 55,
        "scalability": 95,
        "personalization": 50,
        "trust_building": 30,
        "urgency_signal": 90,
        "data_gathering": 20,
        "relationship_depth": 25,
        "duration_minutes": 1,
    },
    ChannelType.WEB: {
        "brand_adherence_base": 85,
        "scalability": 100,
        "personalization": 60,
        "trust_building": 45,
        "urgency_signal": 20,
        "data_gathering": 70,
        "relationship_depth": 30,
        "duration_minutes": 10,
    },
    ChannelType.WHATSAPP: {
        "brand_adherence_base": 60,
        "scalability": 80,
        "personalization": 70,
        "trust_building": 55,
        "urgency_signal": 80,
        "data_gathering": 45,
        "relationship_depth": 55,
        "duration_minutes": 5,
    },
    ChannelType.IN_PERSON: {
        "brand_adherence_base": 60,
        "scalability": 10,
        "personalization": 100,
        "trust_building": 95,
        "urgency_signal": 50,
        "data_gathering": 90,
        "relationship_depth": 100,
        "duration_minutes": 45,
    },
}


# ─── Verdict → Intent mapping ────────────────────────────────────────
VERDICT_INTENT_MAP = {
    "auto_execute": InteractionIntent.PROPOSAL,
    "escalate_tier_1": InteractionIntent.VALUE_DEMONSTRATION,
    "escalate_tier_2": InteractionIntent.TRUST_BUILDING,
    "needs_data": InteractionIntent.DATA_GATHERING,
    "block": InteractionIntent.REACTIVATION,
}

VERDICT_URGENCY_MAP = {
    "auto_execute": Urgency.IMMEDIATE,
    "escalate_tier_1": Urgency.NEXT_DAY,
    "escalate_tier_2": Urgency.THIS_WEEK,
    "needs_data": Urgency.THIS_WEEK,
    "block": Urgency.DEFERRED,
}


class NIXEngine:
    """
    Next Interaction Experience Engine.

    Consumes PipelineResult and produces NextInteractionExperience
    with ranked channel recommendations across all available channels.

    Usage:
        nix = NIXEngine()
        experience = nix.recommend(pipeline_result)
        # experience.channel_recommendations[0] = best channel
        # Each recommendation is editable before execution
    """

    def __init__(self, channels: List[ChannelType] = None):
        """Initialize with available channels.

        Args:
            channels: List of available channels. Defaults to all channels.
        """
        self.channels = channels or list(ChannelType)

    def recommend(
        self,
        result: PipelineResult,
        prior_channels: List[str] = None,
        brand_coherence_data: Dict[str, float] = None,
        segment_gap_pattern: str = "",
    ) -> NextInteractionExperience:
        """
        Generate next interaction recommendations from pipeline results.

        Causal chain:
          verdict → intent + urgency
          L1 gaps → talking points
          L4 history → channel fatigue avoidance
          L2 coherence → ethos targets
          Segment → message framing

        Args:
            result: PipelineResult from GigatonEngine.run()
            prior_channels: List of channels already used (to avoid fatigue)
            brand_coherence_data: Dict of ethos dimension → score (0-100)
            segment_gap_pattern: Primary gap pattern from segmentation

        Returns:
            NextInteractionExperience with ranked channel recommendations
        """
        prior_channels = prior_channels or []
        brand_coherence_data = brand_coherence_data or self._default_ethos_targets()

        # 1. Derive intent and urgency from verdict
        intent = VERDICT_INTENT_MAP.get(result.verdict, InteractionIntent.NURTURE)
        urgency = VERDICT_URGENCY_MAP.get(result.verdict, Urgency.THIS_WEEK)

        # 2. Build strategic rationale
        rationale = self._build_rationale(result, intent, segment_gap_pattern)

        # 3. Identify gaps and talking points from L1
        gaps = result.prospect_assessment.priority_gaps
        talking_points = self._derive_talking_points(result, gaps, segment_gap_pattern)

        # 4. Score and rank all channels
        channel_recs = []
        for channel in self.channels:
            rec = self._score_channel(
                channel=channel,
                result=result,
                intent=intent,
                prior_channels=prior_channels,
                brand_coherence=brand_coherence_data,
                talking_points=talking_points,
                segment_gap=segment_gap_pattern,
            )
            channel_recs.append(rec)

        # Sort by confidence descending, assign ranks
        channel_recs.sort(key=lambda r: r.confidence, reverse=True)
        for i, rec in enumerate(channel_recs):
            rec.priority_rank = i + 1

        # 5. Derive success criteria
        success_criteria = self._derive_success_criteria(result, intent)

        # 6. Identify blocking conditions
        blocking = self._derive_blocking_conditions(result)

        # 7. Identify prerequisite data
        prerequisites = self._derive_prerequisites(result)

        # 8. Set trust and sentiment targets
        target_trust_shift = self._target_trust_shift(result)
        target_sentiment = self._target_sentiment(result)

        return NextInteractionExperience(
            prospect_id=result.prospect_id,
            prospect_name=result.prospect_name,
            verdict=result.verdict,
            current_fit_score=result.prospect_assessment.total,
            current_value_score=result.value_score,
            current_trust_score=result.trust_score,
            primary_intent=intent,
            urgency=urgency,
            strategic_rationale=rationale,
            channel_recommendations=channel_recs,
            success_criteria=success_criteria,
            target_trust_shift=target_trust_shift,
            target_sentiment=target_sentiment,
            blocking_conditions=blocking,
            prerequisite_data=prerequisites,
        )

    # ─── Channel scoring ──────────────────────────────────────────

    def _score_channel(
        self,
        channel: ChannelType,
        result: PipelineResult,
        intent: InteractionIntent,
        prior_channels: List[str],
        brand_coherence: Dict[str, float],
        talking_points: List[str],
        segment_gap: str,
    ) -> ChannelRecommendation:
        """Score a single channel for this interaction context."""
        caps = CHANNEL_CAPABILITIES[channel]

        # Base score from intent alignment
        intent_score = self._intent_channel_alignment(intent, caps)

        # Fatigue penalty: if channel was recently used, reduce score
        fatigue_penalty = 0.0
        channel_count = prior_channels.count(channel.value)
        if channel_count >= 2:
            fatigue_penalty = 0.20
        elif channel_count == 1:
            fatigue_penalty = 0.08

        # Trust deficit bonus: if trust is low, favor high-trust channels
        trust_bonus = 0.0
        if result.trust_score < 0.5:
            trust_bonus = caps["trust_building"] / 500  # up to +0.19

        # Data gathering bonus: if needs_data, favor data-rich channels
        data_bonus = 0.0
        if result.verdict == "needs_data":
            data_bonus = caps["data_gathering"] / 500

        # Compute confidence
        raw_confidence = (intent_score * 0.5) + (caps["brand_adherence_base"] / 200) + trust_bonus + data_bonus - fatigue_penalty
        confidence = max(0.05, min(0.98, raw_confidence))

        # Derive channel-specific ethos targets
        ethos_targets = self._channel_ethos_targets(channel, brand_coherence)

        # Project NOCS based on channel capability and current performance
        projected_nocs = self._project_nocs(channel, result, confidence)

        # Build reasoning
        reasoning = self._channel_reasoning(channel, intent, result, confidence)

        # Build message frame
        message_frame = self._build_message_frame(channel, intent, result, segment_gap)

        # Determine tone
        tone = self._determine_tone(intent, result)

        # Risk factors
        risks = self._channel_risks(channel, result, prior_channels)

        return ChannelRecommendation(
            channel=channel,
            priority_rank=0,  # Set after sorting
            confidence=round(confidence, 3),
            reasoning=reasoning,
            suggested_message_frame=message_frame,
            suggested_tone=tone,
            key_talking_points=talking_points[:4],  # Top 4
            ethos_targets=ethos_targets,
            projected_nocs=round(projected_nocs, 1),
            projected_brand_adherence=float(caps["brand_adherence_base"]),
            estimated_duration_minutes=caps["duration_minutes"],
            risk_factors=risks,
        )

    def _intent_channel_alignment(self, intent: InteractionIntent, caps: Dict) -> float:
        """How well does this channel serve this intent? Returns 0-1."""
        alignment_map = {
            InteractionIntent.DISCOVERY: lambda c: (c["data_gathering"] + c["relationship_depth"]) / 200,
            InteractionIntent.QUALIFICATION: lambda c: (c["data_gathering"] + c["personalization"]) / 200,
            InteractionIntent.VALUE_DEMONSTRATION: lambda c: (c["personalization"] + c["trust_building"]) / 200,
            InteractionIntent.OBJECTION_HANDLING: lambda c: (c["relationship_depth"] + c["personalization"]) / 200,
            InteractionIntent.PROPOSAL: lambda c: (c["brand_adherence_base"] + c["personalization"]) / 200,
            InteractionIntent.CLOSE: lambda c: (c["relationship_depth"] + c["trust_building"]) / 200,
            InteractionIntent.NURTURE: lambda c: (c["scalability"] + c["brand_adherence_base"]) / 200,
            InteractionIntent.REACTIVATION: lambda c: (c["urgency_signal"] + c["personalization"]) / 200,
            InteractionIntent.DATA_GATHERING: lambda c: (c["data_gathering"] + c["scalability"]) / 200,
            InteractionIntent.TRUST_BUILDING: lambda c: (c["trust_building"] + c["relationship_depth"]) / 200,
        }
        fn = alignment_map.get(intent, lambda c: 0.5)
        return fn(caps)

    # ─── Talking points derivation ────────────────────────────────

    def _derive_talking_points(
        self, result: PipelineResult, gaps: List[str], segment_gap: str,
    ) -> List[str]:
        """Derive key talking points from pipeline state."""
        points = []

        # From verdict
        if result.verdict == "auto_execute":
            points.append("Strong fit confirmed — present proposal with specific ROI projections")
        elif result.verdict == "escalate_tier_1":
            points.append("Demonstrate value in their specific gap areas before advancing")
        elif result.verdict == "needs_data":
            points.append("Gather missing intelligence before qualifying further")
        elif result.verdict == "escalate_tier_2":
            points.append("Build trust through proof points and social validation")

        # From L1 gaps
        for gap in gaps[:3]:
            points.append(f"Address gap: {gap}")

        # From segment gap pattern
        if segment_gap:
            points.append(f"Primary serviceability gap: {segment_gap}")

        # From certificates
        certs = result.certificates
        if not certs.get("TC", True):
            points.append("Trust Certificate missing — lead with credibility evidence")
        if not certs.get("VC", True):
            points.append("Value Certificate missing — quantify ROI clearly")

        return points[:6]  # Max 6

    # ─── Ethos targets ────────────────────────────────────────────

    def _default_ethos_targets(self) -> Dict[str, float]:
        return {
            "truthfulness_explainability": 75,
            "human_centered_technology": 70,
            "long_term_value_creation": 75,
            "cost_roi_discipline": 70,
            "human_agency_respect": 75,
            "trust_contribution": 80,
            "manipulation_avoidance": 85,
        }

    def _channel_ethos_targets(
        self, channel: ChannelType, base_coherence: Dict[str, float],
    ) -> Dict[str, float]:
        """Adjust ethos targets per channel characteristics."""
        targets = dict(base_coherence)

        # Voice/in-person: higher trust and manipulation avoidance targets
        if channel in (ChannelType.VOICE, ChannelType.IN_PERSON, ChannelType.VIDEO):
            targets["trust_contribution"] = min(100, targets.get("trust_contribution", 70) + 10)
            targets["manipulation_avoidance"] = min(100, targets.get("manipulation_avoidance", 80) + 5)

        # Email/web: higher truthfulness targets (written record)
        if channel in (ChannelType.EMAIL, ChannelType.WEB, ChannelType.LINKEDIN):
            targets["truthfulness_explainability"] = min(100, targets.get("truthfulness_explainability", 70) + 10)
            targets["cost_roi_discipline"] = min(100, targets.get("cost_roi_discipline", 70) + 5)

        return {k: round(v, 1) for k, v in targets.items()}

    # ─── NOCS projection ─────────────────────────────────────────

    def _project_nocs(
        self, channel: ChannelType, result: PipelineResult, confidence: float,
    ) -> float:
        """Project expected NOCS for this channel."""
        caps = CHANNEL_CAPABILITIES[channel]
        # Base from channel quality potential
        base = (caps["brand_adherence_base"] + caps["personalization"]) / 2.5

        # Adjust for current pipeline state
        if result.avg_nocs > 0:
            # Use current NOCS as anchor, adjust by channel quality
            base = result.avg_nocs * (0.7 + confidence * 0.5)

        return max(10, min(95, base))

    # ─── Supporting derivations ───────────────────────────────────

    def _build_rationale(
        self, result: PipelineResult, intent: InteractionIntent, segment_gap: str,
    ) -> str:
        """Build strategic rationale statement."""
        parts = []
        parts.append(f"Pipeline verdict is {result.verdict} (value={result.value_score:.2f}, trust={result.trust_score:.2f}).")

        if intent == InteractionIntent.PROPOSAL:
            parts.append("All certificates pass — prospect is qualified for proposal delivery.")
        elif intent == InteractionIntent.VALUE_DEMONSTRATION:
            parts.append("Escalation required — demonstrate concrete value before advancing.")
        elif intent == InteractionIntent.DATA_GATHERING:
            parts.append("Insufficient data for qualification — gather key intelligence first.")
        elif intent == InteractionIntent.TRUST_BUILDING:
            parts.append("Trust deficit detected — build credibility through proof points.")

        if segment_gap:
            parts.append(f"Segment gap pattern: {segment_gap}.")

        blocking = result.blocking_gates
        if blocking:
            parts.append(f"Blocking gates: {', '.join(blocking)}.")

        return " ".join(parts)

    def _derive_success_criteria(
        self, result: PipelineResult, intent: InteractionIntent,
    ) -> List[str]:
        """What does success look like for this interaction?"""
        criteria = []

        if intent == InteractionIntent.PROPOSAL:
            criteria.extend([
                "Proposal delivered with clear ROI framing",
                "Decision timeline established",
                "Next meeting with economic buyer confirmed",
            ])
        elif intent == InteractionIntent.VALUE_DEMONSTRATION:
            criteria.extend([
                "Prospect articulates understanding of value proposition",
                "At least one specific pain point validated",
                "Internal champion identified or confirmed",
            ])
        elif intent == InteractionIntent.DATA_GATHERING:
            criteria.extend([
                "At least 3 new data points captured",
                "Current tech stack and budget cycle identified",
                "Decision-making process mapped",
            ])
        elif intent == InteractionIntent.TRUST_BUILDING:
            criteria.extend([
                "Relevant case study or reference shared",
                "Prospect shares internal context voluntarily",
                "Trust shift score positive (>0.1)",
            ])
        else:
            criteria.extend([
                "Engagement maintained",
                "Next touchpoint scheduled",
                "Sentiment neutral or positive",
            ])

        return criteria

    def _derive_blocking_conditions(self, result: PipelineResult) -> List[str]:
        """What conditions would block this interaction?"""
        blocks = []
        if result.blocking_gates:
            for gate in result.blocking_gates:
                blocks.append(f"Gate '{gate}' is blocking — resolve before engaging")
        if result.verdict == "block":
            blocks.append("Prospect is blocked — do not engage until conditions change")
        return blocks

    def _derive_prerequisites(self, result: PipelineResult) -> List[str]:
        """What data is needed before this interaction?"""
        prereqs = []
        if result.verdict == "needs_data":
            prereqs.extend([
                "Complete prospect profile (industries, personas, geographies)",
                "Verify company website and public signals",
                "Confirm buyer persona and decision authority",
            ])
        if not result.certificates.get("TC", True):
            prereqs.append("Prepare trust evidence (case studies, testimonials, certifications)")
        if not result.certificates.get("VC", True):
            prereqs.append("Prepare value quantification (ROI model, benchmarks)")
        return prereqs

    def _target_trust_shift(self, result: PipelineResult) -> float:
        """Target trust shift for next interaction."""
        if result.trust_score >= 0.8:
            return 0.1   # Maintain
        elif result.trust_score >= 0.5:
            return 0.2   # Build
        else:
            return 0.3   # Recover

    def _target_sentiment(self, result: PipelineResult) -> float:
        """Target sentiment score for next interaction."""
        if result.verdict == "auto_execute":
            return 0.85
        elif result.verdict in ("escalate_tier_1", "escalate_tier_2"):
            return 0.75
        else:
            return 0.65

    def _channel_reasoning(
        self, channel: ChannelType, intent: InteractionIntent,
        result: PipelineResult, confidence: float,
    ) -> str:
        """Generate reasoning for why this channel."""
        caps = CHANNEL_CAPABILITIES[channel]
        strengths = []
        if caps["trust_building"] >= 80:
            strengths.append("strong trust-building capacity")
        if caps["personalization"] >= 80:
            strengths.append("high personalization")
        if caps["data_gathering"] >= 70:
            strengths.append("effective data gathering")
        if caps["brand_adherence_base"] >= 75:
            strengths.append("controlled brand experience")
        if caps["scalability"] >= 80:
            strengths.append("highly scalable")

        strength_text = ", ".join(strengths) if strengths else "moderate across dimensions"
        return f"{channel.value.replace('_', ' ').title()} — {strength_text}. Confidence: {confidence:.0%} for {intent.value.replace('_', ' ')} intent."

    def _build_message_frame(
        self, channel: ChannelType, intent: InteractionIntent,
        result: PipelineResult, segment_gap: str,
    ) -> str:
        """Build the suggested opening message frame."""
        name = result.prospect_name

        frames = {
            InteractionIntent.PROPOSAL: f"Based on our analysis of {name}'s current infrastructure gaps, we've prepared a specific proposal addressing the identified opportunities with projected ROI timelines.",
            InteractionIntent.VALUE_DEMONSTRATION: f"I'd like to walk through how we've helped similar companies to {name} address exactly the kind of challenges you're facing{' — specifically around ' + segment_gap if segment_gap else ''}.",
            InteractionIntent.DATA_GATHERING: f"We're building out our understanding of {name}'s current landscape and would value a brief conversation to ensure any recommendations are precisely calibrated to your situation.",
            InteractionIntent.TRUST_BUILDING: f"Following up with some relevant proof points we discussed — including a case study from a company with a similar profile to {name}.",
            InteractionIntent.QUALIFICATION: f"I'd like to confirm a few details about {name}'s current priorities and timeline to ensure we're focusing on the right areas.",
            InteractionIntent.NURTURE: f"Sharing some insights we've been developing that are particularly relevant to companies like {name} in your space.",
            InteractionIntent.REACTIVATION: f"It's been a while since we connected — I wanted to share some new developments that may be relevant given what we discussed previously about {name}'s goals.",
        }

        return frames.get(intent, f"Continuing our engagement with {name} — next step in the qualification process.")

    def _determine_tone(self, intent: InteractionIntent, result: PipelineResult) -> str:
        """Determine recommended tone based on intent and state."""
        tone_map = {
            InteractionIntent.PROPOSAL: "confident-consultative",
            InteractionIntent.VALUE_DEMONSTRATION: "educational-empathetic",
            InteractionIntent.DATA_GATHERING: "curious-respectful",
            InteractionIntent.TRUST_BUILDING: "transparent-evidence-based",
            InteractionIntent.QUALIFICATION: "direct-professional",
            InteractionIntent.CLOSE: "assertive-collaborative",
            InteractionIntent.NURTURE: "warm-insightful",
            InteractionIntent.REACTIVATION: "friendly-value-forward",
            InteractionIntent.OBJECTION_HANDLING: "empathetic-logical",
            InteractionIntent.DISCOVERY: "curious-consultative",
        }
        return tone_map.get(intent, "professional-consultative")

    def _channel_risks(
        self, channel: ChannelType, result: PipelineResult, prior_channels: List[str],
    ) -> List[str]:
        """Identify risk factors for this channel."""
        risks = []
        caps = CHANNEL_CAPABILITIES[channel]

        if prior_channels.count(channel.value) >= 2:
            risks.append("Channel fatigue — prospect has received multiple touches via this channel")

        if caps["brand_adherence_base"] < 65:
            risks.append("Lower brand control — higher risk of off-brand messaging")

        if result.trust_score < 0.4 and caps["trust_building"] < 50:
            risks.append("Trust deficit + low trust-building channel = risk of disengagement")

        if result.verdict == "needs_data" and caps["data_gathering"] < 50:
            risks.append("Data gathering is priority but this channel has limited data capture")

        return risks
