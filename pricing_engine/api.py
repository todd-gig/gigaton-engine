"""FastAPI routes for the Pricing Engine."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .engine import PricingEngine
from .models import (
    CostInputs,
    DiscountRule,
    PricingConfig,
    PricingType,
    Tier,
)

router = APIRouter(prefix="/pricing", tags=["pricing"])
_engine = PricingEngine()


# ── Request / Response schemas ────────────────────────────────────────


class TierSchema(BaseModel):
    name: str
    min_units: int
    max_units: int | None = None
    unit_price: float


class DiscountRuleSchema(BaseModel):
    name: str
    discount_rate: float = Field(ge=0.0, le=1.0)
    condition: str = ""


class CostInputsSchema(BaseModel):
    direct_labor: float = 0.0
    indirect_labor: float = 0.0
    tooling: float = 0.0
    delivery: float = 0.0
    support: float = 0.0
    acquisition: float = 0.0
    overhead: float = 0.0


class PricingRequest(BaseModel):
    pricing_type: PricingType
    base_price: float = 0.0
    setup_fee: float = 0.0
    recurring_fee: float = 0.0
    variable_fee_per_unit: float = 0.0
    tiers: list[TierSchema] = []
    discount_rules: list[DiscountRuleSchema] = []
    min_acceptable_margin: float = 0.20
    target_gross_margin: float = 0.50
    target_contribution_margin: float = 0.40
    max_discount: float = 0.30
    contract_term_months: int = 12
    costs: CostInputsSchema
    units: int = 1
    discount_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class PricingResponse(BaseModel):
    recommended_price: float
    floor_price: float
    gross_margin: float
    contribution_margin: float
    discount_applied: float
    discount_impact: float
    margin_warnings: list[str]
    approval_required: bool


# ── Endpoints ─────────────────────────────────────────────────────────


@router.post("/calculate", response_model=PricingResponse)
def calculate_price(req: PricingRequest) -> PricingResponse:
    config = PricingConfig(
        pricing_type=req.pricing_type,
        base_price=req.base_price,
        setup_fee=req.setup_fee,
        recurring_fee=req.recurring_fee,
        variable_fee_per_unit=req.variable_fee_per_unit,
        tiers=[
            Tier(
                name=t.name,
                min_units=t.min_units,
                max_units=t.max_units,
                unit_price=t.unit_price,
            )
            for t in req.tiers
        ],
        discount_rules=[
            DiscountRule(name=d.name, discount_rate=d.discount_rate, condition=d.condition)
            for d in req.discount_rules
        ],
        min_acceptable_margin=req.min_acceptable_margin,
        target_gross_margin=req.target_gross_margin,
        target_contribution_margin=req.target_contribution_margin,
        max_discount=req.max_discount,
        contract_term_months=req.contract_term_months,
    )
    costs = CostInputs(
        direct_labor=req.costs.direct_labor,
        indirect_labor=req.costs.indirect_labor,
        tooling=req.costs.tooling,
        delivery=req.costs.delivery,
        support=req.costs.support,
        acquisition=req.costs.acquisition,
        overhead=req.costs.overhead,
    )
    try:
        result = _engine.calculate(config, costs, units=req.units, discount_rate=req.discount_rate)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return PricingResponse(
        recommended_price=result.recommended_price,
        floor_price=result.floor_price,
        gross_margin=result.gross_margin,
        contribution_margin=result.contribution_margin,
        discount_applied=result.discount_applied,
        discount_impact=result.discount_impact,
        margin_warnings=result.margin_warnings,
        approval_required=result.approval_required,
    )
