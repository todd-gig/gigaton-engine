"""
Test suite for audit.py - Structured audit logging and trail management.
"""

import pytest
from datetime import datetime
from pipeline.audit import (
    AuditStage,
    AuditEntry,
    AuditTrail,
    AuditLogger,
)


# ─────────────────────────────────────────────
# AUDIT ENTRY CREATION
# ─────────────────────────────────────────────

def test_audit_entry_creation():
    """Should create audit entry with all required fields."""
    entry = AuditEntry(
        audit_id="AUD-TEST1234",
        decision_id="DEC-001",
        timestamp="2026-04-23T10:30:00",
        stage="validation",
        action="validate_decision_object",
        details={"errors": [], "valid": True},
        result="passed",
    )
    assert entry.audit_id == "AUD-TEST1234"
    assert entry.decision_id == "DEC-001"
    assert entry.stage == "validation"
    assert entry.result == "passed"


def test_audit_entry_defaults():
    """Audit entry should have default values for optional fields."""
    entry = AuditEntry(
        audit_id="AUD-TEST5678",
        decision_id="DEC-002",
        timestamp="2026-04-23T10:30:00",
        stage="validation",
        action="test",
    )
    assert entry.details == {}
    assert entry.result == "pending"


# ─────────────────────────────────────────────
# AUDIT TRAIL LOGGING
# ─────────────────────────────────────────────

def test_audit_trail_creation():
    """Should create audit trail with decision_id."""
    trail = AuditTrail(decision_id="DEC-003")
    assert trail.decision_id == "DEC-003"
    assert trail.entries == []


def test_audit_trail_log_stage():
    """Should log a stage with entry creation."""
    trail = AuditTrail(decision_id="DEC-004")
    entry = trail.log_stage(
        stage="validation",
        action="validate",
        details={"test": True},
        result="passed",
    )
    assert entry is not None
    assert entry.stage == "validation"
    assert entry.action == "validate"
    assert len(trail.entries) == 1


def test_audit_trail_log_gate_result():
    """Should log gate check result with proper details."""
    trail = AuditTrail(decision_id="DEC-005")
    entry = trail.log_gate_result(
        gate_name="doctrine",
        passed=True,
        reason="Alignment sufficient",
    )
    assert entry.action == "gate_check: doctrine"
    assert entry.details["gate_name"] == "doctrine"
    assert entry.details["passed"] is True
    assert entry.result == "passed"


def test_audit_trail_log_execution():
    """Should log execution authorization with verdict."""
    trail = AuditTrail(decision_id="DEC-006")
    entry = trail.log_execution(
        verdict="auto_execute",
        action_steps=["step1", "step2"],
        escalation_tier=None,
    )
    assert entry.details["verdict"] == "auto_execute"
    assert entry.details["action_steps"] == ["step1", "step2"]
    assert entry.result == "authorized"


def test_audit_trail_log_execution_escalated():
    """Should mark execution as escalated for non-auto verdicts."""
    trail = AuditTrail(decision_id="DEC-007")
    entry = trail.log_execution(
        verdict="escalate_tier_1",
        action_steps=["notify"],
        escalation_tier=1,
    )
    assert entry.result == "escalated"


def test_audit_trail_log_outcome():
    """Should log outcome event with revenue impact."""
    trail = AuditTrail(decision_id="DEC-008")
    entry = trail.log_outcome(
        outcome_type="reply_received",
        revenue_impact=5000.0,
        metadata={"source": "email"},
    )
    assert entry.stage == AuditStage.OUTCOME.value
    assert entry.details["outcome_type"] == "reply_received"
    assert entry.details["revenue_impact"] == 5000.0


def test_audit_trail_get_trail():
    """Should return trail as list of dicts."""
    trail = AuditTrail(decision_id="DEC-009")
    trail.log_stage("validation", "test", result="passed")
    trail.log_stage("trust", "assess", result="passed")

    trail_list = trail.get_trail()
    assert len(trail_list) == 2
    assert all(isinstance(item, dict) for item in trail_list)
    assert "audit_id" in trail_list[0]
    assert "timestamp" in trail_list[0]


def test_audit_trail_to_dict():
    """Should serialize entire trail to dict."""
    trail = AuditTrail(decision_id="DEC-010")
    trail.log_stage("validation", "test")
    trail.log_stage("trust", "assess")

    trail_dict = trail.to_dict()
    assert trail_dict["decision_id"] == "DEC-010"
    assert trail_dict["entry_count"] == 2
    assert len(trail_dict["entries"]) == 2


# ─────────────────────────────────────────────
# AUDIT LOGGER
# ─────────────────────────────────────────────

def test_audit_logger_creation():
    """Should create audit logger with decision_id."""
    logger = AuditLogger("DEC-011")
    assert logger.decision_id == "DEC-011"
    assert isinstance(logger.trail, AuditTrail)


def test_audit_logger_log_validation():
    """Should log validation stage."""
    logger = AuditLogger("DEC-012")
    entry = logger.log_validation(errors=[])
    assert entry.stage == AuditStage.VALIDATION.value
    assert entry.action == "validate_decision_object"
    assert entry.result == "passed"


def test_audit_logger_log_validation_with_errors():
    """Should mark validation as failed when errors present."""
    logger = AuditLogger("DEC-013")
    entry = logger.log_validation(errors=["error1", "error2"])
    assert entry.result == "failed"
    assert entry.details["error_count"] == 2


def test_audit_logger_log_rtql():
    """Should log RTQL prefilter stage."""
    logger = AuditLogger("DEC-014")
    entry = logger.log_rtql(
        stage_name="email_assessment",
        trust_multiplier=1.2,
        write_target="send_email",
        passed=True,
    )
    assert entry.stage == AuditStage.RTQL_PREFILTER.value
    assert entry.details["trust_multiplier"] == 1.2
    assert entry.result == "passed"


def test_audit_logger_log_value_assessment():
    """Should log value assessment."""
    logger = AuditLogger("DEC-015")
    entry = logger.log_value_assessment(
        gross_value=100,
        penalty=10,
        net_value=90,
        classification="high",
    )
    assert entry.stage == AuditStage.VALUE_ASSESSMENT.value
    assert entry.details["net_value"] == 90


def test_audit_logger_log_trust_assessment():
    """Should log trust tier assessment."""
    logger = AuditLogger("DEC-016")
    entry = logger.log_trust_assessment(
        tier="T2",
        total=85,
        demotion_reasons=["risk_signal"],
    )
    assert entry.stage == AuditStage.TRUST_ASSESSMENT.value
    assert entry.details["trust_tier"] == "T2"


def test_audit_logger_log_alignment():
    """Should log alignment check."""
    logger = AuditLogger("DEC-017")
    entry = logger.log_alignment(
        doctrine_alignment=0.85,
        ethos_alignment=0.90,
        first_principles_alignment=0.80,
        composite=0.85,
        anti_patterns=[],
        has_violations=False,
    )
    assert entry.stage == AuditStage.ALIGNMENT_CHECK.value
    assert entry.result == "passed"


def test_audit_logger_log_alignment_with_violations():
    """Should mark alignment as failed if violations present."""
    logger = AuditLogger("DEC-018")
    entry = logger.log_alignment(
        doctrine_alignment=0.5,
        ethos_alignment=0.4,
        first_principles_alignment=0.3,
        composite=0.4,
        anti_patterns=["pattern_a"],
        has_violations=True,
    )
    assert entry.result == "failed"


def test_audit_logger_log_certificate_chain():
    """Should log certificate chain completion."""
    logger = AuditLogger("DEC-019")
    entry = logger.log_certificate_chain(
        qc_status="issued",
        vc_status="issued",
        tc_status="issued",
        ec_status="issued",
        chain_complete=True,
    )
    assert entry.stage == AuditStage.CERTIFICATION.value
    assert entry.result == "complete"


def test_audit_logger_log_gate_check():
    """Should log individual gate check."""
    logger = AuditLogger("DEC-020")
    entry = logger.log_gate_check(
        gate_name="trust_tier",
        passed=True,
        reason="Trust sufficient for D2",
    )
    assert entry.action == "gate_check: trust_tier"


def test_audit_logger_log_authorization():
    """Should log execution authorization."""
    logger = AuditLogger("DEC-021")
    entry = logger.log_authorization(
        verdict="auto_execute",
        action_steps=["send_email"],
        escalation_tier=None,
        gate_results={"doctrine": True, "trust": True},
    )
    assert entry.stage == AuditStage.EXECUTION_AUTHORIZATION.value
    assert entry.result == "authorized"


def test_audit_logger_log_priority_score():
    """Should log priority scoring."""
    logger = AuditLogger("DEC-022")
    entry = logger.log_priority_score(
        score=0.75,
        components={"value": 0.3, "silence": 0.45},
    )
    assert entry.stage == AuditStage.PRIORITY_SCORING.value
    assert entry.details["priority_score"] == 0.75


def test_audit_logger_log_execution_action():
    """Should log action execution."""
    logger = AuditLogger("DEC-023")
    entry = logger.log_execution_action(
        action_type="send_email",
        entity_id="lead_123",
        payload={"template": "follow_up"},
        result="executed",
    )
    assert entry.stage == AuditStage.EXECUTION.value
    assert entry.details["action_type"] == "send_email"


def test_audit_logger_log_outcome():
    """Should log outcome event."""
    logger = AuditLogger("DEC-024")
    entry = logger.log_outcome(
        outcome_type="reply_received",
        entity_id="lead_123",
        revenue_impact=10000.0,
        time_to_outcome_hours=24.5,
    )
    assert entry.stage == AuditStage.OUTCOME.value
    assert entry.result == "completed"


def test_audit_logger_get_trail():
    """Should return audit trail object."""
    logger = AuditLogger("DEC-025")
    trail = logger.get_trail()
    assert isinstance(trail, AuditTrail)
    assert trail.decision_id == "DEC-025"


def test_audit_logger_to_dict():
    """Should serialize logger state to dict."""
    logger = AuditLogger("DEC-026")
    logger.log_validation([])
    logger.log_value_assessment(100, 10, 90, "high")

    trail_dict = logger.to_dict()
    assert trail_dict["decision_id"] == "DEC-026"
    assert trail_dict["entry_count"] == 2
    assert len(trail_dict["entries"]) == 2


# ─────────────────────────────────────────────
# AUDIT ID FORMAT VALIDATION
# ─────────────────────────────────────────────

def test_audit_entry_id_format():
    """Audit IDs should follow AUD- prefix pattern."""
    logger = AuditLogger("DEC-027")
    entry = logger.log_validation([])
    assert entry.audit_id.startswith("AUD-")
    assert len(entry.audit_id) == 12  # AUD- + 8 hex chars


def test_timestamp_iso_format():
    """Timestamps should be in ISO format."""
    logger = AuditLogger("DEC-028")
    entry = logger.log_validation([])
    # Should be parseable as ISO timestamp
    dt = datetime.fromisoformat(entry.timestamp)
    assert dt is not None


# ─────────────────────────────────────────────
# AUDIT TRAIL SEQUENCING
# ─────────────────────────────────────────────

def test_audit_entries_preserve_order():
    """Audit entries should be added in order."""
    logger = AuditLogger("DEC-029")
    logger.log_validation([])
    logger.log_rtql("stage1", 1.0, "email", True)
    logger.log_value_assessment(100, 0, 100, "high")

    trail = logger.to_dict()
    assert trail["entries"][0]["stage"] == AuditStage.VALIDATION.value
    assert trail["entries"][1]["stage"] == AuditStage.RTQL_PREFILTER.value
    assert trail["entries"][2]["stage"] == AuditStage.VALUE_ASSESSMENT.value
