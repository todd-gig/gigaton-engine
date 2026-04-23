"""
Test suite for silence_recovery.py - SIE lead evaluation and action selection.
"""

import pytest
from pipeline.silence_recovery import (
    SilenceStatus,
    ActionType,
    OutcomeType,
    LeadSilenceState,
    CalibrationPolicy,
    FollowUpDecision,
    DecisionOutcomeEvent,
    SilenceRecoveryEngine,
    SCORING_WEIGHTS,
    CALIBRATION_POLICY,
    HIGH_VALUE_THRESHOLD,
    MAX_ATTEMPTS_BEFORE_ESCALATION,
    ESCALATION_SILENCE_THRESHOLD,
)


# ─────────────────────────────────────────────
# LEAD SILENCE STATE
# ─────────────────────────────────────────────

def test_lead_silence_state_creation():
    """Should create lead silence state with required fields."""
    lead = LeadSilenceState(
        lead_id="lead_001",
        email="contact@example.com",
        stage="opportunity",
        days_since_last_touch=5,
        previous_attempts=2,
        status="silent",
    )
    assert lead.lead_id == "lead_001"
    assert lead.status == "silent"


def test_lead_silence_state_is_silent():
    """Should identify silent leads."""
    silent_lead = LeadSilenceState(
        lead_id="lead_002",
        email="test@example.com",
        stage="lead",
        days_since_last_touch=7,
        previous_attempts=1,
        status="silent",
    )
    active_lead = LeadSilenceState(
        lead_id="lead_003",
        email="test2@example.com",
        stage="opportunity",
        days_since_last_touch=1,
        previous_attempts=0,
        status="active",
    )
    assert silent_lead.is_silent() is True
    assert active_lead.is_silent() is False


def test_lead_silence_state_is_disqualified():
    """Should identify disqualified leads."""
    disqualified = LeadSilenceState(
        lead_id="lead_004",
        email="bad@example.com",
        stage="closed",
        days_since_last_touch=30,
        previous_attempts=5,
        status="disqualified",
    )
    unsubscribed = LeadSilenceState(
        lead_id="lead_005",
        email="unsub@example.com",
        stage="lead",
        days_since_last_touch=10,
        previous_attempts=2,
        status="unsubscribed",
    )
    bounced = LeadSilenceState(
        lead_id="lead_006",
        email="invalid@example.com",
        stage="prospecting",
        days_since_last_touch=1,
        previous_attempts=0,
        status="bounced",
    )
    assert disqualified.is_disqualified() is True
    assert unsubscribed.is_disqualified() is True
    assert bounced.is_disqualified() is True


def test_lead_silence_state_has_engagement_signal():
    """Should detect recent engagement signals."""
    with_signal = LeadSilenceState(
        lead_id="lead_007",
        email="engaged@example.com",
        stage="opportunity",
        days_since_last_touch=5,
        previous_attempts=2,
        status="silent",
        recent_open_signal=True,
    )
    no_signal = LeadSilenceState(
        lead_id="lead_008",
        email="cold@example.com",
        stage="lead",
        days_since_last_touch=10,
        previous_attempts=3,
        status="silent",
        recent_open_signal=False,
        recent_click_signal=False,
    )
    assert with_signal.has_engagement_signal() is True
    assert no_signal.has_engagement_signal() is False


def test_lead_silence_state_normalize_deal_value():
    """Should normalize deal value to [0, 1]."""
    lead = LeadSilenceState(
        lead_id="lead_009",
        email="test@example.com",
        stage="proposal",
        days_since_last_touch=3,
        previous_attempts=1,
        status="active",
        deal_value=150000,
    )
    normalized = lead.normalize_deal_value(max_expected_value=500000)
    assert 0.0 <= normalized <= 1.0
    assert normalized == 0.3


# ─────────────────────────────────────────────
# SIE ENGINE INITIALIZATION
# ─────────────────────────────────────────────

def test_silence_recovery_engine_creation():
    """Should create SIE engine with default policy."""
    engine = SilenceRecoveryEngine()
    assert engine.policy is not None
    assert engine.weights == SCORING_WEIGHTS


def test_silence_recovery_engine_custom_policy():
    """Should accept custom calibration policy."""
    policy = CalibrationPolicy(
        max_delta_per_cycle=0.03,
        min_weight=0.01,
        max_weight=0.40,
        cycle_hours=12,
    )
    engine = SilenceRecoveryEngine(policy=policy)
    assert engine.policy.max_delta_per_cycle == 0.03


# ─────────────────────────────────────────────
# LEAD EVALUATION
# ─────────────────────────────────────────────

def test_evaluate_lead_silent():
    """Should evaluate lead state correctly."""
    lead = LeadSilenceState(
        lead_id="lead_010",
        email="test@example.com",
        stage="opportunity",
        days_since_last_touch=8,
        previous_attempts=2,
        status="silent",
        owner_id="owner_001",
        deal_value=50000,
    )
    engine = SilenceRecoveryEngine()
    eval_result = engine.evaluate_lead(lead)

    assert eval_result["is_silent"] is True
    assert eval_result["is_disqualified"] is False
    assert eval_result["days_silence"] == 8
    assert eval_result["attempts_count"] == 2
    assert eval_result["owner_assigned"] is True


# ─────────────────────────────────────────────
# PRIORITY SCORE COMPUTATION
# ─────────────────────────────────────────────

def test_compute_priority_high_value_engaged():
    """Should compute high priority for valuable, engaged leads."""
    lead = LeadSilenceState(
        lead_id="lead_011",
        email="vip@example.com",
        stage="proposal",
        days_since_last_touch=3,
        previous_attempts=1,
        status="silent",
        deal_value=200000,
        recent_open_signal=True,
    )
    engine = SilenceRecoveryEngine()
    score = engine.compute_priority(lead)

    assert 0.0 <= score <= 1.0
    assert score > 0.4  # Should be moderate to high


def test_compute_priority_low_value_cold():
    """Should compute low priority for low-value, cold leads."""
    lead = LeadSilenceState(
        lead_id="lead_012",
        email="cold@example.com",
        stage="prospecting",
        days_since_last_touch=1,
        previous_attempts=0,
        status="active",
        deal_value=1000,
        recent_open_signal=False,
        recent_click_signal=False,
    )
    engine = SilenceRecoveryEngine()
    score = engine.compute_priority(lead)

    assert 0.0 <= score <= 1.0
    assert score < 0.4  # Should be relatively low


def test_compute_priority_formula_weights():
    """Priority score should use configured weights."""
    lead = LeadSilenceState(
        lead_id="lead_013",
        email="test@example.com",
        stage="opportunity",
        days_since_last_touch=10,
        previous_attempts=2,
        status="silent",
        deal_value=100000,
        recent_open_signal=True,
    )
    engine = SilenceRecoveryEngine()
    score = engine.compute_priority(lead)

    # Verify weights sum to 1.0
    assert sum(engine.weights.values()) == pytest.approx(1.0, abs=0.01)
    # Score should be in valid range
    assert 0.0 <= score <= 1.0


# ─────────────────────────────────────────────
# HARD DECISION RULES
# ─────────────────────────────────────────────

def test_hard_rule_disqualified():
    """Rule 1: Disqualified leads should block execution."""
    lead = LeadSilenceState(
        lead_id="lead_014",
        email="bad@example.com",
        stage="closed",
        days_since_last_touch=5,
        previous_attempts=2,
        status="disqualified",
    )
    engine = SilenceRecoveryEngine()
    passed, reason, action = engine.apply_hard_rules(lead)

    assert passed is False
    assert action == ActionType.DO_NOT_EXECUTE.value


def test_hard_rule_no_owner():
    """Rule 2: Missing owner should trigger assignment task."""
    lead = LeadSilenceState(
        lead_id="lead_015",
        email="unassigned@example.com",
        stage="lead",
        days_since_last_touch=3,
        previous_attempts=1,
        status="silent",
        owner_id=None,
    )
    engine = SilenceRecoveryEngine()
    passed, reason, action = engine.apply_hard_rules(lead)

    assert passed is False
    assert action == ActionType.CREATE_TASK.value


def test_hard_rule_high_value_escalation():
    """Rule 4: High-value leads silent >= 7 days should escalate."""
    lead = LeadSilenceState(
        lead_id="lead_016",
        email="vip@example.com",
        stage="proposal",
        days_since_last_touch=ESCALATION_SILENCE_THRESHOLD,
        previous_attempts=2,
        status="silent",
        owner_id="owner_001",
        deal_value=HIGH_VALUE_THRESHOLD,
    )
    engine = SilenceRecoveryEngine()
    passed, reason, action = engine.apply_hard_rules(lead)

    assert passed is False
    assert action == ActionType.ESCALATE_TO_HUMAN.value


def test_hard_rule_exhausted_attempts():
    """Rule 5: Exhausted attempts with no reply should create task."""
    lead = LeadSilenceState(
        lead_id="lead_017",
        email="tired@example.com",
        stage="opportunity",
        days_since_last_touch=10,
        previous_attempts=MAX_ATTEMPTS_BEFORE_ESCALATION,
        status="silent",
        owner_id="owner_001",
        deal_value=25000,
        recent_open_signal=False,
    )
    engine = SilenceRecoveryEngine()
    passed, reason, action = engine.apply_hard_rules(lead)

    assert passed is False
    assert action == ActionType.CREATE_TASK.value


def test_hard_rule_eligible_for_email():
    """Rule 3: Leads with 3+ days silence and < 3 attempts eligible for email."""
    lead = LeadSilenceState(
        lead_id="lead_018",
        email="eligible@example.com",
        stage="qualified",
        days_since_last_touch=3,
        previous_attempts=1,
        status="silent",
        owner_id="owner_001",
        deal_value=15000,
    )
    engine = SilenceRecoveryEngine()
    passed, reason, action = engine.apply_hard_rules(lead)

    assert passed is True
    assert action is None


# ─────────────────────────────────────────────
# AUTHORITY CHECKS
# ─────────────────────────────────────────────

def test_check_authority_send_email_d1():
    """Send email should be approved under D1 ceiling."""
    engine = SilenceRecoveryEngine()
    approved, reason = engine.check_authority(
        ActionType.SEND_EMAIL.value,
        authority_ceiling="D1",
    )
    assert approved is True


def test_check_authority_create_task_d1():
    """Create task should be rejected under D1 ceiling."""
    engine = SilenceRecoveryEngine()
    approved, reason = engine.check_authority(
        ActionType.CREATE_TASK.value,
        authority_ceiling="D1",
    )
    assert approved is False


def test_check_authority_create_task_d2():
    """Create task should be approved under D2 ceiling."""
    engine = SilenceRecoveryEngine()
    approved, reason = engine.check_authority(
        ActionType.CREATE_TASK.value,
        authority_ceiling="D2",
    )
    assert approved is True


def test_check_authority_escalate_d2():
    """Escalation should be rejected under D2 ceiling."""
    engine = SilenceRecoveryEngine()
    approved, reason = engine.check_authority(
        ActionType.ESCALATE_TO_HUMAN.value,
        authority_ceiling="D2",
    )
    assert approved is False


def test_check_authority_escalate_d3():
    """Escalation should be approved under D3+ ceiling."""
    engine = SilenceRecoveryEngine()
    approved, reason = engine.check_authority(
        ActionType.ESCALATE_TO_HUMAN.value,
        authority_ceiling="D3",
    )
    assert approved is True


# ─────────────────────────────────────────────
# ACTION SELECTION
# ─────────────────────────────────────────────

def test_select_action_hard_rule_override():
    """Hard rule override should select specified action."""
    lead = LeadSilenceState(
        lead_id="lead_019",
        email="override@example.com",
        stage="lead",
        days_since_last_touch=5,
        previous_attempts=2,
        status="silent",
        owner_id="owner_001",
    )
    engine = SilenceRecoveryEngine()
    decision = engine.select_action(
        lead=lead,
        priority_score=0.6,
        hard_rules_passed=False,
        hard_rule_override=ActionType.ESCALATE_TO_HUMAN.value,
        authority_ceiling="D3",
    )
    assert decision.selected_action == ActionType.ESCALATE_TO_HUMAN.value


def test_select_action_priority_high():
    """High priority should trigger email action."""
    lead = LeadSilenceState(
        lead_id="lead_020",
        email="hot@example.com",
        stage="proposal",
        days_since_last_touch=5,
        previous_attempts=1,
        status="silent",
        owner_id="owner_001",
        deal_value=100000,
    )
    engine = SilenceRecoveryEngine()
    decision = engine.select_action(
        lead=lead,
        priority_score=0.75,
        hard_rules_passed=True,
        authority_ceiling="D2",
    )
    assert decision.selected_action == ActionType.SEND_EMAIL.value


def test_select_action_priority_medium():
    """Medium priority should trigger task creation."""
    lead = LeadSilenceState(
        lead_id="lead_021",
        email="medium@example.com",
        stage="qualified",
        days_since_last_touch=5,
        previous_attempts=2,
        status="silent",
        owner_id="owner_001",
        deal_value=20000,
    )
    engine = SilenceRecoveryEngine()
    decision = engine.select_action(
        lead=lead,
        priority_score=0.55,
        hard_rules_passed=True,
        authority_ceiling="D2",
    )
    assert decision.selected_action == ActionType.CREATE_TASK.value


def test_select_action_blocked_by_authority():
    """Action exceeding ceiling should be blocked."""
    lead = LeadSilenceState(
        lead_id="lead_022",
        email="restricted@example.com",
        stage="proposal",
        days_since_last_touch=8,
        previous_attempts=2,
        status="silent",
        owner_id="owner_001",
        deal_value=75000,
    )
    engine = SilenceRecoveryEngine()
    decision = engine.select_action(
        lead=lead,
        priority_score=0.8,
        hard_rules_passed=True,
        authority_ceiling="D1",  # Only email allowed
    )
    # Email should be selected (highest priority that fits D1)
    assert decision.selected_action == ActionType.SEND_EMAIL.value


def test_select_action_creates_valid_decision():
    """Select action should create valid FollowUpDecision."""
    lead = LeadSilenceState(
        lead_id="lead_023",
        email="test@example.com",
        stage="opportunity",
        days_since_last_touch=5,
        previous_attempts=1,
        status="silent",
        owner_id="owner_001",
    )
    engine = SilenceRecoveryEngine()
    decision = engine.select_action(
        lead=lead,
        priority_score=0.6,
        hard_rules_passed=True,
        authority_ceiling="D2",
    )

    assert decision.decision_id.startswith("DEC-")
    assert decision.entity_id == lead.lead_id
    assert decision.selected_action in (
        ActionType.SEND_EMAIL.value,
        ActionType.CREATE_TASK.value,
        ActionType.DO_NOT_EXECUTE.value,
    )


# ─────────────────────────────────────────────
# WEIGHT CALIBRATION
# ─────────────────────────────────────────────

def test_update_weights_bounded():
    """Weights should update with bounded delta."""
    engine = SilenceRecoveryEngine()
    original_value = engine.weights["normalized_deal_value"]

    performance_data = {
        "normalized_deal_value": 0.10,  # 10% increase
    }
    engine.update_weights(performance_data)

    # Delta should be capped at max_delta_per_cycle
    actual_delta = engine.weights["normalized_deal_value"] - original_value
    assert abs(actual_delta) <= CALIBRATION_POLICY["max_delta_per_cycle"]


def test_update_weights_min_max_bounds():
    """Weights should respect min and max bounds."""
    engine = SilenceRecoveryEngine()

    # Try to set weight below minimum
    performance_data = {
        "normalized_deal_value": -1.0,
    }
    engine.update_weights(performance_data)
    assert engine.weights["normalized_deal_value"] >= CALIBRATION_POLICY["min_weight"]

    # Try to set weight above maximum
    performance_data = {
        "normalized_deal_value": 1.0,
    }
    engine.update_weights(performance_data)
    assert engine.weights["normalized_deal_value"] <= CALIBRATION_POLICY["max_weight"]


# ─────────────────────────────────────────────
# OUTCOME EVENTS
# ─────────────────────────────────────────────

def test_decision_outcome_event_creation():
    """Should create outcome event with required fields."""
    event = DecisionOutcomeEvent(
        outcome_id="OUT-001",
        decision_id="DEC-024",
        entity_id="lead_024",
        outcome_type=OutcomeType.REPLY_RECEIVED.value,
        observed_at="2026-04-23T15:30:00",
        revenue_impact=5000.0,
        time_to_outcome_hours=4.5,
    )
    assert event.outcome_id == "OUT-001"
    assert event.revenue_impact == 5000.0


def test_decision_outcome_event_to_dict():
    """Outcome event should serialize to dict."""
    event = DecisionOutcomeEvent(
        outcome_id="OUT-002",
        decision_id="DEC-025",
        entity_id="lead_025",
        outcome_type=OutcomeType.MEETING_BOOKED.value,
        observed_at="2026-04-23T16:00:00",
    )
    event_dict = event.to_dict()
    assert event_dict["outcome_type"] == OutcomeType.MEETING_BOOKED.value
    assert event_dict["decision_id"] == "DEC-025"


# ─────────────────────────────────────────────
# FOLLOW-UP DECISION SERIALIZATION
# ─────────────────────────────────────────────

def test_follow_up_decision_to_dict():
    """Follow-up decision should serialize completely."""
    decision = FollowUpDecision(
        decision_id="DEC-026",
        entity_id="lead_026",
        priority_score=0.72,
        trust_score=0.68,
        selected_action=ActionType.SEND_EMAIL.value,
        policy_gate_result="approved",
    )
    decision_dict = decision.to_dict()

    assert decision_dict["decision_id"] == "DEC-026"
    assert decision_dict["priority_score"] == 0.72
    assert decision_dict["selected_action"] == ActionType.SEND_EMAIL.value
