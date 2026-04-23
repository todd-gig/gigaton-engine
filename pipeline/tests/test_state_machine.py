"""
Test suite for state_machine.py - Decision lifecycle and state transitions.
"""

import pytest
from pipeline.state_machine import (
    DecisionState,
    VALID_TRANSITIONS,
    STATE_CERTIFICATE_MAP,
    VERDICT_TO_STATE,
    STATE_ORDER,
    can_transition,
    next_state_for_verdict,
    advance_state,
    get_lifecycle_status,
)


# ─────────────────────────────────────────────
# STATE TRANSITION VALIDITY
# ─────────────────────────────────────────────

def test_can_transition_draft_to_qualified():
    """Should allow draft -> qualified transition."""
    assert can_transition(DecisionState.DRAFT, DecisionState.QUALIFIED) is True


def test_can_transition_draft_to_execution_cleared():
    """Should allow draft -> execution_cleared (fast path)."""
    assert can_transition(DecisionState.DRAFT, DecisionState.EXECUTION_CLEARED) is True


def test_can_transition_invalid():
    """Should reject invalid transitions."""
    assert can_transition(DecisionState.DRAFT, DecisionState.EXECUTED) is False


def test_can_transition_from_archived():
    """Archived state should have no valid transitions."""
    assert can_transition(DecisionState.ARCHIVED, DecisionState.DRAFT) is False


def test_can_transition_qualified_backwards():
    """Should allow backward transition from qualified to draft."""
    assert can_transition(DecisionState.QUALIFIED, DecisionState.DRAFT) is True


def test_can_transition_executed_to_reviewed():
    """Should allow executed -> reviewed."""
    assert can_transition(DecisionState.EXECUTED, DecisionState.REVIEWED) is True


def test_can_transition_reviewed_to_archived():
    """Should allow reviewed -> archived."""
    assert can_transition(DecisionState.REVIEWED, DecisionState.ARCHIVED) is True


# ─────────────────────────────────────────────
# STATE ADVANCE WITH VALIDATION
# ─────────────────────────────────────────────

def test_advance_state_success():
    """Advance state should succeed for valid transition."""
    result = advance_state(DecisionState.DRAFT, DecisionState.QUALIFIED)
    assert result.success is True
    assert result.current_state == DecisionState.QUALIFIED
    assert result.previous_state == DecisionState.DRAFT


def test_advance_state_failure():
    """Advance state should fail for invalid transition."""
    result = advance_state(DecisionState.DRAFT, DecisionState.REVIEWED)
    assert result.success is False
    assert result.current_state == DecisionState.DRAFT


def test_advance_state_includes_required_certificates():
    """Result should list required certificates for target state."""
    result = advance_state(DecisionState.QUALIFIED, DecisionState.VALUE_CONFIRMED)
    # VALUE_CONFIRMED requires QC and VC
    assert "QC" in result.required_certificates
    assert "VC" in result.required_certificates


# ─────────────────────────────────────────────
# VERDICT TO STATE MAPPING
# ─────────────────────────────────────────────

def test_verdict_auto_execute():
    """auto_execute verdict should map to execution_cleared."""
    state = next_state_for_verdict("auto_execute")
    assert state == DecisionState.EXECUTION_CLEARED


def test_verdict_escalate_tier_1():
    """escalate_tier_1 verdict should map to trust_certified."""
    state = next_state_for_verdict("escalate_tier_1")
    assert state == DecisionState.TRUST_CERTIFIED


def test_verdict_escalate_tier_2():
    """escalate_tier_2 verdict should map to trust_certified."""
    state = next_state_for_verdict("escalate_tier_2")
    assert state == DecisionState.TRUST_CERTIFIED


def test_verdict_escalate_tier_3():
    """escalate_tier_3 verdict should map to trust_certified."""
    state = next_state_for_verdict("escalate_tier_3")
    assert state == DecisionState.TRUST_CERTIFIED


def test_verdict_block():
    """block verdict should map to draft."""
    state = next_state_for_verdict("block")
    assert state == DecisionState.DRAFT


def test_verdict_information_only():
    """information_only verdict should map to qualified."""
    state = next_state_for_verdict("information_only")
    assert state == DecisionState.QUALIFIED


def test_verdict_needs_data():
    """needs_data verdict should map to draft."""
    state = next_state_for_verdict("needs_data")
    assert state == DecisionState.DRAFT


def test_verdict_unknown_defaults_to_draft():
    """Unknown verdict should default to draft."""
    state = next_state_for_verdict("unknown_verdict")
    assert state == DecisionState.DRAFT


# ─────────────────────────────────────────────
# CERTIFICATE REQUIREMENTS
# ─────────────────────────────────────────────

def test_certificate_map_draft():
    """Draft state requires no certificates."""
    assert STATE_CERTIFICATE_MAP[DecisionState.DRAFT] == []


def test_certificate_map_qualified():
    """Qualified state requires QC only."""
    assert STATE_CERTIFICATE_MAP[DecisionState.QUALIFIED] == ["QC"]


def test_certificate_map_value_confirmed():
    """Value confirmed requires QC and VC."""
    assert set(STATE_CERTIFICATE_MAP[DecisionState.VALUE_CONFIRMED]) == {"QC", "VC"}


def test_certificate_map_trust_certified():
    """Trust certified requires QC, VC, and TC."""
    assert set(STATE_CERTIFICATE_MAP[DecisionState.TRUST_CERTIFIED]) == {"QC", "VC", "TC"}


def test_certificate_map_execution_cleared():
    """Execution cleared requires all four certificates."""
    assert set(STATE_CERTIFICATE_MAP[DecisionState.EXECUTION_CLEARED]) == {"QC", "VC", "TC", "EC"}


def test_certificate_map_executed():
    """Executed state maintains full certificate chain."""
    assert set(STATE_CERTIFICATE_MAP[DecisionState.EXECUTED]) == {"QC", "VC", "TC", "EC"}


def test_certificate_map_reviewed():
    """Reviewed state maintains full certificate chain."""
    assert set(STATE_CERTIFICATE_MAP[DecisionState.REVIEWED]) == {"QC", "VC", "TC", "EC"}


def test_certificate_map_archived():
    """Archived state maintains full certificate chain."""
    assert set(STATE_CERTIFICATE_MAP[DecisionState.ARCHIVED]) == {"QC", "VC", "TC", "EC"}


# ─────────────────────────────────────────────
# LIFECYCLE STATUS
# ─────────────────────────────────────────────

def test_lifecycle_status_draft():
    """Draft status should show beginning of lifecycle."""
    status = get_lifecycle_status(DecisionState.DRAFT)
    assert status.current_state == DecisionState.DRAFT
    assert status.progress_pct == 0.0
    assert status.is_terminal is False
    assert status.is_executable is False
    assert status.is_pre_execution is True
    assert status.is_post_execution is False


def test_lifecycle_status_execution_cleared():
    """Execution cleared should be marked as executable."""
    status = get_lifecycle_status(DecisionState.EXECUTION_CLEARED)
    assert status.is_executable is True
    assert status.is_pre_execution is False
    assert status.is_post_execution is False


def test_lifecycle_status_executed():
    """Executed should be marked as post-execution."""
    status = get_lifecycle_status(DecisionState.EXECUTED)
    assert status.is_post_execution is True
    assert status.is_executable is False
    assert status.is_terminal is False


def test_lifecycle_status_archived():
    """Archived should be marked as terminal."""
    status = get_lifecycle_status(DecisionState.ARCHIVED)
    assert status.is_terminal is True
    assert status.is_post_execution is True
    assert status.progress_pct == 100.0


def test_lifecycle_status_progress_calculation():
    """Progress should increase monotonically through lifecycle."""
    progress_values = []
    for state in STATE_ORDER:
        status = get_lifecycle_status(state)
        progress_values.append(status.progress_pct)

    # Progress should be monotonically increasing
    for i in range(1, len(progress_values)):
        assert progress_values[i] >= progress_values[i-1]

    # First should be 0, last should be 100
    assert progress_values[0] == 0.0
    assert progress_values[-1] == 100.0


def test_lifecycle_status_certificates():
    """Certificates should match state requirements."""
    for state in STATE_ORDER:
        status = get_lifecycle_status(state)
        expected = STATE_CERTIFICATE_MAP.get(state, [])
        assert set(status.certificates_held) == set(expected)


# ─────────────────────────────────────────────
# VALID TRANSITIONS STRUCTURE
# ─────────────────────────────────────────────

def test_valid_transitions_all_states():
    """VALID_TRANSITIONS should cover all states."""
    for state in DecisionState:
        assert state in VALID_TRANSITIONS


def test_valid_transitions_symmetric_draft_qualified():
    """Draft and qualified should allow transitions to each other."""
    draft_to_qualified = DecisionState.QUALIFIED in VALID_TRANSITIONS[DecisionState.DRAFT]
    qualified_to_draft = DecisionState.DRAFT in VALID_TRANSITIONS[DecisionState.QUALIFIED]
    assert draft_to_qualified is True
    assert qualified_to_draft is True


def test_valid_transitions_value_confirmed_progression():
    """Value confirmed should allow progression and regression."""
    transitions = VALID_TRANSITIONS[DecisionState.VALUE_CONFIRMED]
    assert DecisionState.TRUST_CERTIFIED in transitions
    assert DecisionState.QUALIFIED in transitions


def test_valid_transitions_no_reverse_from_executed():
    """Executed state should not allow backward transitions."""
    transitions = VALID_TRANSITIONS[DecisionState.EXECUTED]
    assert DecisionState.REVIEWED in transitions
    assert DecisionState.DRAFT not in transitions
    assert DecisionState.QUALIFIED not in transitions


# ─────────────────────────────────────────────
# STATE ORDER SEQUENCE
# ─────────────────────────────────────────────

def test_state_order_contains_all_states():
    """STATE_ORDER should contain all DecisionState values."""
    state_set = set(STATE_ORDER)
    for state in DecisionState:
        assert state in state_set


def test_state_order_draft_first():
    """STATE_ORDER should start with draft."""
    assert STATE_ORDER[0] == DecisionState.DRAFT


def test_state_order_archived_last():
    """STATE_ORDER should end with archived."""
    assert STATE_ORDER[-1] == DecisionState.ARCHIVED


def test_state_order_no_duplicates():
    """STATE_ORDER should have no duplicates."""
    assert len(STATE_ORDER) == len(set(STATE_ORDER))
