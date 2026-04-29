"""Email execution data models.

Defines the email message structure, template metadata,
and execution result tracking for silence recovery emails.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum


class EmailStatus(str, Enum):
    """Status of an email execution attempt."""
    DRAFT = "draft"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    BOUNCED = "bounced"
    FAILED = "failed"
    DRY_RUN = "dry_run"


class TemplateType(str, Enum):
    """Email template categories aligned with SilenceRecoveryEngine template hints."""
    INITIAL_FOLLOW_UP = "initial_follow_up"
    FOLLOW_UP_2ND_TOUCH = "follow_up_2nd_touch"
    RE_ENGAGEMENT_3RD_TOUCH = "re_engagement_3rd_touch"
    HIGH_VALUE_ESCALATION = "high_value_escalation"
    ALTERNATE_STRATEGY = "alternate_strategy"
    VALUE_REMINDER = "value_reminder"
    BREAKUP = "breakup"


@dataclass
class EmailMessage:
    """A single email to be sent or that was sent."""
    message_id: str
    to_email: str
    to_name: str = ""
    from_email: str = ""
    from_name: str = ""
    subject: str = ""
    body_html: str = ""
    body_text: str = ""
    template_type: str = TemplateType.INITIAL_FOLLOW_UP.value
    status: str = EmailStatus.DRAFT.value
    # Linkage
    lead_id: str = ""
    decision_id: str = ""
    prospect_id: str = ""
    # Tracking
    created_at: str = ""
    sent_at: Optional[str] = None
    gmail_message_id: Optional[str] = None
    gmail_thread_id: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "to_email": self.to_email,
            "to_name": self.to_name,
            "from_email": self.from_email,
            "subject": self.subject,
            "template_type": self.template_type,
            "status": self.status,
            "lead_id": self.lead_id,
            "decision_id": self.decision_id,
            "created_at": self.created_at,
            "sent_at": self.sent_at,
            "gmail_message_id": self.gmail_message_id,
            "error_message": self.error_message,
        }


@dataclass
class ExecutionResult:
    """Result of executing a silence recovery decision via email."""
    decision_id: str
    lead_id: str
    action: str
    executed: bool = False
    dry_run: bool = False
    message: Optional[EmailMessage] = None
    error: Optional[str] = None
    executed_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "lead_id": self.lead_id,
            "action": self.action,
            "executed": self.executed,
            "dry_run": self.dry_run,
            "message": self.message.to_dict() if self.message else None,
            "error": self.error,
            "executed_at": self.executed_at,
        }
