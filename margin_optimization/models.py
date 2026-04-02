"""Data models for margin optimization."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Dimension(str, Enum):
    PRODUCT = "product"
    BUNDLE = "bundle"
    CHANNEL = "channel"
    SEGMENT = "segment"


class LeverCategory(str, Enum):
    PRICE_INCREASE = "price_increase"
    BUNDLE_RESTRUCTURING = "bundle_restructuring"
    AUTOMATION = "automation"
    DISCOUNT_CONTROLS = "discount_controls"
    LABOR_MIX = "labor_mix"
    CHANNEL_SHIFT = "channel_shift"
    SCOPE_REDUCTION = "scope_reduction"
    SUPPORT_MODEL = "support_model"


class ImpactSpeed(str, Enum):
    FAST = "fast"      # < 30 days
    MEDIUM = "medium"  # 30-90 days
    SLOW = "slow"      # > 90 days


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class ProfitabilityRecord:
    name: str
    dimension: Dimension
    revenue: float
    direct_cost: float
    variable_cost: float
    total_cost: float

    @property
    def gross_margin(self) -> float:
        return (self.revenue - self.direct_cost) / self.revenue if self.revenue else 0.0

    @property
    def contribution_margin(self) -> float:
        return (self.revenue - self.variable_cost) / self.revenue if self.revenue else 0.0

    @property
    def net_margin(self) -> float:
        return (self.revenue - self.total_cost) / self.revenue if self.revenue else 0.0


@dataclass
class MarginLever:
    category: LeverCategory
    description: str
    estimated_margin_lift_pct: float  # e.g. 0.05 = 5pp lift
    speed: ImpactSpeed
    difficulty: RiskLevel
    revenue_risk: RiskLevel

    @property
    def priority_score(self) -> float:
        """Higher is better — favors high lift, fast, low difficulty, low risk."""
        speed_w = {"fast": 3, "medium": 2, "slow": 1}[self.speed.value]
        diff_w = {"low": 3, "medium": 2, "high": 1}[self.difficulty.value]
        risk_w = {"low": 3, "medium": 2, "high": 1}[self.revenue_risk.value]
        return self.estimated_margin_lift_pct * speed_w * diff_w * risk_w


@dataclass
class AlertCondition:
    rule: str
    threshold: float
    actual: float
    triggered: bool
    entity_name: str = ""

    @property
    def severity(self) -> str:
        gap = self.threshold - self.actual
        if gap > 0.15:
            return "critical"
        elif gap > 0.05:
            return "warning"
        return "info"


@dataclass
class OptimizationResult:
    profitability: list[ProfitabilityRecord] = field(default_factory=list)
    ranked_levers: list[MarginLever] = field(default_factory=list)
    alerts: list[AlertCondition] = field(default_factory=list)
    expected_total_lift_pct: float = 0.0
