"""Campaign model for managing multi-channel marketing campaigns."""

from dataclasses import dataclass, field
from typing import List


@dataclass
class Campaign:
    """Represents a marketing campaign across one or more channels."""

    campaign_id: str
    name: str
    channel: str  # voice, sms, whatsapp, web, email, in_person, multi
    status: str = "draft"  # draft, active, paused, completed
    start_date: str = ""  # ISO 8601
    end_date: str = ""  # ISO 8601
    target_segments: List[str] = field(default_factory=list)  # segment_ids
    lead_ids: List[str] = field(default_factory=list)  # lead_ids in campaign
    interaction_ids: List[str] = field(default_factory=list)  # interaction_ids
    budget: float = 0.0
    spend: float = 0.0

    def activate(self) -> bool:
        """Transition campaign from draft to active."""
        if self.status == "draft":
            self.status = "active"
            return True
        return False

    def pause(self) -> bool:
        """Pause an active campaign."""
        if self.status == "active":
            self.status = "paused"
            return True
        return False

    def resume(self) -> bool:
        """Resume a paused campaign."""
        if self.status == "paused":
            self.status = "active"
            return True
        return False

    def complete(self) -> bool:
        """Mark campaign as completed."""
        if self.status in ["active", "paused"]:
            self.status = "completed"
            return True
        return False

    def get_budget_remaining(self) -> float:
        """Calculate remaining budget."""
        return max(0.0, self.budget - self.spend)

    def get_spend_rate(self) -> float:
        """Calculate percentage of budget spent."""
        if self.budget == 0.0:
            return 0.0
        return (self.spend / self.budget) * 100.0
