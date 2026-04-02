"""
dag_model.py
────────────
Playa del Carmen Property ROI — Causal DAG Model

Implements the structural causal equations from gigaton_playa_roisummary.xlsx:
  - Conversion Rate: logistic model on lead quality, price, response time, media
  - Occupancy Rate:  linear model on lead volume, conversion, ALOS, supply
  - Monthly Gross Revenue: linear from occupancy and nightly rate
  - Contribution Margin and Net Profit

Also implements the Channel Scenario model:
  - Baseline (1 channel):                 45% occupancy
  - Manual multi-channel (3 channels):    +5% per channel
  - Gigaton orchestrated (6 channels):    +10% AI uplift + channel uplift

Source of truth: gigaton_playa_roisummary.xlsx (Downloads/Desktop)
Coefficient calibration: scripts/calibrate_dag_from_xlsx.py

Usage:
    from margin_optimization.dag_model import GigatonDAG, ChannelScenario, ScenarioInputs

    dag = GigatonDAG()
    result = dag.run(ScenarioInputs())
    print(result)

    # Channel comparison
    scenarios = ChannelScenario.compare_all()
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Default calibrated coefficients
# Calibrated against:
#   - Baseline ADR: $1,800 MXN/night (≈$90 USD)
#   - Baseline occupancy: 45% single-channel, 70%+ Gigaton orchestrated
#   - Baseline conversion rate: ~3–6% for Playa del Carmen STR market
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ConversionCoeffs:
    """Logistic regression coefficients for Conversion Rate."""
    intercept: float = -3.5          # baseline log-odds
    lead_quality_score: float = 0.25  # 0–10 scale; higher quality → higher CR
    listing_price_relative: float = -1.2  # 1.0 = at market; >1 penalizes CR
    response_time_min: float = -0.03   # minutes to respond; faster = better
    media_quality_index: float = 0.20  # 0–10 scale; better media → higher CR


@dataclass
class OccupancyCoeffs:
    """Linear regression coefficients for Occupancy Rate (0–1).
    Intercept calibrated so that default ScenarioInputs → ~45% occupancy,
    matching the Channel_Scenario baseline in gigaton_playa_roisummary.xlsx.
    """
    intercept: float = 0.40
    lead_volume: float = 0.000008     # impressions → leads pipeline effect
    conversion_rate: float = 0.60     # main driver: CR directly lifts occupancy
    avg_length_of_stay: float = 0.015  # longer stays → better occupancy signal
    market_supply_index: float = -0.08  # more competition → lower occupancy


@dataclass
class RevenueCoeffs:
    """Linear regression coefficients for Monthly Gross Revenue (MXN)."""
    intercept: float = 0.0
    occupancy_rate: float = 1.0       # applied as multiplier below
    nightly_rate_realized: float = 1.0  # applied as multiplier below


# ─────────────────────────────────────────────────────────────────────────────
# Input / Output dataclasses
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ScenarioInputs:
    """
    Exogenous (market) + Treatment (operator-controlled) inputs.
    Defaults represent a typical Playa del Carmen baseline scenario.
    """
    # Exogenous
    seasonality_index: float = 0.70       # 0–1; 1 = peak season
    macro_demand_index: float = 0.70      # 0–1; tourism demand strength
    market_supply_index: float = 1.00     # relative listing competition; 1 = at market

    # Treatment (operator-controlled)
    media_quality_index: float = 7.0      # 0–10; photography/3D/video quality
    listing_price_relative: float = 1.00  # price vs market median (1.05 = 5% above)
    marketing_impressions: float = 10_000  # paid + organic impressions/month
    response_time_min: float = 10.0       # median WhatsApp response time (minutes)
    partner_agency_score: float = 7.0     # 0–10; agency quality/strength

    # Property economics
    nights_per_month: int = 30
    baseline_nightly_rate_mxn: float = 1_800.0   # MXN; Playa del Carmen baseline
    avg_length_of_stay: float = 3.5              # nights
    variable_cost_per_booked_night_mxn: float = 600.0  # MXN cleaning + consumables
    fixed_costs_per_month_mxn: float = 20_000.0         # MXN; insurance, utilities, mgmt

    # Derived assumption
    lead_quality_score: float = 6.0       # 0–10; inferred from funnel signals


@dataclass
class ScenarioResult:
    """Computed output from the DAG model."""
    # Intermediate
    conversion_rate: float = 0.0         # fraction (0–1)
    lead_volume_per_month: float = 0.0
    occupancy_rate: float = 0.0          # fraction (0–1)
    booked_nights: float = 0.0
    nightly_rate_realized_mxn: float = 0.0

    # Financial outputs (MXN)
    monthly_gross_revenue_mxn: float = 0.0
    monthly_variable_costs_mxn: float = 0.0
    monthly_contribution_margin_mxn: float = 0.0
    monthly_net_profit_mxn: float = 0.0

    # USD equivalents (at 17 MXN/USD)
    monthly_gross_revenue_usd: float = 0.0
    monthly_net_profit_usd: float = 0.0
    annual_net_profit_usd: float = 0.0

    # Diagnostics
    contribution_margin_pct: float = 0.0
    inputs: Optional[ScenarioInputs] = None

    def __str__(self) -> str:
        return (
            f"Conversion Rate:         {self.conversion_rate:.1%}\n"
            f"Occupancy Rate:          {self.occupancy_rate:.1%}\n"
            f"Booked Nights/Month:     {self.booked_nights:.1f}\n"
            f"Nightly Rate:            ${self.nightly_rate_realized_mxn:,.0f} MXN  "
            f"(${self.nightly_rate_realized_mxn / 17:.0f} USD)\n"
            f"Monthly Gross Revenue:   ${self.monthly_gross_revenue_mxn:,.0f} MXN  "
            f"(${self.monthly_gross_revenue_usd:,.0f} USD)\n"
            f"Contribution Margin:     ${self.monthly_contribution_margin_mxn:,.0f} MXN  "
            f"({self.contribution_margin_pct:.1%})\n"
            f"Monthly Net Profit:      ${self.monthly_net_profit_mxn:,.0f} MXN  "
            f"(${self.monthly_net_profit_usd:,.0f} USD)\n"
            f"Annual Net Profit:       ${self.annual_net_profit_usd:,.0f} USD\n"
        )


# ─────────────────────────────────────────────────────────────────────────────
# DAG Engine
# ─────────────────────────────────────────────────────────────────────────────

MXN_TO_USD = 1 / 17.0  # 17 MXN per USD (update as needed)


class GigatonDAG:
    """
    Causal DAG model for Playa del Carmen property ROI.

    Structural equations (from gigaton_playa_roisummary.xlsx / Equations_Notes):

    1. Conversion_Rate = logistic(b0 + b1*Lead_Quality + b2*Price_Rel + b3*Resp_Time + b4*Media_Quality)
    2. Occupancy_Rate  = c0 + c1*Lead_Vol + c2*CR + c3*ALOS + c4*Market_Supply
    3. Monthly_Gross_Revenue = Occ_Rate * Nights_per_Month * Nightly_Rate
    4. Monthly_Contribution_Margin = Rev - (Booked_Nights * Variable_Cost)
    5. Monthly_Net_Profit = CM - Fixed_Costs
    """

    def __init__(
        self,
        conv_coeffs: Optional[ConversionCoeffs] = None,
        occ_coeffs: Optional[OccupancyCoeffs] = None,
        rev_coeffs: Optional[RevenueCoeffs] = None,
    ):
        self.conv = conv_coeffs or ConversionCoeffs()
        self.occ = occ_coeffs or OccupancyCoeffs()
        self.rev = rev_coeffs or RevenueCoeffs()

    # ── Node computations ─────────────────────────────────────────────────────

    def conversion_rate(self, inp: ScenarioInputs) -> float:
        """Logistic model: CR = 1 / (1 + exp(-linear_combination))"""
        linear = (
            self.conv.intercept
            + self.conv.lead_quality_score * inp.lead_quality_score
            + self.conv.listing_price_relative * inp.listing_price_relative
            + self.conv.response_time_min * inp.response_time_min
            + self.conv.media_quality_index * inp.media_quality_index
        )
        return 1.0 / (1.0 + math.exp(-linear))

    def lead_volume(self, inp: ScenarioInputs) -> float:
        """Impressions → qualified lead pipeline (simplified linear decay)."""
        return inp.marketing_impressions * 0.02 * inp.macro_demand_index * inp.seasonality_index

    def nightly_rate_realized(self, inp: ScenarioInputs) -> float:
        """Realized nightly rate = baseline * price_relative * seasonality."""
        return inp.baseline_nightly_rate_mxn * inp.listing_price_relative * (
            0.8 + 0.2 * inp.seasonality_index
        )

    def occupancy_rate(self, inp: ScenarioInputs, cr: float, lv: float) -> float:
        """Linear model for occupancy. Clipped to [0.05, 0.98]."""
        occ = (
            self.occ.intercept
            + self.occ.lead_volume * lv
            + self.occ.conversion_rate * cr
            + self.occ.avg_length_of_stay * inp.avg_length_of_stay
            + self.occ.market_supply_index * inp.market_supply_index
        )
        return max(0.05, min(0.98, occ))

    # ── Full DAG run ──────────────────────────────────────────────────────────

    def run(self, inp: ScenarioInputs) -> ScenarioResult:
        cr = self.conversion_rate(inp)
        lv = self.lead_volume(inp)
        occ = self.occupancy_rate(inp, cr, lv)
        rate = self.nightly_rate_realized(inp)

        booked_nights = occ * inp.nights_per_month
        gross_rev_mxn = booked_nights * rate
        var_costs_mxn = booked_nights * inp.variable_cost_per_booked_night_mxn
        cm_mxn = gross_rev_mxn - var_costs_mxn
        net_profit_mxn = cm_mxn - inp.fixed_costs_per_month_mxn

        cm_pct = cm_mxn / gross_rev_mxn if gross_rev_mxn > 0 else 0.0

        return ScenarioResult(
            conversion_rate=cr,
            lead_volume_per_month=lv,
            occupancy_rate=occ,
            booked_nights=booked_nights,
            nightly_rate_realized_mxn=rate,
            monthly_gross_revenue_mxn=gross_rev_mxn,
            monthly_variable_costs_mxn=var_costs_mxn,
            monthly_contribution_margin_mxn=cm_mxn,
            monthly_net_profit_mxn=net_profit_mxn,
            monthly_gross_revenue_usd=gross_rev_mxn * MXN_TO_USD,
            monthly_net_profit_usd=net_profit_mxn * MXN_TO_USD,
            annual_net_profit_usd=net_profit_mxn * MXN_TO_USD * 12,
            contribution_margin_pct=cm_pct,
            inputs=inp,
        )

    def sensitivity(
        self,
        base_inp: ScenarioInputs,
        variable: str,
        values: List[float],
    ) -> List[ScenarioResult]:
        """Run the model across a range of values for one input variable."""
        results = []
        for v in values:
            inp = ScenarioInputs(**{**base_inp.__dict__, variable: v})
            results.append(self.run(inp))
        return results


# ─────────────────────────────────────────────────────────────────────────────
# Channel Scenario Model
# (from gigaton_playa_roisummary.xlsx / Channel_Scenario sheet)
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ChannelScenarioResult:
    name: str
    channels: int
    nightly_rate_mxn: float
    occupancy_rate: float
    booked_nights: float
    gross_revenue_mxn: float
    variable_costs_mxn: float
    contribution_margin_mxn: float
    net_profit_mxn: float
    net_profit_usd: float
    annual_net_profit_usd: float

    def __str__(self) -> str:
        return (
            f"{self.name}\n"
            f"  Channels:        {self.channels}\n"
            f"  Occupancy:       {self.occupancy_rate:.1%}\n"
            f"  Booked Nights:   {self.booked_nights:.1f}/mo\n"
            f"  Nightly Rate:    ${self.nightly_rate_mxn:,.0f} MXN\n"
            f"  Gross Revenue:   ${self.gross_revenue_mxn:,.0f} MXN/mo\n"
            f"  Net Profit:      ${self.net_profit_usd:,.0f} USD/mo\n"
            f"  Annual Profit:   ${self.annual_net_profit_usd:,.0f} USD/yr\n"
        )


class ChannelScenario:
    """
    Channel distribution scenario model.
    Source: gigaton_playa_roisummary.xlsx / Channel_Scenario sheet.
    """

    # Exact parameters from xlsx Channel_Scenario sheet
    NIGHTS_PER_MONTH = 30
    VARIABLE_COST_PER_BOOKED_NIGHT_MXN = 600.0
    FIXED_COSTS_PER_MONTH_MXN = 20_000.0
    BASE_OCCUPANCY_SINGLE_CHANNEL = 0.45
    UPLIFT_PER_ADDITIONAL_CHANNEL = 0.05
    GIGATON_INTELLIGENCE_EXTRA_UPLIFT = 0.10
    BASELINE_NIGHTLY_RATE_MXN = 1_800.0
    GIGATON_NIGHTLY_RATE_UPLIFT = 0.05  # 5% premium via Gigaton AI optimization

    @classmethod
    def _compute(
        cls,
        name: str,
        channels: int,
        gigaton_ai: bool = False,
    ) -> ChannelScenarioResult:
        occ = cls.BASE_OCCUPANCY_SINGLE_CHANNEL + (channels - 1) * cls.UPLIFT_PER_ADDITIONAL_CHANNEL
        if gigaton_ai:
            occ += cls.GIGATON_INTELLIGENCE_EXTRA_UPLIFT
        occ = min(occ, 0.98)

        rate = cls.BASELINE_NIGHTLY_RATE_MXN
        if gigaton_ai:
            rate *= 1.0 + cls.GIGATON_NIGHTLY_RATE_UPLIFT

        booked_nights = occ * cls.NIGHTS_PER_MONTH
        gross_rev = booked_nights * rate
        var_costs = booked_nights * cls.VARIABLE_COST_PER_BOOKED_NIGHT_MXN
        cm = gross_rev - var_costs
        net_profit_mxn = cm - cls.FIXED_COSTS_PER_MONTH_MXN
        net_profit_usd = net_profit_mxn * MXN_TO_USD

        return ChannelScenarioResult(
            name=name,
            channels=channels,
            nightly_rate_mxn=rate,
            occupancy_rate=occ,
            booked_nights=booked_nights,
            gross_revenue_mxn=gross_rev,
            variable_costs_mxn=var_costs,
            contribution_margin_mxn=cm,
            net_profit_mxn=net_profit_mxn,
            net_profit_usd=net_profit_usd,
            annual_net_profit_usd=net_profit_usd * 12,
        )

    @classmethod
    def baseline(cls) -> ChannelScenarioResult:
        """Single-channel distribution (Airbnb only)."""
        return cls._compute("Baseline — 1 channel", channels=1, gigaton_ai=False)

    @classmethod
    def manual_multichannel(cls) -> ChannelScenarioResult:
        """Manual multi-channel (Airbnb + VRBO + Booking.com)."""
        return cls._compute("Manual multi-channel — 3 channels", channels=3, gigaton_ai=False)

    @classmethod
    def gigaton_orchestrated(cls) -> ChannelScenarioResult:
        """Gigaton AI-orchestrated multi-channel (6 channels + AI uplift)."""
        return cls._compute(
            "Gigaton orchestrated multi-channel — 6 channels + AI",
            channels=6,
            gigaton_ai=True,
        )

    @classmethod
    def compare_all(cls) -> List[ChannelScenarioResult]:
        return [cls.baseline(), cls.manual_multichannel(), cls.gigaton_orchestrated()]

    @classmethod
    def print_comparison(cls) -> None:
        scenarios = cls.compare_all()
        baseline_profit = scenarios[0].net_profit_usd
        print("=" * 60)
        print("Gigaton Channel Distribution — Property ROI Comparison")
        print("=" * 60)
        for s in scenarios:
            print(s)
        gigaton = scenarios[-1]
        print(f"Monthly profit increase vs baseline: "
              f"${gigaton.net_profit_usd - baseline_profit:,.0f} USD/mo")
        print(f"Annual profit increase vs baseline:  "
              f"${(gigaton.net_profit_usd - baseline_profit) * 12:,.0f} USD/yr")
        if baseline_profit > 0:
            roi = (gigaton.net_profit_usd - baseline_profit) / baseline_profit
            print(f"ROI vs baseline:                     {roi:.1%}")
        print("=" * 60)


# ─────────────────────────────────────────────────────────────────────────────
# FastAPI integration — add to margin_optimization/api.py
# ─────────────────────────────────────────────────────────────────────────────

def get_dag() -> GigatonDAG:
    """Module-level singleton for dependency injection."""
    return GigatonDAG()


# ─────────────────────────────────────────────────────────────────────────────
# CLI / quick-run
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    dag = GigatonDAG()

    print("\n" + "=" * 60)
    print("Gigaton DAG Model — Playa del Carmen Property ROI")
    print("=" * 60)

    # Default scenario
    inp = ScenarioInputs()
    result = dag.run(inp)
    print("\nDefault Scenario:")
    print(result)

    # Gigaton-optimized scenario
    print("\nGigaton-Optimized Scenario (high media, fast response, 6 channels):")
    optimized = ScenarioInputs(
        media_quality_index=9.5,
        response_time_min=2.0,
        marketing_impressions=50_000,
        partner_agency_score=9.0,
        listing_price_relative=1.05,
        lead_quality_score=8.0,
    )
    result_opt = dag.run(optimized)
    print(result_opt)

    # Sensitivity: media quality
    print("Sensitivity — Media Quality Index (0→10):")
    sensitivity = dag.sensitivity(inp, "media_quality_index", [3, 5, 7, 9])
    for mq, r in zip([3, 5, 7, 9], sensitivity):
        print(f"  Media Quality {mq}: Occ={r.occupancy_rate:.1%}, "
              f"Net Profit ${r.monthly_net_profit_usd:,.0f}/mo USD")

    print()
    ChannelScenario.print_comparison()
