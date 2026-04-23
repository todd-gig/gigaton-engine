"""
Learning Loop — Post-Execution Variance Tracking & Institutional Learning

Implements the feedback loop described in docs/09_learning_loop.md:
1. Record expected vs actual outcomes for executed decisions
2. Calculate variance with directional decomposition
3. Recommend trust adjustments (upgrade/downgrade)
4. Identify update targets (registries, weights, thresholds, playbooks)
5. Persist all learning records to JSON flat-file storage
6. Surface aggregate learning metrics for continuous improvement

Core Rule: A repeated decision class should get easier, faster, and safer over time.

Storage: JSON-lines file at {data_dir}/learning_records.jsonl
Index:   JSON file at {data_dir}/learning_index.json (keyed by decision_id)
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4


# ─────────────────────────────────────────────
# ENUMS
# ─────────────────────────────────────────────

class VarianceDirection(Enum):
    POSITIVE = "positive"       # Actual exceeded expected
    NEUTRAL = "neutral"         # Within tolerance
    NEGATIVE = "negative"       # Actual fell short of expected


class TrustRecommendation(Enum):
    UPGRADE = "upgrade"
    MAINTAIN = "maintain"
    DOWNGRADE = "downgrade"
    REVIEW = "review"           # Needs human review — ambiguous signal


class UpdateTarget(Enum):
    FIRST_PRINCIPLES_REGISTRY = "first_principles_registry"
    VALUE_MATRIX_WEIGHTS = "value_matrix_weights"
    TRUST_MATRIX_WEIGHTS = "trust_matrix_weights"
    EXECUTION_THRESHOLDS = "execution_thresholds"
    PLAYBOOKS = "playbooks"
    TEMPLATES = "templates"


# ─────────────────────────────────────────────
# DATA MODELS
# ─────────────────────────────────────────────

@dataclass
class OutcomeRecord:
    """Captures the actual outcome of an executed decision."""
    decision_id: str = ""
    decision_class: str = ""
    original_verdict: str = ""
    # Expected outcome (captured at execution time)
    expected_value: float = 0.0
    expected_timeline_days: int = 0
    expected_risk_level: str = ""       # low, medium, high
    # Actual outcome (captured post-execution)
    actual_value: float = 0.0
    actual_timeline_days: int = 0
    actual_risk_materialized: bool = False
    actual_risk_description: str = ""
    # Qualitative
    outcome_summary: str = ""
    lessons_learned: list[str] = field(default_factory=list)
    # Metadata
    recorded_by: str = ""
    recorded_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class VarianceAnalysis:
    """Decomposed variance between expected and actual."""
    decision_id: str = ""
    # Value variance
    value_variance: float = 0.0         # actual_value - expected_value
    value_variance_pct: float = 0.0     # percentage deviation
    value_direction: VarianceDirection = VarianceDirection.NEUTRAL
    # Timeline variance
    timeline_variance_days: int = 0     # actual - expected (positive = late)
    timeline_direction: VarianceDirection = VarianceDirection.NEUTRAL
    # Risk variance
    risk_surprise: bool = False         # risk materialized when not expected (or vice versa)
    # Composite
    composite_variance_score: float = 0.0   # -1.0 to +1.0 normalized
    # Derived recommendations
    trust_recommendation: TrustRecommendation = TrustRecommendation.MAINTAIN
    trust_recommendation_reason: str = ""
    suggested_update_targets: list[str] = field(default_factory=list)
    suggested_actions: list[str] = field(default_factory=list)
    # Metadata
    analyzed_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class LearningRecord:
    """Complete learning record combining outcome + variance."""
    record_id: str = ""
    decision_id: str = ""
    decision_class: str = ""
    outcome: OutcomeRecord = field(default_factory=OutcomeRecord)
    variance: VarianceAnalysis = field(default_factory=VarianceAnalysis)
    # Tracking
    applied: bool = False               # Has this learning been applied?
    applied_at: Optional[str] = None
    applied_targets: list[str] = field(default_factory=list)
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ─────────────────────────────────────────────
# VARIANCE CALCULATION ENGINE
# ─────────────────────────────────────────────

# Tolerance band: variance within ±10% is considered neutral
VALUE_TOLERANCE_PCT = 0.10
TIMELINE_TOLERANCE_DAYS = 3


def calculate_variance(outcome: OutcomeRecord) -> VarianceAnalysis:
    """
    Decompose expected vs actual into directional variance components.
    Returns a VarianceAnalysis with trust recommendation and update targets.
    """
    va = VarianceAnalysis(decision_id=outcome.decision_id)

    # ── Value variance ──
    va.value_variance = outcome.actual_value - outcome.expected_value
    if outcome.expected_value != 0:
        va.value_variance_pct = va.value_variance / abs(outcome.expected_value)
    else:
        va.value_variance_pct = 1.0 if outcome.actual_value > 0 else 0.0

    if va.value_variance_pct > VALUE_TOLERANCE_PCT:
        va.value_direction = VarianceDirection.POSITIVE
    elif va.value_variance_pct < -VALUE_TOLERANCE_PCT:
        va.value_direction = VarianceDirection.NEGATIVE
    else:
        va.value_direction = VarianceDirection.NEUTRAL

    # ── Timeline variance ──
    va.timeline_variance_days = outcome.actual_timeline_days - outcome.expected_timeline_days
    if va.timeline_variance_days < -TIMELINE_TOLERANCE_DAYS:
        va.timeline_direction = VarianceDirection.POSITIVE   # Faster than expected
    elif va.timeline_variance_days > TIMELINE_TOLERANCE_DAYS:
        va.timeline_direction = VarianceDirection.NEGATIVE   # Slower than expected
    else:
        va.timeline_direction = VarianceDirection.NEUTRAL

    # ── Risk variance ──
    va.risk_surprise = outcome.actual_risk_materialized and outcome.expected_risk_level == "low"

    # ── Composite score (-1.0 to +1.0) ──
    # Weighted: value 50%, timeline 30%, risk 20%
    value_component = _direction_to_score(va.value_direction)
    timeline_component = _direction_to_score(va.timeline_direction)
    risk_component = -1.0 if va.risk_surprise else (0.5 if not outcome.actual_risk_materialized else -0.3)
    va.composite_variance_score = round(
        value_component * 0.50 + timeline_component * 0.30 + risk_component * 0.20,
        3
    )

    # ── Trust recommendation ──
    va.trust_recommendation, va.trust_recommendation_reason = _derive_trust_recommendation(va)

    # ── Update targets ──
    va.suggested_update_targets = _derive_update_targets(va, outcome)
    va.suggested_actions = _derive_actions(va, outcome)

    return va


def _direction_to_score(d: VarianceDirection) -> float:
    return {
        VarianceDirection.POSITIVE: 1.0,
        VarianceDirection.NEUTRAL: 0.0,
        VarianceDirection.NEGATIVE: -1.0,
    }[d]


def _derive_trust_recommendation(va: VarianceAnalysis) -> tuple[TrustRecommendation, str]:
    """Map composite variance to a trust recommendation."""
    score = va.composite_variance_score

    if va.risk_surprise:
        return (
            TrustRecommendation.DOWNGRADE,
            f"Risk materialized unexpectedly. Composite: {score}. "
            "Risk containment model needs recalibration."
        )

    if score >= 0.5:
        return (
            TrustRecommendation.UPGRADE,
            f"Strong positive variance ({score}). "
            "Decision framework predicted conservatively — trust can be elevated."
        )
    elif score >= -0.2:
        return (
            TrustRecommendation.MAINTAIN,
            f"Variance within acceptable range ({score}). "
            "No trust adjustment needed."
        )
    elif score >= -0.5:
        return (
            TrustRecommendation.REVIEW,
            f"Moderate negative variance ({score}). "
            "Human review recommended to identify root cause."
        )
    else:
        return (
            TrustRecommendation.DOWNGRADE,
            f"Significant negative variance ({score}). "
            "Decision framework overestimated value or underestimated risk."
        )


def _derive_update_targets(va: VarianceAnalysis, outcome: OutcomeRecord) -> list[str]:
    """Determine which system artifacts should be updated based on variance."""
    targets = []

    if va.value_direction == VarianceDirection.NEGATIVE:
        targets.append(UpdateTarget.VALUE_MATRIX_WEIGHTS.value)

    if va.risk_surprise:
        targets.append(UpdateTarget.TRUST_MATRIX_WEIGHTS.value)
        targets.append(UpdateTarget.EXECUTION_THRESHOLDS.value)

    if va.timeline_direction == VarianceDirection.NEGATIVE:
        targets.append(UpdateTarget.PLAYBOOKS.value)

    if va.composite_variance_score >= 0.5:
        # Positive learnings → update playbooks and templates to codify
        targets.append(UpdateTarget.PLAYBOOKS.value)
        targets.append(UpdateTarget.TEMPLATES.value)

    if any(
        "first_principle" in lesson.lower() or "axiom" in lesson.lower()
        for lesson in outcome.lessons_learned
    ):
        targets.append(UpdateTarget.FIRST_PRINCIPLES_REGISTRY.value)

    return list(set(targets))  # deduplicate


def _derive_actions(va: VarianceAnalysis, outcome: OutcomeRecord) -> list[str]:
    """Generate specific action items from the variance analysis."""
    actions = []

    if va.trust_recommendation == TrustRecommendation.DOWNGRADE:
        actions.append(
            f"DOWNGRADE trust parameters for {outcome.decision_class} decisions. "
            f"Reason: {va.trust_recommendation_reason}"
        )

    if va.trust_recommendation == TrustRecommendation.UPGRADE:
        actions.append(
            f"EVALUATE trust promotion for {outcome.decision_class} decisions. "
            f"Pattern shows conservative estimation."
        )

    if va.risk_surprise:
        actions.append(
            "AUDIT risk containment model — unexpected risk materialization indicates "
            "blind spot in risk scoring."
        )

    if va.value_direction == VarianceDirection.NEGATIVE:
        actions.append(
            "RECALIBRATE value scoring weights — actual value fell short of prediction."
        )

    if va.timeline_direction == VarianceDirection.NEGATIVE:
        actions.append(
            f"REVIEW execution playbooks — timeline overran by "
            f"{va.timeline_variance_days} days."
        )

    if not actions:
        actions.append("No corrective actions required — outcome within tolerance.")

    return actions


# ─────────────────────────────────────────────
# OUTCOME REPORTER
# ─────────────────────────────────────────────

class OutcomeReporter:
    """Record and analyze decision outcomes."""

    @staticmethod
    def record_outcome(
        decision_id: str,
        decision_class: str,
        original_verdict: str,
        expected_value: float,
        expected_timeline_days: int,
        expected_risk_level: str,
        actual_value: float,
        actual_timeline_days: int,
        actual_risk_materialized: bool,
        actual_risk_description: str = "",
        outcome_summary: str = "",
        lessons_learned: list[str] = None,
        recorded_by: str = "",
    ) -> LearningRecord:
        """
        Record a decision outcome and compute variance analysis.

        Returns the complete LearningRecord with variance analysis.
        """
        outcome = OutcomeRecord(
            decision_id=decision_id,
            decision_class=decision_class,
            original_verdict=original_verdict,
            expected_value=expected_value,
            expected_timeline_days=expected_timeline_days,
            expected_risk_level=expected_risk_level,
            actual_value=actual_value,
            actual_timeline_days=actual_timeline_days,
            actual_risk_materialized=actual_risk_materialized,
            actual_risk_description=actual_risk_description,
            outcome_summary=outcome_summary,
            lessons_learned=lessons_learned or [],
            recorded_by=recorded_by,
        )

        variance = calculate_variance(outcome)

        record = LearningRecord(
            record_id=f"LRN-{uuid4().hex[:8]}",
            decision_id=decision_id,
            decision_class=decision_class,
            outcome=outcome,
            variance=variance,
        )

        return record

    @staticmethod
    def compare_expected_vs_actual(outcome: OutcomeRecord) -> dict:
        """Generate comparison metrics between expected and actual."""
        return {
            "expected_value": outcome.expected_value,
            "actual_value": outcome.actual_value,
            "value_variance": outcome.actual_value - outcome.expected_value,
            "expected_timeline_days": outcome.expected_timeline_days,
            "actual_timeline_days": outcome.actual_timeline_days,
            "timeline_variance_days": outcome.actual_timeline_days - outcome.expected_timeline_days,
            "expected_risk_level": outcome.expected_risk_level,
            "actual_risk_materialized": outcome.actual_risk_materialized,
        }

    @staticmethod
    def generate_outcome_summary(record: LearningRecord) -> str:
        """Generate a human-readable summary of the outcome and variance."""
        lines = [
            f"Decision ID: {record.decision_id}",
            f"Decision Class: {record.decision_class}",
            f"Original Verdict: {record.outcome.original_verdict}",
            "",
            "Expected vs Actual:",
            f"  Value: {record.outcome.expected_value} → {record.outcome.actual_value} "
            f"(variance: {record.variance.value_variance:+.2f}, {record.variance.value_direction.value})",
            f"  Timeline: {record.outcome.expected_timeline_days}d → {record.outcome.actual_timeline_days}d "
            f"(variance: {record.variance.timeline_variance_days:+d}d, {record.variance.timeline_direction.value})",
            f"  Risk: expected={record.outcome.expected_risk_level}, materialized={record.outcome.actual_risk_materialized}",
            "",
            "Variance Analysis:",
            f"  Composite Score: {record.variance.composite_variance_score}",
            f"  Trust Recommendation: {record.variance.trust_recommendation.value}",
            f"  Reason: {record.variance.trust_recommendation_reason}",
            "",
            "Update Targets:",
        ]

        if record.variance.suggested_update_targets:
            for target in record.variance.suggested_update_targets:
                lines.append(f"  - {target}")
        else:
            lines.append("  (none)")

        lines.append("")
        lines.append("Suggested Actions:")
        for action in record.variance.suggested_actions:
            lines.append(f"  - {action}")

        return "\n".join(lines)


# ─────────────────────────────────────────────
# LEARNING LOOP CLASS (composable)
# ─────────────────────────────────────────────

class LearningLoop:
    """
    Composable learning loop that tracks decision outcomes and generates
    recommendations without persistence (for use in pipelines).
    """

    def __init__(self):
        self.records: list[LearningRecord] = []
        self.reporter = OutcomeReporter()

    def analyze_outcome(
        self,
        decision_id: str,
        decision_class: str,
        original_verdict: str,
        expected_value: float,
        expected_timeline_days: int,
        expected_risk_level: str,
        actual_value: float,
        actual_timeline_days: int,
        actual_risk_materialized: bool,
        actual_risk_description: str = "",
        outcome_summary: str = "",
        lessons_learned: list[str] = None,
        recorded_by: str = "",
    ) -> LearningRecord:
        """Analyze an outcome and record learning."""
        record = self.reporter.record_outcome(
            decision_id=decision_id,
            decision_class=decision_class,
            original_verdict=original_verdict,
            expected_value=expected_value,
            expected_timeline_days=expected_timeline_days,
            expected_risk_level=expected_risk_level,
            actual_value=actual_value,
            actual_timeline_days=actual_timeline_days,
            actual_risk_materialized=actual_risk_materialized,
            actual_risk_description=actual_risk_description,
            outcome_summary=outcome_summary,
            lessons_learned=lessons_learned,
            recorded_by=recorded_by,
        )
        self.records.append(record)
        return record

    def compute_variance(self, outcome: OutcomeRecord) -> VarianceAnalysis:
        """Compute variance for an outcome."""
        return calculate_variance(outcome)

    def recommend_trust_adjustment(self, record: LearningRecord) -> TrustRecommendation:
        """Get trust recommendation from a learning record."""
        return record.variance.trust_recommendation

    def generate_update_targets(self, record: LearningRecord) -> list[str]:
        """Get suggested update targets from a learning record."""
        return record.variance.suggested_update_targets

    def compile_learning_report(self) -> dict:
        """Generate aggregate statistics from all recorded learnings."""
        if not self.records:
            return {
                "total_records": 0,
                "by_class": {},
                "recommendations": [],
            }

        by_class: dict[str, list[LearningRecord]] = {}
        for record in self.records:
            by_class.setdefault(record.decision_class, []).append(record)

        class_stats = {}
        for cls, recs in by_class.items():
            upgrades = sum(1 for r in recs if r.variance.trust_recommendation == TrustRecommendation.UPGRADE)
            downgrades = sum(1 for r in recs if r.variance.trust_recommendation == TrustRecommendation.DOWNGRADE)
            reviews = sum(1 for r in recs if r.variance.trust_recommendation == TrustRecommendation.REVIEW)
            maintains = sum(1 for r in recs if r.variance.trust_recommendation == TrustRecommendation.MAINTAIN)
            avg_variance = sum(r.variance.composite_variance_score for r in recs) / len(recs)

            class_stats[cls] = {
                "count": len(recs),
                "upgrade_count": upgrades,
                "downgrade_count": downgrades,
                "review_count": reviews,
                "maintain_count": maintains,
                "avg_variance": round(avg_variance, 3),
                "upgrade_rate": round(upgrades / len(recs), 3) if recs else 0.0,
            }

        return {
            "total_records": len(self.records),
            "by_class": class_stats,
            "recommendations": [
                r.variance.trust_recommendation.value
                for r in self.records
            ],
        }
