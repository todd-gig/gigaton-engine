"""FastAPI routes for Margin Optimization."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from .dag_model import (
    ChannelScenario,
    GigatonDAG,
    ScenarioInputs,
)
from .models import (
    Dimension,
    ImpactSpeed,
    LeverCategory,
    MarginLever,
    ProfitabilityRecord,
    RiskLevel,
)
from .optimizer import MarginOptimizer

router = APIRouter(prefix="/margin", tags=["margin"])


# ── Schemas ────────────────────────────────────────────────────────────


class ProfitabilitySchema(BaseModel):
    name: str
    dimension: Dimension
    revenue: float
    direct_cost: float
    variable_cost: float
    total_cost: float


class LeverSchema(BaseModel):
    category: LeverCategory
    description: str
    estimated_margin_lift_pct: float
    speed: ImpactSpeed
    difficulty: RiskLevel
    revenue_risk: RiskLevel


class OptimizeRequest(BaseModel):
    records: list[ProfitabilitySchema]
    levers: list[LeverSchema]
    min_gross_margin: float = 0.20
    target_gross_margin: float = 0.50


class AlertSchema(BaseModel):
    rule: str
    threshold: float
    actual: float
    triggered: bool
    entity_name: str
    severity: str


class RankedLeverSchema(BaseModel):
    category: LeverCategory
    description: str
    estimated_margin_lift_pct: float
    speed: ImpactSpeed
    difficulty: RiskLevel
    revenue_risk: RiskLevel
    priority_score: float


class OptimizeResponse(BaseModel):
    profitability: list[ProfitabilitySchema]
    ranked_levers: list[RankedLeverSchema]
    alerts: list[AlertSchema]
    expected_total_lift_pct: float


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/optimize", response_model=OptimizeResponse)
def optimize_margins(req: OptimizeRequest) -> OptimizeResponse:
    records = [
        ProfitabilityRecord(
            name=r.name,
            dimension=r.dimension,
            revenue=r.revenue,
            direct_cost=r.direct_cost,
            variable_cost=r.variable_cost,
            total_cost=r.total_cost,
        )
        for r in req.records
    ]
    levers = [
        MarginLever(
            category=lv.category,
            description=lv.description,
            estimated_margin_lift_pct=lv.estimated_margin_lift_pct,
            speed=lv.speed,
            difficulty=lv.difficulty,
            revenue_risk=lv.revenue_risk,
        )
        for lv in req.levers
    ]
    optimizer = MarginOptimizer(
        min_gross_margin=req.min_gross_margin,
        target_gross_margin=req.target_gross_margin,
    )
    result = optimizer.evaluate(records, levers)

    return OptimizeResponse(
        profitability=[
            ProfitabilitySchema(
                name=p.name,
                dimension=p.dimension,
                revenue=p.revenue,
                direct_cost=p.direct_cost,
                variable_cost=p.variable_cost,
                total_cost=p.total_cost,
            )
            for p in result.profitability
        ],
        ranked_levers=[
            RankedLeverSchema(
                category=lv.category,
                description=lv.description,
                estimated_margin_lift_pct=lv.estimated_margin_lift_pct,
                speed=lv.speed,
                difficulty=lv.difficulty,
                revenue_risk=lv.revenue_risk,
                priority_score=round(lv.priority_score, 4),
            )
            for lv in result.ranked_levers
        ],
        alerts=[
            AlertSchema(
                rule=a.rule,
                threshold=a.threshold,
                actual=a.actual,
                triggered=a.triggered,
                entity_name=a.entity_name,
                severity=a.severity,
            )
            for a in result.alerts
        ],
        expected_total_lift_pct=result.expected_total_lift_pct,
    )


# ── DAG / Property ROI Endpoints ───────────────────────────────────────


class DAGInputsSchema(BaseModel):
    seasonality_index: float = 0.70
    macro_demand_index: float = 0.70
    market_supply_index: float = 1.00
    media_quality_index: float = 7.0
    listing_price_relative: float = 1.00
    marketing_impressions: float = 10_000
    response_time_min: float = 10.0
    partner_agency_score: float = 7.0
    nights_per_month: int = 30
    baseline_nightly_rate_mxn: float = 1_800.0
    avg_length_of_stay: float = 3.5
    variable_cost_per_booked_night_mxn: float = 600.0
    fixed_costs_per_month_mxn: float = 20_000.0
    lead_quality_score: float = 6.0


class DAGResultSchema(BaseModel):
    conversion_rate: float
    occupancy_rate: float
    booked_nights: float
    nightly_rate_realized_mxn: float
    monthly_gross_revenue_mxn: float
    monthly_contribution_margin_mxn: float
    monthly_net_profit_mxn: float
    monthly_gross_revenue_usd: float
    monthly_net_profit_usd: float
    annual_net_profit_usd: float
    contribution_margin_pct: float


class ChannelScenarioSchema(BaseModel):
    name: str
    channels: int
    nightly_rate_mxn: float
    occupancy_rate: float
    booked_nights: float
    gross_revenue_mxn: float
    net_profit_usd: float
    annual_net_profit_usd: float


@router.post("/dag/run", response_model=DAGResultSchema, tags=["dag"])
def run_dag(inputs: DAGInputsSchema) -> DAGResultSchema:
    """
    Run the Gigaton Playa del Carmen property ROI causal DAG model.

    Computes conversion rate, occupancy rate, revenue, contribution margin,
    and net profit from operator-controlled and market inputs.
    """
    dag = GigatonDAG()
    inp = ScenarioInputs(**inputs.model_dump())
    r = dag.run(inp)
    return DAGResultSchema(
        conversion_rate=round(r.conversion_rate, 4),
        occupancy_rate=round(r.occupancy_rate, 4),
        booked_nights=round(r.booked_nights, 2),
        nightly_rate_realized_mxn=round(r.nightly_rate_realized_mxn, 2),
        monthly_gross_revenue_mxn=round(r.monthly_gross_revenue_mxn, 2),
        monthly_contribution_margin_mxn=round(r.monthly_contribution_margin_mxn, 2),
        monthly_net_profit_mxn=round(r.monthly_net_profit_mxn, 2),
        monthly_gross_revenue_usd=round(r.monthly_gross_revenue_usd, 2),
        monthly_net_profit_usd=round(r.monthly_net_profit_usd, 2),
        annual_net_profit_usd=round(r.annual_net_profit_usd, 2),
        contribution_margin_pct=round(r.contribution_margin_pct, 4),
    )


@router.get("/dag/channel-scenarios", response_model=list[ChannelScenarioSchema], tags=["dag"])
def channel_scenarios() -> list[ChannelScenarioSchema]:
    """
    Return the three Gigaton channel distribution scenarios:
    baseline (1 channel), manual multi-channel (3), Gigaton orchestrated (6 + AI).

    Parameters sourced from gigaton_playa_roisummary.xlsx / Channel_Scenario sheet.
    """
    scenarios = ChannelScenario.compare_all()
    return [
        ChannelScenarioSchema(
            name=s.name,
            channels=s.channels,
            nightly_rate_mxn=round(s.nightly_rate_mxn, 2),
            occupancy_rate=round(s.occupancy_rate, 4),
            booked_nights=round(s.booked_nights, 2),
            gross_revenue_mxn=round(s.gross_revenue_mxn, 2),
            net_profit_usd=round(s.net_profit_usd, 2),
            annual_net_profit_usd=round(s.annual_net_profit_usd, 2),
        )
        for s in scenarios
    ]
