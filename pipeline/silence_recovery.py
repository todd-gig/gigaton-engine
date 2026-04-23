"""
Silence Intelligence Engine (SIE) - Lead Recovery Module

Evaluates silent leads, computes priority scores, applies hard decision rules,
and recommends follow-up actions aligned with governance authority ceilings.

Core question: Given a silent lead, what is the next governed action with
the highest expected ROI?
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class SilenceStatus(str, Enum):
    """Lead silence classification."""
    ACTIVE = "active"
    SILENT = "silent"
    ENGAGED = "engaged"
    DISQUALIFIED = "disqualified"
    UNSUBSCRIBED = "unsubscribed"
    BOUNCED = "bounced"
    CLOSED = "closed"


class ActionType(str, Enum):
    """Follow-up action types aligned with policy ceiling."""
    SEND_EMAIL = "send_email"
    SEND_MESSAGE = "send_message"
    CREATE_TASK = "create_task"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    SCHEDULE_FOLLOW_UP = "schedule_follow_up"
    DO_NOT_EXECUTE = "do_not_execute"


class OutcomeType(str, Enum):
    """Outcome classification for learning loop."""
    REPLY_RECEIVED = "reply_received"
    MEETING_BOOKED = "meeting_booked"
    OPPORTUNITY_REVIVED = "opportunity_revived"
    DEAL_CLOSED = "deal_closed"
    NO_REPLY = "no_reply"
    BOUNCE = "bounce"
    UNSUBSCRIBE = "unsubscribe"
    FAILED_EXECUTION = "failed_execution"


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

# Baseline scoring weights (normalized to sum to 1.0)
SCORING_WEIGHTS = {
    "normalized_deal_value": 0.3,
    "silence_score": 0.3,
    "engagement_decay_score": 0.2,
    "stage_score": 0.2,
}

# Calibration policy for weight updates
CALIBRATION_POLICY = {
    "max_delta_per_cycle": 0.05,
    "min_weight": 0.02,
    "max_weight": 0.50,
    "cycle_hours": 24,
}

# Hard decision rule thresholds
HIGH_VALUE_THRESHOLD = 50000  # Dollars
MAX_ATTEMPTS_BEFORE_ESCALATION = 3
ESCALATION_SILENCE_THRESHOLD = 7  # Days

# Stage scoring reference (adjust as needed per business logic)
STAGE_SCORES = {
    "prospecting": 0.2,
    "lead": 0.3,
    "qualified": 0.5,
    "opportunity": 0.7,
    "proposal": 0.9,
    "negotiation": 0.95,
    "closed": 1.0,
}


# ─────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────

@dataclass
class LeadSilenceState:
    """Snapshot of a lead's silence and engagement state."""
    lead_id: str
    email: str
    stage: str
    days_since_last_touch: int
    previous_attempts: int
    status: str
    account_id: Optional[str] = None
    opportunity_id: Optional[str] = None
    owner_id: Optional[str] = None
    phone: Optional[str] = None
    deal_value: float = 0.0
    last_touch_at: Optional[str] = None
    last_reply_at: Optional[str] = None
    recent_open_signal: bool = False
    recent_click_signal: bool = False
    meeting_status: Optional[str] = None
    metadata: dict = field(default_factory=dict)

    def is_silent(self) -> bool:
        """Determine if lead is in silent state."""
        return self.status == SilenceStatus.SILENT.value

    def is_disqualified(self) -> bool:
        """Determine if lead is disqualified/unsubscribed/bounced."""
        disqualified_statuses = {
            SilenceStatus.DISQUALIFIED.value,
            SilenceStatus.UNSUBSCRIBED.value,
            SilenceStatus.BOUNCED.value,
        }
        return self.status in disqualified_statuses

    def has_engagement_signal(self) -> bool:
        """Check if lead shows any recent engagement signal."""
        return self.recent_open_signal or self.recent_click_signal

    def normalize_deal_value(self, max_expected_value: float = 500000) -> float:
        """Normalize deal value to [0, 1] range."""
        if max_expected_value <= 0:
            return 0.0
        return min(self.deal_value / max_expected_value, 1.0)


@dataclass
class CalibrationPolicy:
    """Weight calibration parameters for continuous learning."""
    max_delta_per_cycle: float = 0.05
    min_weight: float = 0.02
    max_weight: float = 0.50
    cycle_hours: int = 24


@dataclass
class FollowUpDecision:
    """Recommended follow-up action for a silent lead."""
    decision_id: str
    entity_id: str
    decision_type: str = "follow_up_action"
    context: dict = field(default_factory=dict)
    priority_score: float = 0.0
    trust_score: float = 0.0
    authority_level: str = "D1"
    selected_action: str = ActionType.DO_NOT_EXECUTE.value
    action_payload: dict = field(default_factory=dict)
    policy_gate_result: str = "approved"
    status: str = "proposed"
    created_at: str = ""
    executed_at: Optional[str] = None
    source_refs: list = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize decision to dict."""
        return {
            "decision_id": self.decision_id,
            "entity_id": self.entity_id,
            "decision_type": self.decision_type,
            "context": self.context,
            "priority_score": round(self.priority_score, 4),
            "trust_score": round(self.trust_score, 4),
            "authority_level": self.authority_level,
            "selected_action": self.selected_action,
            "action_payload": self.action_payload,
            "policy_gate_result": self.policy_gate_result,
            "status": self.status,
            "created_at": self.created_at,
            "executed_at": self.executed_at,
            "source_refs": self.source_refs,
        }


@dataclass
class DecisionOutcomeEvent:
    """Record of a decision outcome for learning loop."""
    outcome_id: str
    decision_id: str
    entity_id: str
    outcome_type: str
    observed_at: str
    revenue_impact: float = 0.0
    time_to_outcome_hours: float = 0.0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize outcome to dict."""
        return {
            "outcome_id": self.outcome_id,
            "decision_id": self.decision_id,
            "entity_id": self.entity_id,
            "outcome_type": self.outcome_type,
            "observed_at": self.observed_at,
            "revenue_impact": self.revenue_impact,
            "time_to_outcome_hours": self.time_to_outcome_hours,
            "metadata": self.metadata,
        }


# ─────────────────────────────────────────────
# SILENCE RECOVERY ENGINE
# ─────────────────────────────────────────────

class SilenceRecoveryEngine:
    """
    SIE core: Evaluates silent leads and recommends highest-ROI follow-up actions
    constrained by governance authority ceilings.
    """

    def __init__(self, policy: Optional[CalibrationPolicy] = None):
        self.policy = policy or CalibrationPolicy(**CALIBRATION_POLICY)
        self.weights = SCORING_WEIGHTS.copy()

    def evaluate_lead(self, lead: LeadSilenceState) -> dict:
        """
        Comprehensive lead evaluation including silence status, signals, and risk factors.

        Returns:
            dict with: is_silent, is_disqualified, has_signals, days_silence,
                      attempts_count, recommended_action_type
        """
        return {
            "is_silent": lead.is_silent(),
            "is_disqualified": lead.is_disqualified(),
            "has_engagement_signal": lead.has_engagement_signal(),
            "days_silence": lead.days_since_last_touch,
            "attempts_count": lead.previous_attempts,
            "owner_assigned": lead.owner_id is not None,
            "deal_value": lead.deal_value,
            "stage": lead.stage,
            "status": lead.status,
        }

    def compute_priority(self, lead: LeadSilenceState) -> float:
        """
        Compute priority score using weighted formula.

        Formula:
            priority_score =
              0.3 * normalized_deal_value +
              0.3 * silence_score +
              0.2 * engagement_decay_score +
              0.2 * stage_score

        Args:
            lead: LeadSilenceState snapshot

        Returns:
            float: priority score in [0, 1] range
        """
        # Normalized deal value: 0-1
        norm_value = lead.normalize_deal_value()

        # Silence score: based on days_since_last_touch
        # 0 days = 0, 30 days = 1.0
        silence_score = min(lead.days_since_last_touch / 30.0, 1.0)

        # Engagement decay: penalize for lack of signals
        # Has signal = 0.8, no signal = 0.3
        engagement_decay = 0.8 if lead.has_engagement_signal() else 0.3

        # Stage score from reference table
        stage_score = STAGE_SCORES.get(lead.stage.lower(), 0.5)

        # Weighted sum
        priority = (
            self.weights["normalized_deal_value"] * norm_value +
            self.weights["silence_score"] * silence_score +
            self.weights["engagement_decay_score"] * engagement_decay +
            self.weights["stage_score"] * stage_score
        )

        return round(priority, 4)

    def apply_hard_rules(self, lead: LeadSilenceState) -> tuple[bool, str, Optional[str]]:
        """
        Apply five hard decision rules from governance specification.

        Rules:
        1. If disqualified/unsubscribed/bounced -> do_not_execute
        2. If no owner assigned -> create_task (assign owner first)
        3. If days >= 3 and attempts < 3 -> send_email
        4. If days >= 7 and deal_value >= threshold -> escalate_to_human
        5. If attempts >= 3 and no reply -> create_task (alternate strategy)

        Returns:
            tuple: (passed, description, recommended_action)
                - passed: bool, True if no blocking rules triggered
                - description: str, reason for decision
                - recommended_action: Optional[str], action if blocked/overridden
        """
        # Rule 1: Disqualified leads
        if lead.is_disqualified():
            return False, "Lead is disqualified/unsubscribed/bounced", ActionType.DO_NOT_EXECUTE.value

        # Rule 2: No owner assigned
        if not lead.owner_id:
            return False, "No owner assigned; must create assignment task", ActionType.CREATE_TASK.value

        # Rule 4: High-value + high silence -> escalate
        if (lead.days_since_last_touch >= ESCALATION_SILENCE_THRESHOLD and
                lead.deal_value >= HIGH_VALUE_THRESHOLD):
            return False, "High-value lead silent >= 7 days; requires human review", ActionType.ESCALATE_TO_HUMAN.value

        # Rule 5: Exhausted attempts with no reply
        if (lead.previous_attempts >= MAX_ATTEMPTS_BEFORE_ESCALATION and
                not lead.has_engagement_signal()):
            return False, "Exhausted attempts; create alternative strategy task", ActionType.CREATE_TASK.value

        # Rule 3: Eligible for email (days >= 3, attempts < 3)
        if lead.days_since_last_touch >= 3 and lead.previous_attempts < MAX_ATTEMPTS_BEFORE_ESCALATION:
            return True, "Eligible for email per hard rule 3", None

        # Default pass
        return True, "No blocking rules triggered", None

    def check_authority(self, selected_action: str, authority_ceiling: str = "D2") -> tuple[bool, str]:
        """
        Validate action against policy authority ceiling.

        Authority mappings:
        - D1 ceiling: send_email OK
        - D2 ceiling: send_email, send_message, create_task OK
        - D3+ ceiling: requires escalate_to_human or higher approval

        Args:
            selected_action: str, the proposed action
            authority_ceiling: str, max authority level allowed (D1-D3+)

        Returns:
            tuple: (approved, reason)
        """
        d1_actions = {ActionType.SEND_EMAIL.value}
        d2_actions = {
            ActionType.SEND_EMAIL.value,
            ActionType.SEND_MESSAGE.value,
            ActionType.CREATE_TASK.value,
        }
        d3_plus_actions = {
            ActionType.ESCALATE_TO_HUMAN.value,
            ActionType.SCHEDULE_FOLLOW_UP.value,
        }

        if authority_ceiling == "D1":
            if selected_action in d1_actions:
                return True, "Action approved under D1 authority"
            else:
                return False, f"Action '{selected_action}' exceeds D1 ceiling"

        elif authority_ceiling == "D2":
            if selected_action in d2_actions:
                return True, "Action approved under D2 authority"
            else:
                return False, f"Action '{selected_action}' exceeds D2 ceiling"

        elif authority_ceiling in ("D3", "D3+"):
            if selected_action in (d1_actions | d2_actions | d3_plus_actions):
                return True, f"Action approved under {authority_ceiling} authority"
            else:
                return False, f"Action '{selected_action}' blocked"

        else:
            return False, f"Unknown authority ceiling: {authority_ceiling}"

    def select_action(self, lead: LeadSilenceState,
                     priority_score: float,
                     hard_rules_passed: bool,
                     hard_rule_override: Optional[str] = None,
                     authority_ceiling: str = "D2") -> FollowUpDecision:
        """
        Select follow-up action based on priority, hard rules, and authority.

        Decision logic:
        1. If hard rule triggered an override, use that action
        2. If hard rules passed and priority >= threshold, use priority-based action
        3. Otherwise use default (do_not_execute or escalate)

        Args:
            lead: LeadSilenceState
            priority_score: float, computed priority
            hard_rules_passed: bool
            hard_rule_override: Optional[str], action if rule blocked
            authority_ceiling: str, policy ceiling (D1-D3+)

        Returns:
            FollowUpDecision with selected_action and metadata
        """
        decision_id = f"DEC-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.utcnow().isoformat()

        context = {
            "days_since_last_touch": lead.days_since_last_touch,
            "deal_value": lead.deal_value,
            "stage": lead.stage,
            "previous_attempts": lead.previous_attempts,
            "prior_response_rate": 0.0,
            "account_tier": "standard",
            "owner_assigned": lead.owner_id is not None,
            "recent_open_signal": lead.recent_open_signal,
            "recent_click_signal": lead.recent_click_signal,
            "meeting_status": lead.meeting_status,
        }

        # Start with default decision
        selected_action = ActionType.DO_NOT_EXECUTE.value
        policy_gate_result = "approved"
        trust_score = priority_score

        # Apply hard rule override if present
        if not hard_rules_passed and hard_rule_override:
            selected_action = hard_rule_override
            trust_score = priority_score * 0.8  # Reduce trust for forced actions
        elif hard_rules_passed:
            # Select action based on priority thresholds
            if priority_score >= 0.7:
                selected_action = ActionType.SEND_EMAIL.value
            elif priority_score >= 0.5:
                selected_action = ActionType.CREATE_TASK.value
            elif priority_score >= 0.3:
                selected_action = ActionType.SCHEDULE_FOLLOW_UP.value
            else:
                selected_action = ActionType.DO_NOT_EXECUTE.value

        # Check authority ceiling
        auth_approved, auth_reason = self.check_authority(selected_action, authority_ceiling)
        if not auth_approved:
            selected_action = ActionType.DO_NOT_EXECUTE.value
            policy_gate_result = "blocked"
            trust_score = 0.0

        # Determine authority level
        authority_level = "D1" if selected_action == ActionType.SEND_EMAIL.value else (
            "D2" if selected_action in (ActionType.SEND_MESSAGE.value, ActionType.CREATE_TASK.value) else
            "D3"
        )

        # Build action payload
        action_payload = {
            "lead_id": lead.lead_id,
            "email": lead.email,
            "stage": lead.stage,
            "template_hint": self._get_template_hint(selected_action, lead),
        }

        decision = FollowUpDecision(
            decision_id=decision_id,
            entity_id=lead.lead_id,
            decision_type="follow_up_action",
            context=context,
            priority_score=priority_score,
            trust_score=round(trust_score, 4),
            authority_level=authority_level,
            selected_action=selected_action,
            action_payload=action_payload,
            policy_gate_result=policy_gate_result,
            status="proposed",
            created_at=created_at,
            source_refs=[f"lead:{lead.lead_id}"],
        )

        return decision

    def _get_template_hint(self, action: str, lead: LeadSilenceState) -> str:
        """Suggest template category based on action and lead state."""
        if action == ActionType.SEND_EMAIL.value:
            if lead.previous_attempts >= 2:
                return "re_engagement_3rd_touch"
            elif lead.previous_attempts >= 1:
                return "follow_up_2nd_touch"
            else:
                return "initial_follow_up"
        elif action == ActionType.CREATE_TASK.value:
            if lead.previous_attempts >= MAX_ATTEMPTS_BEFORE_ESCALATION:
                return "alternate_strategy_task"
            else:
                return "assignment_task"
        elif action == ActionType.ESCALATE_TO_HUMAN.value:
            return "high_value_escalation"
        else:
            return "default"

    def update_weights(self, performance_data: dict) -> None:
        """
        Calibrate weights based on outcome performance.

        Bounded update: each weight adjusts by at most max_delta_per_cycle
        and stays within [min_weight, max_weight].

        Args:
            performance_data: dict with weight_adjustments by key
        """
        for weight_key, delta in performance_data.items():
            if weight_key not in self.weights:
                continue

            current = self.weights[weight_key]
            new_val = current + delta

            # Apply bounds
            new_val = max(self.policy.min_weight, min(new_val, self.policy.max_weight))

            # Cap delta
            actual_delta = new_val - current
            if abs(actual_delta) > self.policy.max_delta_per_cycle:
                actual_delta = (
                    self.policy.max_delta_per_cycle
                    if actual_delta > 0
                    else -self.policy.max_delta_per_cycle
                )
                new_val = current + actual_delta

            self.weights[weight_key] = round(new_val, 4)
