---
title: Gigaton Engine — Claude Operating Guide
version: 1.0
status: active
created: 2026-04-01
role: project-system-prompt
priority: critical
tags:
  - gigaton
  - pricing-engine
  - margin-optimization
  - multi-agent
  - fastapi
  - playa-del-carmen
---

# Project Identity

**Gigaton Engine** is the core FastAPI backend powering the Gigaton platform — a property technology and AI services company focused on the Playa del Carmen short-term and long-term rental market.

Key capabilities:
- **Pricing Engine** — cost-aware, margin-governed price computation with tiered/bundle/subscription models
- **Margin Optimization** — real-time optimization of operating margins against configurable thresholds
- **Multi-Agent Coordination** — orchestrates AI agent deployments across property workflows
- **Trigger Engine** — real-time event processing for property and market signals

# Architecture

```
gigaton-engine/
  main.py                 — FastAPI app factory, router wiring
  integration/wiring.py   — Dependency injection / container setup
  pricing_engine/
    api.py                — POST /pricing/calculate, POST /pricing/quote, GET /pricing/analyze
    engine.py             — Core pricing computation logic
    models.py             — PricingConfig, Tier, DiscountRule, CostInputs
  margin_optimization/    — Margin modeling and optimization
  multi_agent/            — Agent coordination layer
  trigger_engine/         — Event stream processing
  requirements.txt        — fastapi, uvicorn, pydantic
```

# Pricing Engine

**Pricing types**: `flat` | `tiered` | `subscription` | `usage_based` | `bundle`

**Margin governance** (non-negotiable):
- `min_acceptable_margin` — floor (default 20%). Reject any price below this.
- `target_gross_margin` — goal (default 50%). Optimize toward this.
- `target_contribution_margin` — contribution target (default 40%).
- `max_discount` — ceiling on discounts (default 30%).

**Cost structure** (from `CostInputs`):
```
direct_labor + indirect_labor + tooling + delivery + support + acquisition + overhead
```

# DAG Causal Model — Playa del Carmen ROI

Source: `gigaton_playa_roisummary.xlsx` (Downloads folder). This is the causal graph that governs how exogenous and treatment variables drive conversion, occupancy, and revenue outcomes for short-term rental properties.

**Exogenous (market inputs)**:
- `Seasonality_Index` — seasonal demand strength (0–1)
- `Macro_Demand_Index` — tourism demand index (child of Seasonality_Index)
- `Market_Supply_Index` — competing listings pressure

**Treatment (operator-controlled)**:
- `Media_Quality_Index` — photography/3D/video quality (0–10)
- `Listing_Price_Relative` — price vs market median (1.05 = 5% above)
- `Marketing_Impressions` — paid + organic impressions per period
- `Response_Time_Min` — WhatsApp median response time (minutes)
- `Partner_Agency_Score` — partner agency quality (0–10)

**Outcome nodes** (derived from Occ_Coeffs, Conv_Coeffs, Rev_Coeffs sheets):
- Conversion rate, Occupancy rate, Revenue per property

**DAG sheet names in xlsx**: `DAG_Nodes`, `Conv_Coeffs`, `Occ_Coeffs`, `Rev_Coeffs`, `Scenarios`, `Channel_Scenario`, `Owner_Summary`

# Market Context (from company_valuation_model.xlsx)

- **Target market**: Playa del Carmen short-term + long-term rentals
- **TAM**: ~$985M (25,000 STR units × $25K/yr + 15,000 LTR units × $12K/yr)
- **Operating margin target**: 30%
- **1.5% market share** = ~$14.8M revenue, ~$4.4M profit
- **Short-term unit avg annual rent**: $25,000 (70% occupancy × avg daily rate)
- **Long-term unit avg annual rent**: $12,000

# Development Rules

1. **Margin floor is hard** — never generate a price below `min_acceptable_margin`. Raise an HTTP 422 if the computed price fails margin governance.
2. **Pricing type routing** — `tiered` pricing requires at least one tier in the request; validate before computation.
3. **DAG coefficients** — when updating `Occ_Coeffs`, `Conv_Coeffs`, or `Rev_Coeffs`, update the xlsx source first, then regenerate the Python coefficient dictionaries. The xlsx is the source of truth.
4. **Dependency injection** — all dependencies wired through `integration/wiring.py`. Do not instantiate engines directly in route handlers.
5. **No hard-coded currency** — all monetary values in USD by convention unless explicitly parameterized.

# Org Alignment

Gigaton Engine serves as the commercial logic backbone for:
- **Carmen Beach Properties** — pricing and margin data feeds property service packages
- **Sales Operating System** — catalog item prices and ROI projections reference engine outputs
- **Gigaton UI System** — consumes this API exclusively

The DAG model here is the analytical foundation for all property ROI claims made to owners and investors.
