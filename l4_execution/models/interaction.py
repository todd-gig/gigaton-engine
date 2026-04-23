"""InteractionEvent model for tracking brand interactions."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class InteractionEvent:
    """Represents a single interaction event across any channel."""

    interaction_id: str
    entity_id: str
    channel: str  # voice, sms, whatsapp, web, email, in_person
    timestamp: str  # ISO 8601
    status: str  # open, active, resolved, abandoned, escalated
    response_time_seconds: Optional[float] = None
    resolution_time_seconds: Optional[float] = None
    converted: bool = False
    abandoned: bool = False
    escalated: bool = False
    sentiment_score: float = 0.5  # 0-1, where 0.5 is neutral
    trust_shift_score: float = 0.0  # -1 to +1
