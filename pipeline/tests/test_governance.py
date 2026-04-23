"""
Test suite for governance.py - 7-gate authorization system and policy gating.
"""

import pytest
from pipeline.governance import (
    DecisionClass,
    ReversibilityTag,
    TrustTier,
    PolicyGateResult,
    TRUST_TIER_MINIMUMS,
    VALUE_THRESHOLDS,
    AUTO_EXECUTE_REVERSIBILITY,
    MANDATORY_HUMAN_CLASSES,
    ROLE_HIERARCHY,
    gate_1_doctrine,
    gate_2_trust_tier,
    gate_3_value_threshold,
    gate_4_reversibility,
    gate_5_risk_containment,
    gate_6_approval_routing,
    gate_7_monitoring,
    determine_escalation_tier,
    check_policy_gate,
    check_authority,
)


# ─────────────────────────────────────────────
# GATE 1: DOCTRINE
# ─────────────────────────────────────────────

def test_gate_1_doctrine_pass():
    """Gate 1 should pass for valid doctrine alignment."""
    result = gate_1_doctrine(
        doctrine_alignment=0.85,
        anti_patterns=[],
        ethical_misalignment=1.5,
    )
    assert result.passed is True
    assert "doctrine" in result.reason.lower()


def test_gate_1_doctrine_fail_low_composite():
    """Gate 1 should fail if composite alignment is too low."""
    result = gate_1_doctrine(
        doctrine_alignment=0.2,
        anti_patterns=["optics_over_substance"],
        ethical_misalignment=4.0,
    )
    assert result.passed is False


# ─────────────────────────────────────────────
# GATE 2: TRUST TIER
# ─────────────────────────────────────────────

def test_gate_2_trust_tier_sufficient():
    """Gate 2 should pass when trust tier meets minimum."""
    result = gate_2_trust_tier(
        decision_class=DecisionClass.D2_OPERATIONAL,
        trust_tier=TrustTier.T2_QUALIFIED,
    )
    assert result.passed is True


def test_gate_2_trust_tier_insufficient():
    """Gate 2 should fail when trust tier is below minimum."""
    result = gate_2_trust_tier(
        decision_class=DecisionClass.D4_STRATEGIC,
        trust_tier=TrustTier.T1_OBSERVED,
    )
    assert result.passed is False


def test_gate_2_trust_tier_d0_no_requirement():
    """Gate 2 should pass for D0 (informational) with any trust tier."""
    result = gate_2_trust_tier(
        decision_class=DecisionClass.D0_INFORMATIONAL,
        trust_tier=TrustTier.T0_UNQUALIFIED,
    )
    assert result.passed is True


# ─────────────────────────────────────────────
# GATE 3: VALUE THRESHOLD
# ─────────────────────────────────────────────

def test_gate_3_value_threshold_pass():
    """Gate 3 should pass when value exceeds decision class threshold."""
    result = gate_3_value_threshold(
        decision_class=DecisionClass.D2_OPERATIONAL,
        net_value=12,
    )
    assert result.passed is True


def test_gate_3_value_threshold_fail():
    """Gate 3 should fail when value is below threshold."""
    result = gate_3_value_threshold(
        decision_class=DecisionClass.D3_FINANCIAL,
        net_value=5,
    )
    assert result.passed is False


def test_gate_3_value_threshold_d0_unlimited():
    """Gate 3 should pass for D0 regardless of value."""
    result = gate_3_value_threshold(
        decision_class=DecisionClass.D0_INFORMATIONAL,
        net_value=0,
    )
    assert result.passed is True


# ─────────────────────────────────────────────
# GATE 4: REVERSIBILITY
# ─────────────────────────────────────────────

def test_gate_4_reversibility_auto_eligible():
    """Gate 4 should pass for reversible actions (R1, R2)."""
    result = gate_4_reversibility(
        decision_class=DecisionClass.D1_REVERSIBLE_TACTICAL,
        reversibility=ReversibilityTag.R1_EASILY_REVERSIBLE,
    )
    assert result.passed is True


def test_gate_4_reversibility_not_auto_eligible():
    """Gate 4 should fail for irreversible actions (R3, R4)."""
    result = gate_4_reversibility(
        decision_class=DecisionClass.D2_OPERATIONAL,
        reversibility=ReversibilityTag.R4_PERMANENT,
    )
    assert result.passed is False


# ─────────────────────────────────────────────
# GATE 5: RISK CONTAINMENT
# ─────────────────────────────────────────────

def test_gate_5_risk_containment_pass():
    """Gate 5 should pass for acceptable risk profile."""
    result = gate_5_risk_containment(
        downside_risk=2.0,
        uncertainty=1.5,
        reversibility=ReversibilityTag.R2_MODERATELY_REVERSIBLE,
        rollback_trigger=True,
        monitoring_metric=True,
    )
    assert result.passed is True


def test_gate_5_risk_containment_violations():
    """Gate 5 should fail if violations detected."""
    result = gate_5_risk_containment(
        downside_risk=4.0,
        uncertainty=4.0,
        reversibility=ReversibilityTag.R4_PERMANENT,
        rollback_trigger=False,
        monitoring_metric=False,
    )
    assert result.passed is False


# ─────────────────────────────────────────────
# GATE 6: APPROVAL ROUTING
# ─────────────────────────────────────────────

def test_gate_6_approval_routing_d1():
    """Gate 6 should route D1 to AI agent."""
    result = gate_6_approval_routing(
        decision_class=DecisionClass.D1_REVERSIBLE_TACTICAL,
        trust_tier=TrustTier.T3_CERTIFIED,
        required_approvals=[],
        owner="system",
    )
    assert result.passed is True
    assert "auto" in result.reason.lower()


def test_gate_6_approval_routing_d3():
    """Gate 6 should route D3 to human for approval."""
    result = gate_6_approval_routing(
        decision_class=DecisionClass.D3_FINANCIAL,
        trust_tier=TrustTier.T2_QUALIFIED,
        required_approvals=["exec_approver"],
        owner="domain_owner",
    )
    assert result.passed is True
    assert "approval" in result.reason.lower()


# ─────────────────────────────────────────────
# GATE 7: MONITORING
# ─────────────────────────────────────────────

def test_gate_7_monitoring_pass():
    """Gate 7 should pass when monitoring is configured."""
    result = gate_7_monitoring(
        monitoring_metric=True,
        review_date=True,
        rollback_trigger=True,
        decision_class=DecisionClass.D2_OPERATIONAL,
    )
    assert result.passed is True


def test_gate_7_monitoring_no_setup():
    """Gate 7 should warn if monitoring not set up."""
    result = gate_7_monitoring(
        monitoring_metric=False,
        review_date=False,
        rollback_trigger=False,
        decision_class=DecisionClass.D2_OPERATIONAL,
    )
    assert result.passed is False or "monitor" in result.reason.lower()


# ─────────────────────────────────────────────
# ESCALATION TIER ROUTING
# ─────────────────────────────────────────────

def test_determine_escalation_tier_1():
    """Escalation Tier 1 for moderate risk."""
    tier, sla, recipients = determine_escalation_tier(
        decision_class=DecisionClass.D2_OPERATIONAL,
        failed_gates=["gate_2"],
    )
    assert tier == 1
    assert sla == "4 hours"


def test_determine_escalation_tier_2():
    """Escalation Tier 2 for elevated risk."""
    tier, sla, recipients = determine_escalation_tier(
        decision_class=DecisionClass.D3_FINANCIAL,
        failed_gates=["gate_3", "gate_4"],
    )
    assert tier == 2
    assert sla == "1 business day"


def test_determine_escalation_tier_3():
    """Escalation Tier 3 for high-risk decisions."""
    tier, sla, recipients = determine_escalation_tier(
        decision_class=DecisionClass.D5_LEGAL_ETHICAL,
        failed_gates=["gate_1", "gate_5"],
    )
    assert tier == 3
    assert sla == "3 business days"


# ─────────────────────────────────────────────
# POLICY GATING
# ─────────────────────────────────────────────

def test_check_policy_gate_approved_d1():
    """Policy gate should approve D1 auto-execution."""
    result = check_policy_gate(
        decision_class=DecisionClass.D1_REVERSIBLE_TACTICAL,
        authority_ceiling="D1",
    )
    assert result == PolicyGateResult.APPROVED


def test_check_policy_gate_blocked_mandatory_human():
    """Policy gate should block D5/D6 without human approval."""
    result = check_policy_gate(
        decision_class=DecisionClass.D5_LEGAL_ETHICAL,
        authority_ceiling="escalate",
    )
    assert result in (PolicyGateResult.BLOCKED, PolicyGateResult.REQUIRES_HUMAN_REVIEW)


def test_check_policy_gate_requires_review_d3():
    """Policy gate should require human review for D3+."""
    result = check_policy_gate(
        decision_class=DecisionClass.D3_FINANCIAL,
        authority_ceiling="D3",
    )
    assert result in (PolicyGateResult.APPROVED, PolicyGateResult.REQUIRES_HUMAN_REVIEW)


# ─────────────────────────────────────────────
# AUTHORITY CHECKS
# ─────────────────────────────────────────────

def test_check_authority_ai_agent_d1():
    """AI agent should have authority for D1."""
    result = check_authority(
        decision_class=DecisionClass.D1_REVERSIBLE_TACTICAL,
        actor_role="AI_Agent",
        trust_tier=TrustTier.T3_CERTIFIED,
    )
    assert result.can_execute is True


def test_check_authority_ai_agent_d3_denied():
    """AI agent should not have authority for D3."""
    result = check_authority(
        decision_class=DecisionClass.D3_FINANCIAL,
        actor_role="AI_Domain_Agent",
        trust_tier=TrustTier.T2_QUALIFIED,
    )
    assert result.can_execute is False


def test_check_authority_human_executive_d3():
    """Human Executive should have authority for D3."""
    result = check_authority(
        decision_class=DecisionClass.D3_FINANCIAL,
        actor_role="Human_Executive",
        trust_tier=TrustTier.T3_CERTIFIED,
    )
    assert result.can_execute is True


def test_check_authority_insufficient_trust():
    """Should deny execution if trust tier below minimum."""
    result = check_authority(
        decision_class=DecisionClass.D4_STRATEGIC,
        actor_role="Domain_Owner",
        trust_tier=TrustTier.T0_UNQUALIFIED,
    )
    assert result.can_execute is False


def test_check_authority_board_always_authorized():
    """Board should have authority for all decisions."""
    result = check_authority(
        decision_class=DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST,
        actor_role="Human_CEO",
        trust_tier=TrustTier.T1_OBSERVED,
    )
    assert result.can_execute is True


# ─────────────────────────────────────────────
# CONSTANTS VALIDATION
# ─────────────────────────────────────────────

def test_trust_tier_minimums_structure():
    """TRUST_TIER_MINIMUMS should map all decision classes."""
    for cls in DecisionClass:
        assert cls in TRUST_TIER_MINIMUMS
        assert TRUST_TIER_MINIMUMS[cls] in TrustTier


def test_value_thresholds_structure():
    """VALUE_THRESHOLDS should map all decision classes."""
    for cls in DecisionClass:
        assert cls in VALUE_THRESHOLDS
        assert isinstance(VALUE_THRESHOLDS[cls], (int, float))


def test_role_hierarchy_numeric():
    """ROLE_HIERARCHY should have numeric values."""
    for role, level in ROLE_HIERARCHY.items():
        assert isinstance(level, int)
        assert 1 <= level <= 5


def test_auto_execute_reversibility():
    """AUTO_EXECUTE_REVERSIBILITY should contain only R1 and R2."""
    assert ReversibilityTag.R1_EASILY_REVERSIBLE in AUTO_EXECUTE_REVERSIBILITY
    assert ReversibilityTag.R2_MODERATELY_REVERSIBLE in AUTO_EXECUTE_REVERSIBILITY
    assert ReversibilityTag.R3_DIFFICULT_REVERSIBLE not in AUTO_EXECUTE_REVERSIBILITY


def test_mandatory_human_classes():
    """MANDATORY_HUMAN_CLASSES should contain D5 and D6."""
    assert DecisionClass.D5_LEGAL_ETHICAL in MANDATORY_HUMAN_CLASSES
    assert DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST in MANDATORY_HUMAN_CLASSES
