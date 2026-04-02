"""Core pricing data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class PricingType(str, Enum):
    FIXED = "fixed"
    TIERED = "tiered"
    SUBSCRIPTION = "subscription"
    HYBRID = "hybrid"


@dataclass
class CostInputs:
    direct_labor: float = 0.0
    indirect_labor: float = 0.0
    tooling: float = 0.0
    delivery: float = 0.0
    support: float = 0.0
    acquisition: float = 0.0
    overhead: float = 0.0

    @property
    def total_cost(self) -> float:
        return (
            self.direct_labor
            + self.indirect_labor
            + self.tooling
            + self.delivery
            + self.support
            + self.acquisition
            + self.overhead
        )

    @property
    def variable_cost(self) -> float:
        return self.direct_labor + self.tooling + self.delivery

    @property
    def fixed_cost(self) -> float:
        return self.indirect_labor + self.support + self.acquisition + self.overhead


@dataclass
class Tier:
    name: str
    min_units: int
    max_units: Optional[int]  # None = unlimited
    unit_price: float


@dataclass
class DiscountRule:
    name: str
    discount_rate: float  # 0.0–1.0
    condition: str  # human-readable description


@dataclass
class PricingConfig:
    pricing_type: PricingType
    base_price: float = 0.0
    setup_fee: float = 0.0
    recurring_fee: float = 0.0
    variable_fee_per_unit: float = 0.0
    tiers: list[Tier] = field(default_factory=list)
    discount_rules: list[DiscountRule] = field(default_factory=list)
    min_acceptable_margin: float = 0.20
    target_gross_margin: float = 0.50
    target_contribution_margin: float = 0.40
    max_discount: float = 0.30
    contract_term_months: int = 12


@dataclass
class PricingResult:
    recommended_price: float
    floor_price: float
    gross_margin: float
    contribution_margin: float
    discount_applied: float
    discount_impact: float
    margin_warnings: list[str] = field(default_factory=list)
    approval_required: bool = False
