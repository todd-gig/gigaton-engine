"""
Audit Logging Module

Creates structured, timestamped audit records at each pipeline stage.
Produces serializable output for storage, learning loop input, and compliance review.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional
import uuid


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class AuditStage(str, Enum):
    """Pipeline stage for audit logging."""
    VALIDATION = "validation"
    RTQL_PREFILTER = "rtql_prefilter"
    VALUE_ASSESSMENT = "value_assessment"
    TRUST_ASSESSMENT = "trust_assessment"
    ALIGNMENT_CHECK = "alignment_check"
    CERTIFICATION = "certification"
    EXECUTION_AUTHORIZATION = "execution_authorization"
    PRIORITY_SCORING = "priority_scoring"
    EXECUTION = "execution"
    OUTCOME = "outcome"


# ─────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────

@dataclass
class AuditEntry:
    """A single audit log entry."""
    audit_id: str
    decision_id: str
    timestamp: str
    stage: str
    action: str
    details: dict = field(default_factory=dict)
    result: str = "pending"


@dataclass
class AuditTrail:
    """Collection of audit entries for a decision."""
    decision_id: str
    entries: list[AuditEntry] = field(default_factory=list)

    def log_stage(self, stage: str, action: str, details: dict = None,
                 result: str = "completed") -> AuditEntry:
        """Log a stage-specific action."""
        entry = AuditEntry(
            audit_id=f"AUD-{uuid.uuid4().hex[:8].upper()}",
            decision_id=self.decision_id,
            timestamp=datetime.utcnow().isoformat(),
            stage=stage,
            action=action,
            details=details or {},
            result=result,
        )
        self.entries.append(entry)
        return entry

    def log_gate_result(self, gate_name: str, passed: bool, reason: str) -> AuditEntry:
        """Log a gate check result."""
        return self.log_stage(
            stage=AuditStage.EXECUTION_AUTHORIZATION.value,
            action=f"gate_check: {gate_name}",
            details={
                "gate_name": gate_name,
                "passed": passed,
                "reason": reason,
            },
            result="passed" if passed else "failed",
        )

    def log_execution(self, verdict: str, action_steps: list,
                     escalation_tier: Optional[int] = None) -> AuditEntry:
        """Log execution authorization result."""
        return self.log_stage(
            stage=AuditStage.EXECUTION_AUTHORIZATION.value,
            action="run_7_gate_authorization",
            details={
                "verdict": verdict,
                "action_steps": action_steps,
                "escalation_tier": escalation_tier,
            },
            result="authorized" if verdict == "auto_execute" else "escalated",
        )

    def log_outcome(self, outcome_type: str, revenue_impact: float = 0.0,
                   metadata: dict = None) -> AuditEntry:
        """Log a decision outcome."""
        return self.log_stage(
            stage=AuditStage.OUTCOME.value,
            action="record_outcome",
            details={
                "outcome_type": outcome_type,
                "revenue_impact": revenue_impact,
                "metadata": metadata or {},
            },
            result="completed",
        )

    def get_trail(self) -> list[dict]:
        """Return the audit trail as a list of dicts."""
        return [
            {
                "audit_id": e.audit_id,
                "timestamp": e.timestamp,
                "stage": e.stage,
                "action": e.action,
                "result": e.result,
                "details": e.details,
            }
            for e in self.entries
        ]

    def to_dict(self) -> dict:
        """Serialize the entire audit trail."""
        return {
            "decision_id": self.decision_id,
            "entry_count": len(self.entries),
            "entries": self.get_trail(),
        }


# ─────────────────────────────────────────────
# AUDIT LOGGER
# ─────────────────────────────────────────────

class AuditLogger:
    """Factory for creating and managing audit trails."""

    def __init__(self, decision_id: str):
        self.decision_id = decision_id
        self.trail = AuditTrail(decision_id)

    def log_validation(self, errors: list[str]) -> AuditEntry:
        """Log validation stage."""
        return self.trail.log_stage(
            stage=AuditStage.VALIDATION.value,
            action="validate_decision_object",
            details={
                "errors": errors,
                "valid": len(errors) == 0,
                "error_count": len(errors),
            },
            result="passed" if not errors else "failed",
        )

    def log_rtql(self, stage_name: str, trust_multiplier: float,
                write_target: str, passed: bool,
                blocking_reasons: list = None,
                research_actions: list = None) -> AuditEntry:
        """Log RTQL prefilter stage."""
        return self.trail.log_stage(
            stage=AuditStage.RTQL_PREFILTER.value,
            action="classify_input",
            details={
                "stage": stage_name,
                "trust_multiplier": trust_multiplier,
                "write_target": write_target,
                "passed": passed,
                "blocking_reasons": blocking_reasons or [],
                "research_actions": research_actions or [],
            },
            result="passed" if passed else "blocked",
        )

    def log_value_assessment(self, gross_value: int, penalty: int,
                            net_value: int, classification: str) -> AuditEntry:
        """Log value assessment stage."""
        return self.trail.log_stage(
            stage=AuditStage.VALUE_ASSESSMENT.value,
            action="compute_value_scores",
            details={
                "gross_value": gross_value,
                "penalty": penalty,
                "net_value": net_value,
                "classification": classification,
            },
            result="completed",
        )

    def log_trust_assessment(self, tier: str, total: int,
                            demotion_reasons: list = None) -> AuditEntry:
        """Log trust assessment stage."""
        return self.trail.log_stage(
            stage=AuditStage.TRUST_ASSESSMENT.value,
            action="calculate_trust_tier",
            details={
                "trust_tier": tier,
                "trust_total": total,
                "demotion_reasons": demotion_reasons or [],
                "demotion_count": len(demotion_reasons or []),
            },
            result="completed",
        )

    def log_alignment(self, doctrine_alignment: float, ethos_alignment: float,
                     first_principles_alignment: float, composite: float,
                     anti_patterns: list = None, has_violations: bool = False) -> AuditEntry:
        """Log alignment check stage."""
        return self.trail.log_stage(
            stage=AuditStage.ALIGNMENT_CHECK.value,
            action="check_alignment",
            details={
                "doctrine_alignment": doctrine_alignment,
                "ethos_alignment": ethos_alignment,
                "first_principles_alignment": first_principles_alignment,
                "composite": round(composite, 3),
                "anti_pattern_flags": anti_patterns or [],
                "has_violations": has_violations,
            },
            result="passed" if not has_violations else "failed",
        )

    def log_certificate_chain(self, qc_status: str, vc_status: str,
                             tc_status: str, ec_status: str,
                             chain_complete: bool) -> AuditEntry:
        """Log certificate chain stage."""
        return self.trail.log_stage(
            stage=AuditStage.CERTIFICATION.value,
            action="build_certificate_chain",
            details={
                "QC": qc_status,
                "VC": vc_status,
                "TC": tc_status,
                "EC": ec_status,
                "chain_complete": chain_complete,
            },
            result="complete" if chain_complete else "incomplete",
        )

    def log_gate_check(self, gate_name: str, passed: bool, reason: str) -> AuditEntry:
        """Log individual gate check."""
        return self.trail.log_gate_result(gate_name, passed, reason)

    def log_authorization(self, verdict: str, action_steps: list,
                         escalation_tier: Optional[int] = None,
                         gate_results: dict = None) -> AuditEntry:
        """Log execution authorization."""
        entry = self.trail.log_execution(verdict, action_steps, escalation_tier)
        if gate_results:
            entry.details["gate_results"] = gate_results
        return entry

    def log_priority_score(self, score: float, components: dict = None) -> AuditEntry:
        """Log priority scoring."""
        return self.trail.log_stage(
            stage=AuditStage.PRIORITY_SCORING.value,
            action="calculate_priority_score",
            details={
                "priority_score": score,
                "components": components or {},
            },
            result="completed",
        )

    def log_execution_action(self, action_type: str, entity_id: str,
                            payload: dict = None, result: str = "pending") -> AuditEntry:
        """Log action execution."""
        return self.trail.log_stage(
            stage=AuditStage.EXECUTION.value,
            action=f"execute_{action_type}",
            details={
                "action_type": action_type,
                "entity_id": entity_id,
                "payload": payload or {},
            },
            result=result,
        )

    def log_outcome(self, outcome_type: str, entity_id: str,
                   revenue_impact: float = 0.0,
                   time_to_outcome_hours: float = 0.0) -> AuditEntry:
        """Log outcome event."""
        return self.trail.log_stage(
            stage=AuditStage.OUTCOME.value,
            action="record_outcome",
            details={
                "outcome_type": outcome_type,
                "entity_id": entity_id,
                "revenue_impact": revenue_impact,
                "time_to_outcome_hours": time_to_outcome_hours,
            },
            result="completed",
        )

    def get_trail(self) -> AuditTrail:
        """Get the audit trail object."""
        return self.trail

    def to_dict(self) -> dict:
        """Serialize to dict."""
        return self.trail.to_dict()
