"""
Decision Object Model

Defines the 22-field normalized decision contract, value/trust/alignment scoring,
RTQL classification, and supporting enumerations for the decision engine.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List
from datetime import datetime


# ─────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────

class DecisionClass(str, Enum):
    """Decision classification by scope and authority."""
    D1 = "D1"  # Individual tactical
    D2 = "D2"  # Team tactical
    D3 = "D3"  # Department operational
    D4 = "D4"  # Cross-functional operational
    D5 = "D5"  # Strategic
    D6 = "D6"  # Executive strategic


class Reversibility(str, Enum):
    """Decision reversibility classification."""
    R1 = "R1"  # Fully reversible
    R2 = "R2"  # Mostly reversible
    R3 = "R3"  # Partially reversible
    R4 = "R4"  # Irreversible


class TrustTier(str, Enum):
    """Trust tier classification based on trust score."""
    T0_UNQUALIFIED = "T0_UNQUALIFIED"  # total < 10
    T1_OBSERVED = "T1_OBSERVED"        # 10 <= total < 17
    T2_QUALIFIED = "T2_QUALIFIED"      # 17 <= total < 24
    T3_CERTIFIED = "T3_CERTIFIED"      # 24 <= total < 30
    T4_DELEGATED = "T4_DELEGATED"      # total >= 30


class RTQLStage(str, Enum):
    """RTQL (Recursive Trust Qualification Loop) classification stage."""
    NOISE = "noise"
    WEAK_SIGNAL = "weak_signal"
    ECHO_SIGNAL = "echo_signal"
    QUALIFIED = "qualified"
    CERTIFICATION_GAP = "certification_gap"
    CERTIFIED = "certified"
    RESEARCH_GRADE = "research_grade"
    FIRST_PRINCIPLES_CANDIDATE = "first_principles_candidate"
    AXIOM_CANDIDATE = "axiom_candidate"


class WriteTarget(str, Enum):
    """Canonical write target destination based on RTQL stage."""
    QUARANTINE = "quarantine"
    STAGING = "staging"
    CANDIDATE_REGISTRY = "candidate_registry"
    OPERATIONAL_REGISTRY = "operational_registry"
    INSIGHT_REGISTRY = "insight_registry"
    PRINCIPLES_REGISTRY = "principles_registry"
    AXIOM_REVIEW_QUEUE = "axiom_review_queue"


class CertificateType(str, Enum):
    """Certificate types for decision validation."""
    QC = "QC"  # Qualification Certificate
    VC = "VC"  # Verification Certificate
    TC = "TC"  # Trust Certificate
    EC = "EC"  # Execution Certificate


class CertificateStatus(str, Enum):
    """Certificate status."""
    PENDING = "pending"
    ISSUED = "issued"
    REVOKED = "revoked"
    EXPIRED = "expired"


# ─────────────────────────────────────────────
# SCORING MODELS
# ─────────────────────────────────────────────

@dataclass
class ValueScores:
    """
    Value scoring across 8 positive dimensions and 4 penalty dimensions.
    All scores are 0-5 scale.
    """
    # Positive dimensions (value drivers)
    revenue_impact: int = 0  # 0-5
    cost_efficiency: int = 0  # 0-5
    time_leverage: int = 0  # 0-5
    strategic_alignment: int = 0  # 0-5
    customer_human_benefit: int = 0  # 0-5
    knowledge_asset_creation: int = 0  # 0-5
    compounding_potential: int = 0  # 0-5
    reversibility: int = 0  # 0-5

    # Penalty dimensions (risk/drag factors)
    downside_risk: int = 0  # 0-5
    execution_drag: int = 0  # 0-5
    uncertainty: int = 0  # 0-5
    ethical_misalignment: int = 0  # 0-5

    def gross_value(self) -> float:
        """Sum of positive dimensions."""
        return float(
            self.revenue_impact
            + self.cost_efficiency
            + self.time_leverage
            + self.strategic_alignment
            + self.customer_human_benefit
            + self.knowledge_asset_creation
            + self.compounding_potential
            + self.reversibility
        )

    def penalty(self) -> float:
        """Sum of penalty dimensions."""
        return float(
            self.downside_risk
            + self.execution_drag
            + self.uncertainty
            + self.ethical_misalignment
        )

    def net_value(self) -> float:
        """Gross value minus penalties."""
        return self.gross_value() - self.penalty()

    def value_classification(self) -> str:
        """Classify as high/medium/low based on net value."""
        net = self.net_value()
        if net >= 20:
            return "high"
        elif net >= 10:
            return "medium"
        else:
            return "low"


@dataclass
class TrustScores:
    """
    Trust scoring across 7 independent input dimensions.
    All scores are 0-5 scale.
    """
    evidence_quality: int = 0  # 0-5
    logic_integrity: int = 0  # 0-5
    outcome_history: int = 0  # 0-5
    context_fit: int = 0  # 0-5
    stakeholder_clarity: int = 0  # 0-5
    risk_containment: int = 0  # 0-5
    auditability: int = 0  # 0-5

    def total(self) -> int:
        """Sum of all 7 trust dimensions."""
        return (
            self.evidence_quality
            + self.logic_integrity
            + self.outcome_history
            + self.context_fit
            + self.stakeholder_clarity
            + self.risk_containment
            + self.auditability
        )

    def average(self) -> float:
        """Average of all 7 trust dimensions."""
        return self.total() / 7.0


@dataclass
class AlignmentScores:
    """
    Alignment assessment against doctrine, ethos, and first principles.
    All scores are 0-1 scale.
    """
    doctrine_alignment: float = 0.0  # 0-1
    ethos_alignment: float = 0.0  # 0-1
    first_principles_alignment: float = 0.0  # 0-1
    anti_pattern_flags: List[str] = field(default_factory=list)

    def composite(self) -> float:
        """Weighted composite: doctrine 0.4 + ethos 0.3 + first_principles 0.3."""
        return (
            self.doctrine_alignment * 0.4
            + self.ethos_alignment * 0.3
            + self.first_principles_alignment * 0.3
        )


@dataclass
class RTQLScores:
    """
    RTQL (Recursive Trust Qualification Loop) scoring across 7 trust dimensions.
    Uses smooth scoring: {0, 1, 2, 3, 4, 5, 6, 8, 10, 12}.
    """
    source_integrity: int = 0
    exposure_count: int = 0
    independence: int = 0
    explainability: int = 0
    replicability: int = 0
    adversarial_robustness: int = 0
    novelty_yield: int = 0

    ALLOWED_SCORES = {0, 1, 2, 3, 4, 5, 6, 8, 10, 12}

    def __post_init__(self):
        """Validate all scores are in allowed set."""
        dims = [
            "source_integrity",
            "exposure_count",
            "independence",
            "explainability",
            "replicability",
            "adversarial_robustness",
            "novelty_yield",
        ]
        for dim in dims:
            val = getattr(self, dim)
            if val not in self.ALLOWED_SCORES:
                raise ValueError(
                    f"Dimension '{dim}' has value {val} which is not in "
                    f"allowed scores {sorted(self.ALLOWED_SCORES)}"
                )


@dataclass
class CausalChecks:
    """Causal mechanism validation checks for first-principles candidates."""
    reveals_causal_mechanism: bool = False
    is_irreducible: bool = False
    survives_authority_removal: bool = False
    survives_context_shift: bool = False


@dataclass
class RTQLInput:
    """Input record for RTQL classification."""
    scores: RTQLScores
    causal_checks: CausalChecks
    is_identifiable: bool = True
    has_provenance: bool = True
    record_id: Optional[str] = None
    label: Optional[str] = None
    raw_value: float = 0.0


@dataclass
class RTQLResult:
    """Result of RTQL classification."""
    stage: RTQLStage = RTQLStage.NOISE
    passed: bool = False
    blocking_reasons: List[str] = field(default_factory=list)
    trust_multiplier: float = 0.0
    write_target: WriteTarget = WriteTarget.QUARANTINE
    research_actions: List[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# DECISION OBJECT (22 FIELDS)
# ─────────────────────────────────────────────

@dataclass
class DecisionObject:
    """
    Normalized decision contract with 22 fields covering identity,
    intent, value, trust, alignment, and execution context.
    """

    # --- Identity (3 fields) ---
    decision_id: str
    title: str
    decision_class: DecisionClass

    # --- Intent & Authority (2 fields) ---
    owner: Optional[str] = None
    time_horizon: Optional[str] = None

    # --- Decision Classification (2 fields) ---
    reversibility: Reversibility = Reversibility.R2
    problem_statement: str = ""

    # --- Decision Context (3 fields) ---
    requested_action: str = ""
    context_summary: str = ""
    stakeholders: List[str] = field(default_factory=list)

    # --- Constraints & Assumptions (3 fields) ---
    constraints: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)

    # --- Scoring (3 fields) ---
    value_scores: ValueScores = field(default_factory=ValueScores)
    trust_scores: TrustScores = field(default_factory=TrustScores)
    alignment_scores: AlignmentScores = field(default_factory=AlignmentScores)

    # --- RTQL Input (1 field) ---
    rtql_input: Optional[RTQLInput] = None

    # --- Evidence & Execution (3 fields) ---
    evidence_refs: List[str] = field(default_factory=list)
    required_approvals: List[str] = field(default_factory=list)
    execution_plan: str = ""

    # --- Monitoring & Rollback (2 fields) ---
    monitoring_metric: str = ""
    rollback_trigger: Optional[str] = None

    # --- Metadata (1 field) ---
    review_date: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    # --- State Management (3 fields) ---
    current_state: str = "draft"
    has_missing_data: bool = False
    ethical_conflict: bool = False

    # --- Actor Context (1 field) ---
    actor_role: Optional[str] = None
