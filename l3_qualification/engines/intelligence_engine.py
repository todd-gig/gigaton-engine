"""
Client Intelligence Engine

Implements comprehensive client intelligence scoring across 15 master categories
with 5 sub-variables per category, gap analysis, priority ranking, and action generation.

15 Categories (with weights totaling 1.0):
1. Identity Purpose (0.05)
2. Market Reality (0.08)
3. Customer (0.10)
4. Value Creation (0.10)
5. Revenue (0.10)
6. Cost Resources (0.08)
7. Time (0.07)
8. Trust Credibility (0.08)
9. Systems Processes (0.08)
10. Human Capital (0.07)
11. Intelligence Data (0.06)
12. Growth Leverage (0.06)
13. Risk Uncertainty (0.03)
14. Innovation Adaptation (0.02)
15. Governance Control (0.02)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


# ─────────────────────────────────────────────
# MASTER CATEGORIES & VARIABLES
# ─────────────────────────────────────────────

MASTER_CATEGORIES = {
    "identity_purpose": {
        "weight": 0.05,
        "label": "Identity & Purpose",
        "variables": [
            "mission_clarity",
            "brand_differentiation",
            "purpose_alignment",
            "identity_consistency",
            "aspiration_authenticity",
        ],
    },
    "market_reality": {
        "weight": 0.08,
        "label": "Market Reality",
        "variables": [
            "market_sizing",
            "competitive_positioning",
            "industry_trends",
            "regulatory_environment",
            "economic_conditions",
        ],
    },
    "customer": {
        "weight": 0.10,
        "label": "Customer",
        "variables": [
            "customer_needs_clarity",
            "customer_satisfaction",
            "customer_retention",
            "customer_advocacy",
            "customer_intimacy",
        ],
    },
    "value_creation": {
        "weight": 0.10,
        "label": "Value Creation",
        "variables": [
            "value_proposition_clarity",
            "value_delivery_execution",
            "value_differentiation",
            "value_sustainability",
            "value_scalability",
        ],
    },
    "revenue": {
        "weight": 0.10,
        "label": "Revenue",
        "variables": [
            "revenue_model_viability",
            "revenue_diversification",
            "revenue_growth_trajectory",
            "revenue_predictability",
            "revenue_quality",
        ],
    },
    "cost_resources": {
        "weight": 0.08,
        "label": "Cost & Resources",
        "variables": [
            "cost_structure_efficiency",
            "resource_allocation_optimization",
            "operational_leverage",
            "capex_requirements",
            "working_capital_efficiency",
        ],
    },
    "time": {
        "weight": 0.07,
        "label": "Time",
        "variables": [
            "time_to_market",
            "execution_velocity",
            "cycle_time_efficiency",
            "timeline_predictability",
            "speed_advantage",
        ],
    },
    "trust_credibility": {
        "weight": 0.08,
        "label": "Trust & Credibility",
        "variables": [
            "leadership_track_record",
            "stakeholder_confidence",
            "historical_promise_delivery",
            "stakeholder_alignment",
            "crisis_resilience",
        ],
    },
    "systems_processes": {
        "weight": 0.08,
        "label": "Systems & Processes",
        "variables": [
            "process_standardization",
            "operational_efficiency",
            "quality_consistency",
            "documentation_completeness",
            "automation_maturity",
        ],
    },
    "human_capital": {
        "weight": 0.07,
        "label": "Human Capital",
        "variables": [
            "talent_quality",
            "capability_depth",
            "team_cohesion",
            "knowledge_retention",
            "culture_alignment",
        ],
    },
    "intelligence_data": {
        "weight": 0.06,
        "label": "Intelligence & Data",
        "variables": [
            "data_quality",
            "insights_actionability",
            "decision_velocity",
            "data_integration",
            "analytics_sophistication",
        ],
    },
    "growth_leverage": {
        "weight": 0.06,
        "label": "Growth Leverage",
        "variables": [
            "network_effects",
            "platform_scalability",
            "partnership_leverage",
            "ecosystem_strength",
            "expansion_readiness",
        ],
    },
    "risk_uncertainty": {
        "weight": 0.03,
        "label": "Risk & Uncertainty",
        "variables": [
            "market_risk",
            "execution_risk",
            "financial_risk",
            "regulatory_risk",
            "concentration_risk",
        ],
    },
    "innovation_adaptation": {
        "weight": 0.02,
        "label": "Innovation & Adaptation",
        "variables": [
            "innovation_culture",
            "adaptation_velocity",
            "disruption_readiness",
            "learning_capability",
            "reinvention_capacity",
        ],
    },
    "governance_control": {
        "weight": 0.02,
        "label": "Governance & Control",
        "variables": [
            "governance_structure",
            "control_frameworks",
            "compliance_maturity",
            "audit_readiness",
            "stakeholder_accountability",
        ],
    },
}


# ─────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────

class GapSeverity(str, Enum):
    """Severity classification for identified gaps."""
    MINOR = "minor"          # gap_score < 10.0
    MODERATE = "moderate"    # gap_score < 25.0
    MAJOR = "major"          # gap_score < 45.0
    CRITICAL = "critical"    # gap_score >= 45.0


GAP_SEVERITY_BANDS = [
    (10.0, GapSeverity.MINOR),
    (25.0, GapSeverity.MODERATE),
    (45.0, GapSeverity.MAJOR),
    (float("inf"), GapSeverity.CRITICAL),
]


# ─────────────────────────────────────────────
# SCORING MODELS
# ─────────────────────────────────────────────

@dataclass
class CategoryScore:
    """Score for a single category."""
    category_key: str
    category_label: str
    variable_strength: float  # 0-100
    evidence_quality: float  # 0-100
    execution_maturity: float  # 0-100
    consistency: float  # 0-100
    strategic_fit: float  # 0-100

    def composite_score(self) -> float:
        """
        Calculate composite category score.
        Formula: VS×0.35 + EQ×0.20 + EM×0.20 + CO×0.15 + SF×0.10
        """
        return (
            self.variable_strength * 0.35
            + self.evidence_quality * 0.20
            + self.execution_maturity * 0.20
            + self.consistency * 0.15
            + self.strategic_fit * 0.10
        )


@dataclass
class GapResult:
    """Gap analysis result for a category."""
    category_key: str
    category_label: str
    actual: float  # Current score (0-100)
    target: float  # Target score (0-100)
    strategic_importance: float  # 0-1
    trust_penalty_modifier: float  # 0-1

    def gap_score(self) -> float:
        """
        Calculate gap score for priority ranking.
        Formula: max(0, target - actual) × strategic_importance × trust_penalty_modifier
        """
        return max(0, self.target - self.actual) * self.strategic_importance * self.trust_penalty_modifier

    def gap_severity(self) -> GapSeverity:
        """Classify gap severity."""
        score = self.gap_score()
        for threshold, severity in GAP_SEVERITY_BANDS:
            if score < threshold:
                return severity
        return GapSeverity.CRITICAL


@dataclass
class ActionItem:
    """Recommended action item from gap analysis."""
    category_key: str
    category_label: str
    description: str
    gap_score: float
    leverage: float  # 0-1, impact of addressing this gap
    urgency: float  # 0-1, time sensitivity
    value_impact: float  # 0-1, value creation potential
    severity: GapSeverity = GapSeverity.MINOR

    def priority_score(self) -> float:
        """
        Calculate action priority score for ranking.
        Formula: gap_score×0.35 + leverage×0.30 + urgency×0.20 + value_impact×0.15
        """
        return (
            self.gap_score * 0.35
            + self.leverage * 0.30
            + self.urgency * 0.20
            + self.value_impact * 0.15
        )


@dataclass
class ClientIntelligenceReport:
    """Complete client intelligence report."""
    client_name: str
    report_date: str
    category_scores: Dict[str, CategoryScore] = field(default_factory=dict)
    gap_results: Dict[str, GapResult] = field(default_factory=dict)
    action_items: List[ActionItem] = field(default_factory=list)
    overall_trust_stage: str = "unknown"
    overall_weighted_score: float = 0.0


# ─────────────────────────────────────────────
# INTELLIGENCE ENGINE
# ─────────────────────────────────────────────

class ClientIntelligenceEngine:
    """
    Client intelligence engine for comprehensive assessment across 15 categories.
    """

    def __init__(self):
        """Initialize with master categories."""
        self.categories = MASTER_CATEGORIES

    def score_category(
        self,
        category_key: str,
        variable_strength: float,
        evidence_quality: float,
        execution_maturity: float,
        consistency: float,
        strategic_fit: float,
    ) -> CategoryScore:
        """Score a single category."""
        if category_key not in self.categories:
            raise ValueError(f"Unknown category: {category_key}")

        return CategoryScore(
            category_key=category_key,
            category_label=self.categories[category_key]["label"],
            variable_strength=min(100, max(0, variable_strength)),
            evidence_quality=min(100, max(0, evidence_quality)),
            execution_maturity=min(100, max(0, execution_maturity)),
            consistency=min(100, max(0, consistency)),
            strategic_fit=min(100, max(0, strategic_fit)),
        )

    def analyze_gap(
        self,
        category_key: str,
        actual: float,
        target: float,
        strategic_importance: float = 1.0,
        trust_penalty_modifier: float = 1.0,
    ) -> GapResult:
        """Analyze gap for a category."""
        if category_key not in self.categories:
            raise ValueError(f"Unknown category: {category_key}")

        return GapResult(
            category_key=category_key,
            category_label=self.categories[category_key]["label"],
            actual=min(100, max(0, actual)),
            target=min(100, max(0, target)),
            strategic_importance=min(1.0, max(0, strategic_importance)),
            trust_penalty_modifier=min(1.0, max(0, trust_penalty_modifier)),
        )

    def generate_action(
        self,
        gap_result: GapResult,
        description: str,
        leverage: float = 0.5,
        urgency: float = 0.5,
        value_impact: float = 0.5,
    ) -> ActionItem:
        """Generate action item from gap."""
        action = ActionItem(
            category_key=gap_result.category_key,
            category_label=gap_result.category_label,
            description=description,
            gap_score=gap_result.gap_score(),
            leverage=min(1.0, max(0, leverage)),
            urgency=min(1.0, max(0, urgency)),
            value_impact=min(1.0, max(0, value_impact)),
            severity=gap_result.gap_severity(),
        )
        return action

    def calculate_overall_score(
        self, category_scores: Dict[str, CategoryScore]
    ) -> float:
        """
        Calculate overall weighted intelligence score.

        Formula: sum(category_score × category_weight) for all 15 categories
        """
        total_score = 0.0

        for key, score in category_scores.items():
            if key in self.categories:
                weight = self.categories[key]["weight"]
                composite = score.composite_score()
                total_score += (composite / 100.0) * weight

        return round(total_score * 100, 1)

    def prioritize_actions(self, action_items: List[ActionItem]) -> List[ActionItem]:
        """
        Rank actions by priority score (descending).

        Returns sorted list of ActionItem objects.
        """
        return sorted(
            action_items,
            key=lambda a: a.priority_score(),
            reverse=True,
        )

    def generate_report(
        self,
        client_name: str,
        report_date: str,
        category_scores: Dict[str, CategoryScore],
        gap_results: Dict[str, GapResult],
        action_items: List[ActionItem],
        overall_trust_stage: str = "unknown",
    ) -> ClientIntelligenceReport:
        """Generate comprehensive client intelligence report."""
        # Sort actions by priority
        sorted_actions = self.prioritize_actions(action_items)

        # Calculate overall weighted score
        overall_score = self.calculate_overall_score(category_scores)

        return ClientIntelligenceReport(
            client_name=client_name,
            report_date=report_date,
            category_scores=category_scores,
            gap_results=gap_results,
            action_items=sorted_actions,
            overall_trust_stage=overall_trust_stage,
            overall_weighted_score=overall_score,
        )

    def get_category_info(self, category_key: str) -> Dict:
        """Get info about a specific category."""
        if category_key not in self.categories:
            raise ValueError(f"Unknown category: {category_key}")
        return self.categories[category_key]

    def list_categories(self) -> List[Dict]:
        """List all 15 master categories."""
        return [
            {
                "key": key,
                "label": info["label"],
                "weight": info["weight"],
                "variables": info["variables"],
            }
            for key, info in self.categories.items()
        ]
