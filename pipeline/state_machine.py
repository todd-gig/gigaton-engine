"""
Decision State Machine

Implements the 8-state decision lifecycle with valid transitions,
certificate requirements, and state progression logic.

States:
    draft → qualified → value_confirmed → trust_certified →
    execution_cleared → executed → reviewed → archived
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class DecisionState(str, Enum):
    """Decision lifecycle states."""
    DRAFT = "draft"
    QUALIFIED = "qualified"
    VALUE_CONFIRMED = "value_confirmed"
    TRUST_CERTIFIED = "trust_certified"
    EXECUTION_CLEARED = "execution_cleared"
    EXECUTED = "executed"
    REVIEWED = "reviewed"
    ARCHIVED = "archived"


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

VALID_TRANSITIONS = {
    DecisionState.DRAFT: [DecisionState.QUALIFIED, DecisionState.EXECUTION_CLEARED],
    DecisionState.QUALIFIED: [DecisionState.VALUE_CONFIRMED, DecisionState.DRAFT],
    DecisionState.VALUE_CONFIRMED: [DecisionState.TRUST_CERTIFIED, DecisionState.QUALIFIED],
    DecisionState.TRUST_CERTIFIED: [DecisionState.EXECUTION_CLEARED, DecisionState.QUALIFIED],
    DecisionState.EXECUTION_CLEARED: [DecisionState.EXECUTED, DecisionState.TRUST_CERTIFIED],
    DecisionState.EXECUTED: [DecisionState.REVIEWED],
    DecisionState.REVIEWED: [DecisionState.ARCHIVED, DecisionState.QUALIFIED],
    DecisionState.ARCHIVED: [],
}

STATE_CERTIFICATE_MAP = {
    DecisionState.DRAFT: [],
    DecisionState.QUALIFIED: ["QC"],
    DecisionState.VALUE_CONFIRMED: ["QC", "VC"],
    DecisionState.TRUST_CERTIFIED: ["QC", "VC", "TC"],
    DecisionState.EXECUTION_CLEARED: ["QC", "VC", "TC", "EC"],
    DecisionState.EXECUTED: ["QC", "VC", "TC", "EC"],
    DecisionState.REVIEWED: ["QC", "VC", "TC", "EC"],
    DecisionState.ARCHIVED: ["QC", "VC", "TC", "EC"],
}

VERDICT_TO_STATE = {
    "auto_execute": DecisionState.EXECUTION_CLEARED,
    "escalate_tier_1": DecisionState.TRUST_CERTIFIED,
    "escalate_tier_2": DecisionState.TRUST_CERTIFIED,
    "escalate_tier_3": DecisionState.TRUST_CERTIFIED,
    "block": DecisionState.DRAFT,
    "information_only": DecisionState.QUALIFIED,
    "needs_data": DecisionState.DRAFT,
}

STATE_ORDER = [
    DecisionState.DRAFT,
    DecisionState.QUALIFIED,
    DecisionState.VALUE_CONFIRMED,
    DecisionState.TRUST_CERTIFIED,
    DecisionState.EXECUTION_CLEARED,
    DecisionState.EXECUTED,
    DecisionState.REVIEWED,
    DecisionState.ARCHIVED,
]


# ─────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────

@dataclass
class StateTransitionResult:
    """Result of a state transition attempt."""
    success: bool
    previous_state: DecisionState
    current_state: DecisionState
    reason: str
    required_certificates: list = field(default_factory=list)


@dataclass
class LifecycleStatus:
    """Summary of a decision's lifecycle position."""
    current_state: DecisionState
    progress_pct: float
    certificates_held: list
    is_terminal: bool
    is_executable: bool
    is_pre_execution: bool
    is_post_execution: bool


# ─────────────────────────────────────────────
# STATE TRANSITIONS
# ─────────────────────────────────────────────

def can_transition(current_state: DecisionState, target_state: DecisionState) -> bool:
    """Check if a state transition is valid."""
    allowed = VALID_TRANSITIONS.get(current_state, [])
    return target_state in allowed


def next_state_for_verdict(verdict: str) -> DecisionState:
    """
    Determine the next state based on the engine's recommended verdict.

    Verdict strings from the 7-gate authorization system:
    - auto_execute
    - escalate_tier_1, escalate_tier_2, escalate_tier_3
    - block
    - information_only
    - needs_data
    """
    return VERDICT_TO_STATE.get(verdict, DecisionState.DRAFT)


def advance_state(current_state: DecisionState,
                 target_state: DecisionState) -> StateTransitionResult:
    """
    Attempt to advance the decision to a new state.

    Returns:
        StateTransitionResult with success flag, reason, and required certificates.
    """
    if can_transition(current_state, target_state):
        return StateTransitionResult(
            success=True,
            previous_state=current_state,
            current_state=target_state,
            reason=f"Valid transition from '{current_state.value}' to '{target_state.value}'",
            required_certificates=STATE_CERTIFICATE_MAP.get(target_state, [])
        )
    else:
        allowed = VALID_TRANSITIONS.get(current_state, [])
        allowed_names = [s.value for s in allowed]
        return StateTransitionResult(
            success=False,
            previous_state=current_state,
            current_state=current_state,
            reason=(
                f"Invalid transition from '{current_state.value}' to '{target_state.value}'. "
                f"Allowed: {allowed_names}"
            ),
            required_certificates=STATE_CERTIFICATE_MAP.get(current_state, [])
        )


# ─────────────────────────────────────────────
# LIFECYCLE TRACKING
# ─────────────────────────────────────────────

def get_lifecycle_status(current_state: DecisionState) -> LifecycleStatus:
    """Get a summary of the decision's lifecycle position."""
    try:
        idx = STATE_ORDER.index(current_state)
    except ValueError:
        idx = 0

    progress_pct = round((idx / (len(STATE_ORDER) - 1)) * 100, 1) if len(STATE_ORDER) > 1 else 0.0

    return LifecycleStatus(
        current_state=current_state,
        progress_pct=progress_pct,
        certificates_held=STATE_CERTIFICATE_MAP.get(current_state, []),
        is_terminal=current_state == DecisionState.ARCHIVED,
        is_executable=current_state == DecisionState.EXECUTION_CLEARED,
        is_pre_execution=current_state in (
            DecisionState.DRAFT,
            DecisionState.QUALIFIED,
            DecisionState.VALUE_CONFIRMED,
            DecisionState.TRUST_CERTIFIED,
        ),
        is_post_execution=current_state in (
            DecisionState.EXECUTED,
            DecisionState.REVIEWED,
            DecisionState.ARCHIVED,
        ),
    )
