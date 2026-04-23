"""Gap Analysis and Value Leakage Engine.

Integrates gap detection, priority scoring, and value leakage detection.

Gap Detection Rules — a gap exists when:
    - actual score < target
    - RTQL trust < required threshold
    - evidence is weak
    - execution maturity is low relative to strategic importance
    - variable has strong leverage but low performance

Gap Formula:
    Gap Score = (Target - Actual) × Strategic Importance × Trust Penalty Modifier

Trust Penalty Modifier:
    1.25 if RTQL < qualified
    1.10 if RTQL = certification_gap
    1.00 if RTQL >= certified

Priority Formula:
    Priority Score = (Gap Score × 0.35) + (Leverage × 0.30) + (Urgency × 0.20) + (Value Impact × 0.15)

Value Leakage Formula:
    Annual_Value_Loss = Sum(AOV × System_Weight × (1 - Dimension_Score) × Days/365 × Cascade_Multiplier)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


# ── RTQL Stage compatibility ──────────────────────────────────────────

class RTQLStage(str, Enum):
    """Backward-compatible RTQL stages for gap analysis."""
    NOISE = "noise"
    WEAK_SIGNAL = "weak_signal"
    ECHO_SIGNAL = "echo_signal"
    QUALIFIED = "qualified"
    CERTIFICATION_GAP = "certification_gap"
    CERTIFIED = "certified"


class EscalationLevel(int, Enum):
    """Value leakage escalation levels."""
    LEVEL_1_AUTOMATED = 1   # real-time, <24h
    LEVEL_2_DEPARTMENT = 2  # 48h response
    LEVEL_3_EXECUTIVE = 3   # 72h response


class LeakageRuleType(str, Enum):
    """Classification of leakage detection rules."""
    SINGLE_DIMENSION = "single_dimension"
    MULTI_CASCADE = "multi_cascade"
    TREND_EARLY_WARNING = "trend_early_warning"
    BOTTLENECK = "bottleneck"


# ── Constants ─────────────────────────────────────────────────────────

CASCADE_MULTIPLIERS = {
    1: 1.0,
    2: 1.3,
    3: 1.7,
    4: 2.2,
}

SYSTEM_WEIGHTS = {
    "People": 0.30,
    "Process": 0.25,
    "Technology": 0.25,
    "Learning": 0.20,
}

# Dependency chains: system A enables system B
DEPENDENCY_CHAIN = {
    "People": ("Process", 0.8),
    "Process": ("Technology", 0.7),
    "Technology": ("Learning", 0.6),
    "Learning": ("People", 0.75),
}


# ── Gap Analysis Data Structures ──────────────────────────────────────

@dataclass
class GapItem:
    """Represents a single gap with priority scoring."""
    category: str = ""
    variable: str = ""
    actual_score: float = 0.0
    target_score: float = 5.0
    strategic_importance: float = 1.0
    rtql_stage: RTQLStage = RTQLStage.QUALIFIED
    leverage_score: float = 0.0
    urgency_score: float = 0.0
    value_matrix_impact: float = 0.0
    gap_score: float = 0.0
    gap_severity_label: str = "minor"
    priority_score: float = 0.0
    trust_penalty: float = 1.0


@dataclass
class ActionItem:
    """Action item derived from gap analysis."""
    category: str = ""
    variable: str = ""
    current_score: float = 0.0
    target_score: float = 0.0
    rtql_stage: str = ""
    gap_severity_label: str = ""
    leverage_score: float = 0.0
    urgency_score: float = 0.0
    priority_score: float = 0.0
    root_cause_hypothesis: str = ""
    required_research: list[str] = field(default_factory=list)
    recommended_action: list[str] = field(default_factory=list)
    expected_impact: dict = field(default_factory=lambda: {
        "revenue": "low", "trust": "low", "speed": "low", "risk_reduction": "low"
    })
    timeline: str = ""
    owner_type: str = ""


# ── Value Leakage Data Structures ─────────────────────────────────────

@dataclass
class LeakageAlert:
    """Alert for detected value leakage."""
    rule_type: LeakageRuleType
    system_name: str
    dimension: str
    estimated_annual_loss: float
    cascade_multiplier: float
    escalation_level: EscalationLevel
    description: str
    severity: str  # critical / warning / info


@dataclass
class LeakageReport:
    """Summary report of value leakage detection."""
    total_estimated_annual_loss: float
    alerts: list[LeakageAlert] = field(default_factory=list)
    systems_in_leakage: int = 0
    cascade_multiplier_applied: float = 1.0


# ── System Score Compatibility ────────────────────────────────────────

@dataclass
class SystemScoreData:
    """Minimal system score data for leakage detection."""
    name: str
    score: float
    dimensions: dict[str, float] = field(default_factory=dict)
    trend: Optional[float] = None


@dataclass
class OVSResultData:
    """Minimal OVS result data for leakage detection."""
    people_score: SystemScoreData = field(default_factory=lambda: SystemScoreData(name="People", score=0.5))
    process_score: SystemScoreData = field(default_factory=lambda: SystemScoreData(name="Process", score=0.5))
    technology_score: SystemScoreData = field(default_factory=lambda: SystemScoreData(name="Technology", score=0.5))
    learning_score: SystemScoreData = field(default_factory=lambda: SystemScoreData(name="Learning", score=0.5))
    composite_ovs: float = 0.5


# ── Gap Analysis Functions ────────────────────────────────────────────

def gap_severity(gap_score: float) -> str:
    """Classify gap severity based on score."""
    if gap_score >= 46:
        return "critical"
    elif gap_score >= 26:
        return "major"
    elif gap_score >= 11:
        return "moderate"
    else:
        return "minor"


def trust_penalty_modifier(rtql_stage: RTQLStage) -> float:
    """
    Calculate trust penalty multiplier.

    Higher modifier = worse penalty for low-trust inputs.
    This amplifies gaps when evidence quality is poor.
    """
    low_trust = {
        RTQLStage.NOISE, RTQLStage.WEAK_SIGNAL,
        RTQLStage.ECHO_SIGNAL, RTQLStage.QUALIFIED,
    }
    if rtql_stage in low_trust:
        return 1.25
    elif rtql_stage == RTQLStage.CERTIFICATION_GAP:
        return 1.10
    else:
        return 1.00


def calculate_gap(
    actual: float,
    target: float,
    strategic_importance: float,
    rtql_stage: RTQLStage,
) -> tuple[float, float, str]:
    """
    Calculate gap score with trust penalty.

    Returns (gap_score, trust_penalty, severity).
    Formula: Gap Score = (Target - Actual) × Strategic Importance × Trust Penalty Modifier
    """
    raw_gap = max(target - actual, 0)
    penalty = trust_penalty_modifier(rtql_stage)
    score = raw_gap * strategic_importance * penalty
    severity = gap_severity(score)
    return round(score, 2), penalty, severity


def calculate_priority(
    gap_score: float,
    leverage_score: float,
    urgency_score: float,
    value_matrix_impact: float,
) -> float:
    """
    Calculate priority score.

    Priority Score = (Gap × 0.35) + (Leverage × 0.30) + (Urgency × 0.20) + (Value Impact × 0.15)
    """
    return round(
        (gap_score * 0.35) +
        (leverage_score * 0.30) +
        (urgency_score * 0.20) +
        (value_matrix_impact * 0.15),
        2
    )


def analyze_gaps(items: list[dict]) -> list[GapItem]:
    """
    Process a batch of gap analysis inputs.

    Each item dict should contain:
        category, variable, actual_score, target_score,
        strategic_importance, rtql_stage (str),
        leverage_score, urgency_score, value_matrix_impact

    Returns list of GapItem sorted by priority_score descending.
    """
    results = []

    for item in items:
        stage_str = item.get("rtql_stage", "qualified")
        try:
            rtql_stage = RTQLStage(stage_str)
        except ValueError:
            rtql_stage = RTQLStage.QUALIFIED

        gap_score, penalty, severity = calculate_gap(
            actual=item.get("actual_score", 0),
            target=item.get("target_score", 5),
            strategic_importance=item.get("strategic_importance", 1.0),
            rtql_stage=rtql_stage,
        )

        priority = calculate_priority(
            gap_score=gap_score,
            leverage_score=item.get("leverage_score", 0),
            urgency_score=item.get("urgency_score", 0),
            value_matrix_impact=item.get("value_matrix_impact", 0),
        )

        results.append(GapItem(
            category=item.get("category", ""),
            variable=item.get("variable", ""),
            actual_score=item.get("actual_score", 0),
            target_score=item.get("target_score", 5),
            strategic_importance=item.get("strategic_importance", 1.0),
            rtql_stage=rtql_stage,
            leverage_score=item.get("leverage_score", 0),
            urgency_score=item.get("urgency_score", 0),
            value_matrix_impact=item.get("value_matrix_impact", 0),
            gap_score=gap_score,
            gap_severity_label=severity,
            priority_score=priority,
            trust_penalty=penalty,
        ))

    # Sort by priority descending
    results.sort(key=lambda x: x.priority_score, reverse=True)
    return results


def generate_action_items(gaps: list[GapItem],
                          min_severity: str = "moderate") -> list[ActionItem]:
    """
    Generate action items for gaps at or above minimum severity.

    Severity order: minor < moderate < major < critical
    """
    severity_order = {"minor": 0, "moderate": 1, "major": 2, "critical": 3}
    min_level = severity_order.get(min_severity, 1)

    actions = []
    for gap in gaps:
        if severity_order.get(gap.gap_severity_label, 0) >= min_level:
            research = []
            if gap.rtql_stage in (RTQLStage.NOISE, RTQLStage.WEAK_SIGNAL):
                research.append("Establish auditable source trail")
                research.append("Seek independent confirmation")
            elif gap.rtql_stage == RTQLStage.ECHO_SIGNAL:
                research.append("Find cross-domain independent validation")
            elif gap.rtql_stage == RTQLStage.CERTIFICATION_GAP:
                research.append("Improve mechanistic explainability")
                research.append("Define replication protocol")

            actions.append(ActionItem(
                category=gap.category,
                variable=gap.variable,
                current_score=gap.actual_score,
                target_score=gap.target_score,
                rtql_stage=gap.rtql_stage.value,
                gap_severity_label=gap.gap_severity_label,
                leverage_score=gap.leverage_score,
                urgency_score=gap.urgency_score,
                priority_score=gap.priority_score,
                required_research=research,
            ))

    return actions


# ── Value Leakage Detection ───────────────────────────────────────────

class ValueLeakageDetector:
    """Detect and quantify value leakage across organizational systems."""

    def __init__(
        self,
        annual_org_value: float = 1_000_000.0,
        single_dim_threshold: float = 0.5,
        system_threshold: float = 0.6,
        trend_decline_threshold: float = -0.05,
    ) -> None:
        self.annual_org_value = annual_org_value
        self.single_dim_threshold = single_dim_threshold
        self.system_threshold = system_threshold
        self.trend_decline_threshold = trend_decline_threshold

    def detect(self, ovs: OVSResultData) -> LeakageReport:
        """
        Detect value leakage using 4 detection rules.

        Rules:
        1. Single-dimension leakage: dimension score below threshold
        2. Multi-cascade: 2+ systems in leakage with compound multiplier
        3. Trend-based: negative trend projected forward
        4. Bottleneck: dependency chain blockage
        """
        alerts: list[LeakageAlert] = []
        scores = {
            "People": ovs.people_score,
            "Process": ovs.process_score,
            "Technology": ovs.technology_score,
            "Learning": ovs.learning_score,
        }

        # Count systems in leakage
        leaking_systems = [
            name for name, s in scores.items() if s.score < self.system_threshold
        ]
        n_leaking = len(leaking_systems)
        cascade_mult = CASCADE_MULTIPLIERS.get(n_leaking, CASCADE_MULTIPLIERS[4])

        # Rule 1: Single-dimension leakage
        for name, sys_score in scores.items():
            for dim_name, dim_val in sys_score.dimensions.items():
                if dim_val < self.single_dim_threshold:
                    loss = (
                        self.annual_org_value
                        * SYSTEM_WEIGHTS[name]
                        * (1 - dim_val)
                        * cascade_mult
                    )
                    alerts.append(LeakageAlert(
                        rule_type=LeakageRuleType.SINGLE_DIMENSION,
                        system_name=name,
                        dimension=dim_name,
                        estimated_annual_loss=round(loss, 2),
                        cascade_multiplier=cascade_mult,
                        escalation_level=EscalationLevel.LEVEL_1_AUTOMATED,
                        description=f"{name}.{dim_name} at {dim_val:.2f} (< {self.single_dim_threshold})",
                        severity="critical" if dim_val < 0.3 else "warning",
                    ))

        # Rule 2: Multi-system cascade
        if n_leaking >= 2:
            total_cascade_loss = sum(
                self.annual_org_value * SYSTEM_WEIGHTS[name] * (1 - scores[name].score) * cascade_mult
                for name in leaking_systems
            )
            alerts.append(LeakageAlert(
                rule_type=LeakageRuleType.MULTI_CASCADE,
                system_name=", ".join(leaking_systems),
                dimension="system_level",
                estimated_annual_loss=round(total_cascade_loss, 2),
                cascade_multiplier=cascade_mult,
                escalation_level=EscalationLevel.LEVEL_2_DEPARTMENT,
                description=f"{n_leaking} systems in cascade leakage: {', '.join(leaking_systems)}",
                severity="critical",
            ))

        # Rule 3: Trend-based early warning
        for name, sys_score in scores.items():
            if sys_score.trend is not None and sys_score.trend < self.trend_decline_threshold:
                projected_loss = (
                    self.annual_org_value
                    * SYSTEM_WEIGHTS[name]
                    * abs(sys_score.trend)
                    * 4  # annualize weekly trend
                )
                alerts.append(LeakageAlert(
                    rule_type=LeakageRuleType.TREND_EARLY_WARNING,
                    system_name=name,
                    dimension="trend",
                    estimated_annual_loss=round(projected_loss, 2),
                    cascade_multiplier=1.0,
                    escalation_level=EscalationLevel.LEVEL_1_AUTOMATED,
                    description=f"{name} declining {sys_score.trend:.1%} WoW",
                    severity="warning",
                ))

        # Rule 4: Bottleneck detection
        for primary, (dependent, dep_weight) in DEPENDENCY_CHAIN.items():
            p_score = scores[primary]
            d_score = scores[dependent]
            if p_score.score >= 0.6 and d_score.score < 0.5:
                bottleneck_loss = (
                    self.annual_org_value
                    * SYSTEM_WEIGHTS[dependent]
                    * (1 - d_score.score)
                    * dep_weight
                )
                alerts.append(LeakageAlert(
                    rule_type=LeakageRuleType.BOTTLENECK,
                    system_name=dependent,
                    dimension=f"blocked_by_{primary}",
                    estimated_annual_loss=round(bottleneck_loss, 2),
                    cascade_multiplier=dep_weight,
                    escalation_level=EscalationLevel.LEVEL_2_DEPARTMENT,
                    description=f"{primary} healthy but {dependent} degrading — dependency bottleneck",
                    severity="warning",
                ))

        total_loss = sum(a.estimated_annual_loss for a in alerts)

        return LeakageReport(
            total_estimated_annual_loss=round(total_loss, 2),
            alerts=alerts,
            systems_in_leakage=n_leaking,
            cascade_multiplier_applied=cascade_mult,
        )
