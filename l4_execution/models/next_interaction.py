"""
Next Interaction Experience (NIX) models.

Represents a recommended next interaction across any channel,
derived from the full L1→L3→L4 pipeline state. Each recommendation
includes channel selection, timing, message framing, ethos targets,
and projected NOCS — all editable by the operator.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum


class ChannelType(Enum):
    """Supported interaction channels."""
    EMAIL = "email"
    VOICE = "voice"
    SMS = "sms"
    WEB = "web"
    WHATSAPP = "whatsapp"
    IN_PERSON = "in_person"
    LINKEDIN = "linkedin"
    VIDEO = "video"


class InteractionIntent(Enum):
    """Primary intent of the interaction."""
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    VALUE_DEMONSTRATION = "value_demonstration"
    OBJECTION_HANDLING = "objection_handling"
    PROPOSAL = "proposal"
    CLOSE = "close"
    NURTURE = "nurture"
    REACTIVATION = "reactivation"
    DATA_GATHERING = "data_gathering"
    TRUST_BUILDING = "trust_building"


class Urgency(Enum):
    """Timing urgency."""
    IMMEDIATE = "immediate"       # Within hours
    NEXT_DAY = "next_day"         # Within 24h
    THIS_WEEK = "this_week"       # Within 7 days
    NEXT_WEEK = "next_week"       # 7-14 days
    DEFERRED = "deferred"         # When data available


@dataclass
class ChannelRecommendation:
    """Recommendation for a single channel."""
    channel: ChannelType
    priority_rank: int              # 1 = highest priority channel
    confidence: float               # 0-1 how confident in this channel choice
    reasoning: str                  # Why this channel
    suggested_message_frame: str    # Opening frame / approach
    suggested_tone: str             # e.g. "consultative", "assertive", "empathetic"
    key_talking_points: List[str]   # What to cover
    ethos_targets: Dict[str, float] # Target ethos dimension scores (0-100)
    projected_nocs: float           # Expected NOCS if executed well
    projected_brand_adherence: float # Expected brand_adherence score
    estimated_duration_minutes: int  # Expected interaction length
    risk_factors: List[str]         # What could go wrong

    # Editable fields (operator can override)
    operator_override_message: str = ""
    operator_override_tone: str = ""
    operator_notes: str = ""
    is_approved: bool = False


@dataclass
class NextInteractionExperience:
    """Complete next interaction recommendation for a prospect.

    Contains recommendations across ALL channels, ranked by priority,
    plus the overall strategic recommendation and timing guidance.
    """
    prospect_id: str
    prospect_name: str
    verdict: str                    # Current pipeline verdict
    current_fit_score: float        # L1 total
    current_value_score: float      # L3 value
    current_trust_score: float      # L3 trust

    # Strategic recommendation
    primary_intent: InteractionIntent
    urgency: Urgency
    strategic_rationale: str        # Why this intent + timing

    # Channel recommendations (all channels, ranked)
    channel_recommendations: List[ChannelRecommendation] = field(default_factory=list)

    # What success looks like
    success_criteria: List[str] = field(default_factory=list)
    target_trust_shift: float = 0.0     # Expected trust delta
    target_sentiment: float = 0.7       # Target sentiment score

    # Constraints
    blocking_conditions: List[str] = field(default_factory=list)
    prerequisite_data: List[str] = field(default_factory=list)

    # Operator edit state
    operator_selected_channel: Optional[str] = None
    operator_approved: bool = False

    @property
    def primary_channel(self) -> Optional[ChannelRecommendation]:
        """Get the highest-priority channel recommendation."""
        if self.channel_recommendations:
            return self.channel_recommendations[0]
        return None

    def get_channel(self, channel_type: ChannelType) -> Optional[ChannelRecommendation]:
        """Get recommendation for a specific channel."""
        for rec in self.channel_recommendations:
            if rec.channel == channel_type:
                return rec
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for dashboard rendering."""
        return {
            "prospect_id": self.prospect_id,
            "prospect_name": self.prospect_name,
            "verdict": self.verdict,
            "current_fit_score": self.current_fit_score,
            "current_value_score": self.current_value_score,
            "current_trust_score": self.current_trust_score,
            "primary_intent": self.primary_intent.value,
            "urgency": self.urgency.value,
            "strategic_rationale": self.strategic_rationale,
            "success_criteria": self.success_criteria,
            "target_trust_shift": self.target_trust_shift,
            "target_sentiment": self.target_sentiment,
            "blocking_conditions": self.blocking_conditions,
            "prerequisite_data": self.prerequisite_data,
            "operator_selected_channel": self.operator_selected_channel,
            "operator_approved": self.operator_approved,
            "channels": [
                {
                    "channel": rec.channel.value,
                    "priority_rank": rec.priority_rank,
                    "confidence": rec.confidence,
                    "reasoning": rec.reasoning,
                    "suggested_message_frame": rec.suggested_message_frame,
                    "suggested_tone": rec.suggested_tone,
                    "key_talking_points": rec.key_talking_points,
                    "ethos_targets": rec.ethos_targets,
                    "projected_nocs": rec.projected_nocs,
                    "projected_brand_adherence": rec.projected_brand_adherence,
                    "estimated_duration_minutes": rec.estimated_duration_minutes,
                    "risk_factors": rec.risk_factors,
                    "operator_override_message": rec.operator_override_message,
                    "operator_override_tone": rec.operator_override_tone,
                    "operator_notes": rec.operator_notes,
                    "is_approved": rec.is_approved,
                }
                for rec in self.channel_recommendations
            ],
        }
