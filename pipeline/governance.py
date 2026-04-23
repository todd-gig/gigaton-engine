"""
Unified Governance Module

Combines 7-gate authorization system + SIE authority tiers + execution gates.
Implements decision classification, trust tier mapping, policy gating, and
role-based authority routing.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class DecisionClass(str, Enum):
    """Decision classification by reversibility and impact."""
    D0_INFORMATIONAL = "D0"
    D1_REVERSIBLE_TACTICAL = "D1"
    D2_OPERATIONAL = "D2"
    D3_FINANCIAL = "D3"
    D4_STRATEGIC = "D4"
    D5_LEGAL_ETHICAL = "D5"
    D6_IRREVERSIBLE_HIGH_BLAST = "D6"


class ReversibilityTag(str, Enum):
    """Reversibility classification."""
    R1_EASILY_REVERSIBLE = "R1"
    R2_MODERATELY_REVERSIBLE = "R2"
    R3_DIFFICULT_REVERSIBLE = "R3"
    R4_PERMANENT = "R4"


class TrustTier(str, Enum):
    """Trust tier classification."""
    T0_UNQUALIFIED = "T0"
    T1_OBSERVED = "T1"
    T2_QUALIFIED = "T2"
    T3_CERTIFIED = "T3"
    T4_DELEGATED = "T4"


class PolicyGateResult(str, Enum):
    """Policy gate evaluation result."""
    APPROVED = "approved"
    BLOCKED = "blocked"
    REQUIRES_HUMAN_REVIEW = "requires_human_review"


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

TRUST_TIER_MINIMUMS = {
    DecisionClass.D0_INFORMATIONAL: TrustTier.T0_UNQUALIFIED,
    DecisionClass.D1_REVERSIBLE_TACTICAL: TrustTier.T3_CERTIFIED,
    DecisionClass.D2_OPERATIONAL: TrustTier.T2_QUALIFIED,
    DecisionClass.D3_FINANCIAL: TrustTier.T3_CERTIFIED,
    DecisionClass.D4_STRATEGIC: TrustTier.T3_CERTIFIED,
    DecisionClass.D5_LEGAL_ETHICAL: TrustTier.T4_DELEGATED,
    DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST: TrustTier.T4_DELEGATED,
}

VALUE_THRESHOLDS = {
    DecisionClass.D0_INFORMATIONAL: 0,
    DecisionClass.D1_REVERSIBLE_TACTICAL: 8,
    DecisionClass.D2_OPERATIONAL: 12,
    DecisionClass.D3_FINANCIAL: 16,
    DecisionClass.D4_STRATEGIC: 20,
    DecisionClass.D5_LEGAL_ETHICAL: 20,
    DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST: 24,
}

AUTO_EXECUTE_REVERSIBILITY = {
    ReversibilityTag.R1_EASILY_REVERSIBLE,
    ReversibilityTag.R2_MODERATELY_REVERSIBLE,
}

MANDATORY_HUMAN_CLASSES = {
    DecisionClass.D5_LEGAL_ETHICAL,
    DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST,
}

AUTO_ELIGIBLE_CLASSES = {
    DecisionClass.D0_INFORMATIONAL,
    DecisionClass.D1_REVERSIBLE_TACTICAL,
}

D2_AUTO_ELIGIBLE = DecisionClass.D2_OPERATIONAL

TIER_ORDER = {
    TrustTier.T0_UNQUALIFIED: 0,
    TrustTier.T1_OBSERVED: 1,
    TrustTier.T2_QUALIFIED: 2,
    TrustTier.T3_CERTIFIED: 3,
    TrustTier.T4_DELEGATED: 4,
}

ROLE_HIERARCHY = {
    "AI_Agent": 1,
    "Domain_Owner": 2,
    "Human_Executive": 3,
    "Human_CEO": 4,
    "Board": 5,
}


# ─────────────────────────────────────────────
# DATACLASSES
# ─────────────────────────────────────────────

@dataclass
class GateCheckResult:
    """Result of a single gate check."""
    gate_name: str
    passed: bool
    reason: str


@dataclass
class AuthorityCheckResult:
    """Result of authority validation."""
    can_execute: bool
    required_executor: str
    required_approval: str
    min_trust: str
    actor_sufficient: bool
    trust_sufficient: bool
    approval_required: bool
    reason: str


@dataclass
class GovernanceResult:
    """Complete governance evaluation result."""
    decision_id: str
    decision_class: DecisionClass
    trust_tier: TrustTier
    net_value: int
    gate_results: dict = field(default_factory=dict)
    policy_gate_result: PolicyGateResult = PolicyGateResult.APPROVED
    authority_check: Optional[AuthorityCheckResult] = None
    blocking_gates: list = field(default_factory=list)
    escalation_tier: Optional[int] = None
    escalation_sla: Optional[str] = None
    escalation_recipients: list = field(default_factory=list)


# ─────────────────────────────────────────────
# UTILITY FUNCTIONS
# ─────────────────────────────────────────────

def _tier_gte(actual: TrustTier, minimum: TrustTier) -> bool:
    """Check if actual trust tier meets or exceeds minimum."""
    return TIER_ORDER[actual] >= TIER_ORDER[minimum]


def _role_gte(actor_role: str, required_role: str) -> bool:
    """Check if actor role meets or exceeds required role."""
    return ROLE_HIERARCHY.get(actor_role, 0) >= ROLE_HIERARCHY.get(required_role, 0)


# ─────────────────────────────────────────────
# GATE CHECKS
# ─────────────────────────────────────────────

def gate_1_doctrine(doctrine_alignment: float, anti_patterns: list,
                    ethical_misalignment: float) -> GateCheckResult:
    """Gate 1: No non-negotiable doctrine violations."""
    if doctrine_alignment < 0.3:
        return GateCheckResult(
            "gate_1_doctrine", False,
            f"Doctrine alignment {doctrine_alignment} below 0.3 minimum"
        )

    critical_patterns = {
        "optics_over_substance",
        "automation_without_human_override",
        "ethical_misalignment_above_threshold",
    }
    violations = critical_patterns.intersection(set(anti_patterns))
    if violations:
        return GateCheckResult(
            "gate_1_doctrine", False,
            f"Critical anti-pattern violations: {', '.join(violations)}"
        )

    if ethical_misalignment > 3:
        return GateCheckResult(
            "gate_1_doctrine", False,
            f"Ethical misalignment score {ethical_misalignment} exceeds threshold 3"
        )

    return GateCheckResult("gate_1_doctrine", True, "Doctrine check passed")


def gate_2_trust_tier(decision_class: DecisionClass, trust_tier: TrustTier) -> GateCheckResult:
    """Gate 2: Trust tier meets decision class minimum."""
    minimum = TRUST_TIER_MINIMUMS[decision_class]
    if _tier_gte(trust_tier, minimum):
        return GateCheckResult(
            "gate_2_trust_tier", True,
            f"Trust tier {trust_tier.value} meets minimum {minimum.value} for {decision_class.value}"
        )
    return GateCheckResult(
        "gate_2_trust_tier", False,
        f"Trust tier {trust_tier.value} below minimum {minimum.value} for {decision_class.value}"
    )


def gate_3_value_threshold(decision_class: DecisionClass, net_value: int) -> GateCheckResult:
    """Gate 3: Net value score meets decision class threshold."""
    threshold = VALUE_THRESHOLDS[decision_class]
    if net_value >= threshold:
        return GateCheckResult(
            "gate_3_value_threshold", True,
            f"Net value {net_value} meets threshold {threshold} for {decision_class.value}"
        )
    return GateCheckResult(
        "gate_3_value_threshold", False,
        f"Net value {net_value} below threshold {threshold} for {decision_class.value}"
    )


def gate_4_reversibility(decision_class: DecisionClass,
                        reversibility: ReversibilityTag) -> GateCheckResult:
    """Gate 4: Reversibility tag compatible with autonomous execution."""
    if decision_class in MANDATORY_HUMAN_CLASSES:
        return GateCheckResult(
            "gate_4_reversibility", False,
            f"Decision class {decision_class.value} requires mandatory human approval"
        )

    if reversibility in AUTO_EXECUTE_REVERSIBILITY:
        return GateCheckResult(
            "gate_4_reversibility", True,
            f"Reversibility {reversibility.value} is within auto-execute bounds"
        )

    return GateCheckResult(
        "gate_4_reversibility", False,
        f"Reversibility {reversibility.value} too high for autonomous execution"
    )


def gate_5_risk_containment(downside_risk: float, uncertainty: float,
                           reversibility: ReversibilityTag,
                           rollback_trigger: bool,
                           monitoring_metric: bool) -> GateCheckResult:
    """Gate 5: Downside bounded and rollback mechanism exists."""
    issues = []

    if downside_risk > 3:
        issues.append(f"Downside risk {downside_risk} exceeds containment threshold 3")

    if uncertainty > 3:
        issues.append(f"Uncertainty {uncertainty} exceeds containment threshold 3")

    if reversibility.value in ("R3", "R4") and not rollback_trigger:
        issues.append("No rollback trigger defined for high-irreversibility decision")

    if not monitoring_metric:
        issues.append("No monitoring metric defined")

    if issues:
        return GateCheckResult("gate_5_risk_containment", False, "; ".join(issues))

    return GateCheckResult(
        "gate_5_risk_containment", True,
        "Risk containment adequate — downside bounded, monitoring in place"
    )


def gate_6_approval_routing(decision_class: DecisionClass, trust_tier: TrustTier,
                           required_approvals: list, owner: str) -> GateCheckResult:
    """Gate 6: Required approvals present or decision class doesn't require them."""
    # D0 and D1 with sufficient trust need no approvals
    if decision_class in AUTO_ELIGIBLE_CLASSES:
        if decision_class == DecisionClass.D0_INFORMATIONAL:
            return GateCheckResult("gate_6_approval_routing", True, "D0 informational — no approval required")
        if _tier_gte(trust_tier, TrustTier.T3_CERTIFIED):
            return GateCheckResult(
                "gate_6_approval_routing", True,
                f"D1 with trust {trust_tier.value} — auto-approved"
            )

    # D2 requires owner approval unless T3+ with approved recurrence
    if decision_class == D2_AUTO_ELIGIBLE:
        if _tier_gte(trust_tier, TrustTier.T3_CERTIFIED):
            if owner in required_approvals:
                return GateCheckResult(
                    "gate_6_approval_routing", True,
                    "D2 with T3+ trust and owner approval — auto-approved"
                )
            elif not required_approvals:
                return GateCheckResult(
                    "gate_6_approval_routing", False,
                    "D2 requires at least owner approval"
                )
        return GateCheckResult(
            "gate_6_approval_routing", False,
            f"D2 with trust {trust_tier.value} requires human approval"
        )

    # D3-D6 always require human approval
    if decision_class in MANDATORY_HUMAN_CLASSES:
        if required_approvals:
            return GateCheckResult(
                "gate_6_approval_routing", True,
                f"Required approvals listed: {', '.join(required_approvals)}"
            )
        return GateCheckResult(
            "gate_6_approval_routing", False,
            f"{decision_class.value} requires mandatory human approval — none listed"
        )

    # D3, D4 — executive approval required
    if required_approvals:
        return GateCheckResult(
            "gate_6_approval_routing", True,
            f"Approvals present for {decision_class.value}: {', '.join(required_approvals)}"
        )
    return GateCheckResult(
        "gate_6_approval_routing", False,
        f"{decision_class.value} requires human executive approval — none listed"
    )


def gate_7_monitoring(monitoring_metric: bool, review_date: bool,
                     rollback_trigger: bool,
                     decision_class: DecisionClass) -> GateCheckResult:
    """Gate 7: Monitoring hooks and review date exist."""
    issues = []

    if not monitoring_metric:
        issues.append("No monitoring metric defined")

    if not review_date:
        issues.append("No review date set")

    if not rollback_trigger and decision_class.value not in ("D0",):
        issues.append("No rollback trigger defined")

    if issues:
        return GateCheckResult("gate_7_monitoring", False, "; ".join(issues))

    return GateCheckResult("gate_7_monitoring", True, "Monitoring configuration complete")


# ─────────────────────────────────────────────
# ESCALATION ROUTING
# ─────────────────────────────────────────────

def determine_escalation_tier(decision_class: DecisionClass,
                             failed_gates: list) -> tuple[int, str, list]:
    """
    Determine escalation tier based on decision class and failure severity.

    Returns (tier, sla, recipients_roles).

    Tier 1: 4hr SLA — owner + stakeholder
    Tier 2: 1-day SLA — functional leader + exec
    Tier 3: 3-day SLA — C-level + board
    """
    # Tier 3: irreversible/high-blast or legal/ethical
    if decision_class in (
        DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST,
        DecisionClass.D5_LEGAL_ETHICAL
    ):
        return 3, "3 business days", ["c_level", "board"]

    # Tier 2: strategic or financial
    if decision_class in (
        DecisionClass.D4_STRATEGIC,
        DecisionClass.D3_FINANCIAL
    ):
        return 2, "1 business day", ["functional_leader", "executive"]

    # Tier 2 if doctrine or trust gates failed
    if any(g in failed_gates for g in ["gate_1_doctrine", "gate_2_trust_tier"]):
        return 2, "1 business day", ["functional_leader", "executive"]

    # Tier 1: operational or tactical
    return 1, "4 hours", ["owner", "stakeholder"]


# ─────────────────────────────────────────────
# POLICY GATE
# ─────────────────────────────────────────────

def check_policy_gate(decision_class: DecisionClass,
                     authority_ceiling: str) -> PolicyGateResult:
    """
    Check if decision class is authorized by policy.

    Authority ceiling recommendations:
    - D1: send email
    - D2: create follow-up task / scheduling prompt
    - D3+: human approval required
    """
    authority_map = {
        "D1": {DecisionClass.D0_INFORMATIONAL, DecisionClass.D1_REVERSIBLE_TACTICAL},
        "D2": {
            DecisionClass.D0_INFORMATIONAL, DecisionClass.D1_REVERSIBLE_TACTICAL,
            DecisionClass.D2_OPERATIONAL
        },
        "D3": {
            DecisionClass.D0_INFORMATIONAL, DecisionClass.D1_REVERSIBLE_TACTICAL,
            DecisionClass.D2_OPERATIONAL, DecisionClass.D3_FINANCIAL
        },
        "D4": {
            DecisionClass.D0_INFORMATIONAL, DecisionClass.D1_REVERSIBLE_TACTICAL,
            DecisionClass.D2_OPERATIONAL, DecisionClass.D3_FINANCIAL,
            DecisionClass.D4_STRATEGIC
        },
        "human": set(DecisionClass),  # All allowed if human approval
    }

    allowed = authority_map.get(authority_ceiling, set())
    if decision_class in allowed:
        return PolicyGateResult.APPROVED
    elif authority_ceiling == "human" or decision_class in MANDATORY_HUMAN_CLASSES:
        return PolicyGateResult.REQUIRES_HUMAN_REVIEW
    else:
        return PolicyGateResult.BLOCKED


# ─────────────────────────────────────────────
# AUTHORITY CHECK
# ─────────────────────────────────────────────

def check_authority(decision_class: DecisionClass, actor_role: str,
                   trust_tier: TrustTier) -> AuthorityCheckResult:
    """
    Check if actor can execute this decision class at current trust tier.

    Authority matrix from SIE:
    D1: AI_Agent at T3+
    D2: Domain_Owner at T3+
    D3: Domain_Owner at T2+
    D4: Human_Executive at T2+
    D5: Human_Executive at T1+
    D6: Human_CEO at T1+
    """
    authority_matrix = {
        DecisionClass.D0_INFORMATIONAL: ("AI_Agent", "T0"),
        DecisionClass.D1_REVERSIBLE_TACTICAL: ("AI_Agent", "T3"),
        DecisionClass.D2_OPERATIONAL: ("Domain_Owner", "T3"),
        DecisionClass.D3_FINANCIAL: ("Domain_Owner", "T2"),
        DecisionClass.D4_STRATEGIC: ("Human_Executive", "T2"),
        DecisionClass.D5_LEGAL_ETHICAL: ("Human_Executive", "T1"),
        DecisionClass.D6_IRREVERSIBLE_HIGH_BLAST: ("Human_CEO", "T1"),
    }

    required_executor, min_trust_str = authority_matrix.get(
        decision_class,
        ("Human_CEO", "T4")
    )

    min_trust = TrustTier(min_trust_str)
    trust_sufficient = _tier_gte(trust_tier, min_trust)
    actor_sufficient = _role_gte(actor_role, required_executor)
    can_execute = trust_sufficient and actor_sufficient
    approval_required = decision_class in MANDATORY_HUMAN_CLASSES

    if not trust_sufficient:
        reason = f"Trust tier {trust_tier.value} below minimum {min_trust.value} for {decision_class.value}"
    elif not actor_sufficient:
        reason = f"Actor role '{actor_role}' insufficient — {decision_class.value} requires '{required_executor}' or higher"
    elif approval_required:
        reason = f"Execution allowed but requires approval from C-level"
        can_execute = True  # Authority check passes; approval is routing concern
    else:
        reason = f"Actor '{actor_role}' authorized to execute {decision_class.value} at {trust_tier.value}"

    return AuthorityCheckResult(
        can_execute=can_execute,
        required_executor=required_executor,
        required_approval="Human_CEO" if approval_required else "none",
        min_trust=min_trust.value,
        actor_sufficient=actor_sufficient,
        trust_sufficient=trust_sufficient,
        approval_required=approval_required,
        reason=reason,
    )
