"""
ROI and Organizational Value Score (OVS) Engines

Implements:
- ROI calculation with leverage factors and confidence-weighted risk
- Portfolio ranking and resource allocation
- OVS composite scoring across 4 organizational dimensions
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


# ─────────────────────────────────────────────
# ENUMERATIONS
# ─────────────────────────────────────────────

class LeverageScope(str, Enum):
    """Leverage scope determines leverage factor multiplier."""
    SINGLE_SYSTEM = "single_system"  # 0.1
    TWO_SYSTEMS = "two_systems"      # 0.3
    THREE_SYSTEMS = "three_systems"  # 0.6


class HealthStatus(str, Enum):
    """Health status classification."""
    GREEN = "green"              # 0.7-1.0
    YELLOW = "yellow"            # 0.5-0.7
    RED = "red"                  # < 0.5
    TRENDING_RED = "trending_red"


class MaturityLevel(str, Enum):
    """Organizational maturity level."""
    BASIC_BASELINE = "basic_baseline"                              # 1
    STANDARDIZED_FOUNDATION = "standardized_foundation"            # 2
    MANAGED_OPTIMIZATION = "managed_optimization"                  # 3
    INTEGRATED_CONTINUOUS_IMPROVEMENT = "integrated_continuous_improvement"  # 4
    STRATEGIC_OPTIMIZATION = "strategic_optimization"              # 5


# ─────────────────────────────────────────────
# ROI MODELS
# ─────────────────────────────────────────────

@dataclass
class ImplementationCost:
    """Implementation cost breakdown."""
    personnel_cost: float = 0.0  # Direct staff allocation
    capital_cost: float = 0.0    # Equipment, licenses, infrastructure
    coordination_cost: float = 0.0  # Change management, training
    opportunity_cost: float = 0.0  # Alternative uses of resources

    @property
    def total(self) -> float:
        """Total cost across all dimensions."""
        return (
            self.personnel_cost
            + self.capital_cost
            + self.coordination_cost
            + self.opportunity_cost
        )


@dataclass
class ROIInput:
    """Input for ROI calculation."""
    name: str
    annual_leakage_loss: float  # Current annual loss from inefficiency
    expected_performance_after: float  # Target performance (0-1)
    implementation_cost: ImplementationCost
    leverage_scope: LeverageScope = LeverageScope.SINGLE_SYSTEM
    confidence: float = 0.7  # 0-1 confidence in estimates
    complexity_score: float = 0.5  # 0-1 implementation complexity
    org_readiness_gap: float = 0.0  # 0-1 organizational readiness shortfall
    required_hours: float = 1000.0  # Implementation effort
    strategic_urgency: float = 0.5  # 0-1 strategic urgency
    is_dependency_blocker: bool = False  # Blocks other initiatives


@dataclass
class ROIResult:
    """Result of ROI calculation."""
    name: str
    impact_value: float  # Annual impact from elimination of leakage
    total_cost: float  # Total implementation cost
    roi_score: float  # Dimensionless ROI score for ranking
    leverage_factor: float  # Leverage multiplier based on scope
    risk_factor: float  # Risk adjustment (0-1)
    value_per_hour: float  # Impact value per hour invested
    passes_threshold: bool = False  # Passes ROI threshold


@dataclass
class ROIPortfolio:
    """Portfolio of ROI results."""
    results: List[ROIResult] = field(default_factory=list)
    total_impact: float = 0.0
    total_cost: float = 0.0
    portfolio_roi: float = 0.0

    def add_result(self, result: ROIResult) -> None:
        """Add result and update totals."""
        self.results.append(result)
        self.total_impact += result.impact_value
        self.total_cost += result.total_cost
        if self.total_cost > 0:
            self.portfolio_roi = self.total_impact / self.total_cost


class ROIEngine:
    """
    ROI calculation and portfolio management engine.
    Formula: roi_score = (impact / cost) × (1 + leverage) × (1 - risk)
    """

    # Leverage factors per scope
    LEVERAGE_FACTORS = {
        LeverageScope.SINGLE_SYSTEM: 0.1,
        LeverageScope.TWO_SYSTEMS: 0.3,
        LeverageScope.THREE_SYSTEMS: 0.6,
    }

    # ROI threshold for approval
    ROI_THRESHOLD = 1.0

    def calculate(self, inp: ROIInput) -> ROIResult:
        """
        Calculate ROI for a single initiative.

        Formula breakdown:
        - impact_value = annual_leakage_loss × (1 - expected_performance_after)
        - risk_factor = (1 - confidence) × 0.3 + complexity × 0.4 + readiness_gap × 0.3
        - leverage_factor from leverage_scope
        - roi_score = (impact / cost) × (1 + leverage) × (1 - risk)
        """
        # Calculate annual impact from closing the leakage gap
        impact_value = inp.annual_leakage_loss * (1 - inp.expected_performance_after)

        # Get total cost
        total_cost = inp.implementation_cost.total
        if total_cost <= 0:
            total_cost = 1.0  # Prevent division by zero

        # Calculate risk factor (weighted combination)
        risk_factor = (
            (1 - inp.confidence) * 0.3
            + inp.complexity_score * 0.4
            + inp.org_readiness_gap * 0.3
        )

        # Get leverage factor
        leverage_factor = self.LEVERAGE_FACTORS.get(inp.leverage_scope, 0.1)

        # Calculate ROI score
        base_roi = impact_value / total_cost
        roi_score = base_roi * (1 + leverage_factor) * (1 - risk_factor)

        # Calculate value per hour
        if inp.required_hours > 0:
            value_per_hour = impact_value / inp.required_hours
        else:
            value_per_hour = 0.0

        # Check against threshold
        passes_threshold = roi_score >= self.ROI_THRESHOLD

        return ROIResult(
            name=inp.name,
            impact_value=round(impact_value, 2),
            total_cost=round(total_cost, 2),
            roi_score=round(roi_score, 3),
            leverage_factor=leverage_factor,
            risk_factor=round(risk_factor, 3),
            value_per_hour=round(value_per_hour, 2),
            passes_threshold=passes_threshold,
        )

    def rank_portfolio(self, inputs: List[ROIInput]) -> ROIPortfolio:
        """
        Rank a portfolio of initiatives by strategic priority.

        Sort order:
        1. Dependency blockers first (highest impact on other initiatives)
        2. Then by ROI score (descending)
        3. Then by strategic urgency (descending)
        4. Then by value per hour (descending)
        """
        results = [self.calculate(inp) for inp in inputs]

        # Sort by: dependency blocker (reverse), roi_score (reverse), urgency (reverse)
        sorted_results = sorted(
            results,
            key=lambda r: (
                # Find corresponding input for this result
                next(
                    (inp.is_dependency_blocker for inp in inputs if inp.name == r.name),
                    False,
                ),
                r.roi_score,
                next(
                    (inp.strategic_urgency for inp in inputs if inp.name == r.name),
                    0.0,
                ),
                r.value_per_hour,
            ),
            reverse=True,
        )

        portfolio = ROIPortfolio()
        for result in sorted_results:
            portfolio.add_result(result)

        return portfolio

    def allocate_resources(
        self, portfolio: ROIPortfolio, total_budget: float
    ) -> Dict[str, float]:
        """
        Allocate resources greedily by value per hour until budget exhausted.

        Returns dict of initiative name -> allocated budget.
        """
        allocation = {}
        remaining_budget = total_budget

        for result in portfolio.results:
            if remaining_budget <= 0:
                break

            # Allocate the lesser of (requested cost or remaining budget)
            allocated = min(result.total_cost, remaining_budget)
            allocation[result.name] = allocated
            remaining_budget -= allocated

        return allocation


# ─────────────────────────────────────────────
# OVS (Organizational Value Score) MODELS
# ─────────────────────────────────────────────

@dataclass
class PeopleDimensions:
    """People dimension scoring."""
    cultural_diversity: float = 0.0  # 0-1
    decision_making_quality: float = 0.0  # 0-1
    relationship_cohesion: float = 0.0  # 0-1
    information_availability: float = 0.0  # 0-1
    learning_velocity: float = 0.0  # 0-1


@dataclass
class ProcessDimensions:
    """Process dimension scoring."""
    standardization: float = 0.0  # 0-1
    efficiency: float = 0.0  # 0-1
    quality: float = 0.0  # 0-1
    automation: float = 0.0  # 0-1
    discipline: float = 0.0  # 0-1


@dataclass
class TechnologyDimensions:
    """Technology dimension scoring."""
    reliability: float = 0.0  # 0-1
    capability: float = 0.0  # 0-1
    data_quality: float = 0.0  # 0-1
    technical_debt: float = 0.0  # 0-1 (inverted: higher = worse)
    security: float = 0.0  # 0-1


@dataclass
class LearningDimensions:
    """Learning dimension scoring."""
    learning_culture: float = 0.0  # 0-1
    knowledge_capture: float = 0.0  # 0-1
    knowledge_distribution: float = 0.0  # 0-1
    knowledge_application: float = 0.0  # 0-1
    learning_velocity: float = 0.0  # 0-1


@dataclass
class SystemScore:
    """Score for a single organizational system."""
    score: float = 0.0  # 0-1
    status: HealthStatus = HealthStatus.RED
    dimensions: Dict[str, float] = field(default_factory=dict)
    confidence: float = 0.0  # 0-1 confidence in score
    trend: Optional[str] = None  # "improving", "stable", "declining"


@dataclass
class OVSResult:
    """Result of organizational value scoring."""
    composite_ovs: float = 0.0  # 0-100 composite OVS
    people_score: float = 0.0  # 0-1
    process_score: float = 0.0  # 0-1
    technology_score: float = 0.0  # 0-1
    learning_score: float = 0.0  # 0-1
    organizational_value: float = 0.0  # 0-1 multiplicative
    maturity_level: MaturityLevel = MaturityLevel.BASIC_BASELINE
    dimension_details: Dict[str, SystemScore] = field(default_factory=dict)


class OVSEngine:
    """
    Organizational Value Score engine.

    Composite OVS = (P×0.30 + Pr×0.25 + T×0.25 + L×0.20) × 100
    Organizational Value = P × Pr × T × L (multiplicative)
    """

    DEFAULT_WEIGHTS = {
        "people": 0.30,
        "process": 0.25,
        "technology": 0.25,
        "learning": 0.20,
    }

    def score_people(self, dims: PeopleDimensions) -> float:
        """
        Score people dimension.
        CD×0.25 + DMQ×0.25 + RC×0.20 + IA×0.20 + LV×0.10
        """
        return (
            dims.cultural_diversity * 0.25
            + dims.decision_making_quality * 0.25
            + dims.relationship_cohesion * 0.20
            + dims.information_availability * 0.20
            + dims.learning_velocity * 0.10
        )

    def score_process(self, dims: ProcessDimensions) -> float:
        """
        Score process dimension.
        PS×0.25 + PE×0.25 + PQ×0.20 + PA×0.15 + PD×0.15
        """
        return (
            dims.standardization * 0.25
            + dims.efficiency * 0.25
            + dims.quality * 0.20
            + dims.automation * 0.15
            + dims.discipline * 0.15
        )

    def score_technology(self, dims: TechnologyDimensions) -> float:
        """
        Score technology dimension.
        SR×0.25 + SC×0.25 + DQ×0.25 + (1-TD)×0.15 + S×0.10
        (Technical debt is inverted)
        """
        return (
            dims.reliability * 0.25
            + dims.capability * 0.25
            + dims.data_quality * 0.25
            + (1 - dims.technical_debt) * 0.15
            + dims.security * 0.10
        )

    def score_learning(self, dims: LearningDimensions) -> float:
        """
        Score learning dimension.
        LC×0.25 + KC×0.25 + KD×0.20 + KA×0.20 + LV×0.10
        """
        return (
            dims.learning_culture * 0.25
            + dims.knowledge_capture * 0.25
            + dims.knowledge_distribution * 0.20
            + dims.knowledge_application * 0.20
            + dims.learning_velocity * 0.10
        )

    def _health_status(self, score: float) -> HealthStatus:
        """Determine health status from 0-1 score."""
        if score >= 0.7:
            return HealthStatus.GREEN
        elif score >= 0.5:
            return HealthStatus.YELLOW
        else:
            return HealthStatus.RED

    def _maturity_level(self, composite_ovs: float) -> MaturityLevel:
        """Determine maturity level from 0-100 OVS."""
        if composite_ovs >= 90:
            return MaturityLevel.STRATEGIC_OPTIMIZATION
        elif composite_ovs >= 70:
            return MaturityLevel.INTEGRATED_CONTINUOUS_IMPROVEMENT
        elif composite_ovs >= 50:
            return MaturityLevel.MANAGED_OPTIMIZATION
        elif composite_ovs >= 30:
            return MaturityLevel.STANDARDIZED_FOUNDATION
        else:
            return MaturityLevel.BASIC_BASELINE

    def calculate(
        self,
        people: PeopleDimensions,
        process: ProcessDimensions,
        technology: TechnologyDimensions,
        learning: LearningDimensions,
    ) -> OVSResult:
        """Calculate organizational value score."""
        # Score each dimension
        people_score = self.score_people(people)
        process_score = self.score_process(process)
        technology_score = self.score_technology(technology)
        learning_score = self.score_learning(learning)

        # Composite OVS (0-100)
        composite_ovs = (
            people_score * 0.30
            + process_score * 0.25
            + technology_score * 0.25
            + learning_score * 0.20
        ) * 100

        # Organizational value (multiplicative 0-1)
        organizational_value = (
            people_score * process_score * technology_score * learning_score
        )

        # Maturity level
        maturity_level = self._maturity_level(composite_ovs)

        # Build dimension details (with rounded scores)
        people_score_rounded = round(people_score, 3)
        process_score_rounded = round(process_score, 3)
        technology_score_rounded = round(technology_score, 3)
        learning_score_rounded = round(learning_score, 3)

        dimension_details = {
            "people": SystemScore(
                score=people_score_rounded,
                status=self._health_status(people_score),
                dimensions={
                    "cultural_diversity": people.cultural_diversity,
                    "decision_making_quality": people.decision_making_quality,
                    "relationship_cohesion": people.relationship_cohesion,
                    "information_availability": people.information_availability,
                    "learning_velocity": people.learning_velocity,
                },
            ),
            "process": SystemScore(
                score=process_score_rounded,
                status=self._health_status(process_score),
                dimensions={
                    "standardization": process.standardization,
                    "efficiency": process.efficiency,
                    "quality": process.quality,
                    "automation": process.automation,
                    "discipline": process.discipline,
                },
            ),
            "technology": SystemScore(
                score=technology_score_rounded,
                status=self._health_status(technology_score),
                dimensions={
                    "reliability": technology.reliability,
                    "capability": technology.capability,
                    "data_quality": technology.data_quality,
                    "technical_debt": technology.technical_debt,
                    "security": technology.security,
                },
            ),
            "learning": SystemScore(
                score=learning_score_rounded,
                status=self._health_status(learning_score),
                dimensions={
                    "learning_culture": learning.learning_culture,
                    "knowledge_capture": learning.knowledge_capture,
                    "knowledge_distribution": learning.knowledge_distribution,
                    "knowledge_application": learning.knowledge_application,
                    "learning_velocity": learning.learning_velocity,
                },
            ),
        }

        return OVSResult(
            composite_ovs=round(composite_ovs, 1),
            people_score=round(people_score, 3),
            process_score=round(process_score, 3),
            technology_score=round(technology_score, 3),
            learning_score=round(learning_score, 3),
            organizational_value=round(organizational_value, 3),
            maturity_level=maturity_level,
            dimension_details=dimension_details,
        )
