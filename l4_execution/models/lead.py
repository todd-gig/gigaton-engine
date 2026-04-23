"""Lead model for managing lead lifecycle and progression."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List


class LeadStatus(str, Enum):
    """Enumeration of valid lead statuses."""

    NEW = "new"
    WORKING = "working"
    NURTURING = "nurturing"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    UNQUALIFIED = "unqualified"


@dataclass
class Lead:
    """Represents a lead in the interaction lifecycle."""

    lead_id: str
    prospect_id: str  # Links to L1 Sensing module
    entity_id: str  # Contact/actor identifier
    status: LeadStatus = LeadStatus.NEW
    channel: str = ""
    source: str = ""
    created_at: str = ""  # ISO 8601
    qualified_at: str = ""  # ISO 8601
    converted_at: str = ""  # ISO 8601
    interactions: List[str] = field(default_factory=list)  # interaction_ids
    score: float = 0.0  # 0-100 lead score

    def transition(self, new_status: LeadStatus) -> bool:
        """
        Enforce valid state transitions per 07_interaction_management_model.md:
        new -> working -> nurturing -> qualified -> converted | unqualified
        Also: working -> unqualified, nurturing -> unqualified
        """
        valid_transitions = {
            LeadStatus.NEW: [LeadStatus.WORKING],
            LeadStatus.WORKING: [LeadStatus.NURTURING, LeadStatus.UNQUALIFIED],
            LeadStatus.NURTURING: [LeadStatus.QUALIFIED, LeadStatus.UNQUALIFIED],
            LeadStatus.QUALIFIED: [LeadStatus.CONVERTED, LeadStatus.UNQUALIFIED],
            LeadStatus.CONVERTED: [],  # Terminal state
            LeadStatus.UNQUALIFIED: [],  # Terminal state
        }

        if new_status not in valid_transitions.get(self.status, []):
            return False

        self.status = new_status
        return True

    def validate_score(self) -> bool:
        """Verify that lead score is within valid bounds [0, 100]."""
        return 0.0 <= self.score <= 100.0
