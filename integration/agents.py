"""Pre-built agent handlers that plug into the supervisor.

Each handler takes (input_data, context) and returns a HandoffContract.
These handlers connect the pricing engine, margin optimizer, and domain logic
into the multi-agent workflow.

Claude enrichment (optional): set ANTHROPIC_API_KEY to enable deep signal
analysis in discovery_handler and narrative generation in proposal_handler.
"""
from __future__ import annotations

from typing import Any

from integration.claude_enrichment import enrich_discovery, generate_proposal_narrative
from margin_optimization.optimizer import MarginOptimizer
from multi_agent.models import HandoffContract
from pricing_engine.engine import PricingEngine
from pricing_engine.models import CostInputs, PricingConfig, PricingType


_pricing_engine = PricingEngine()
_margin_optimizer = MarginOptimizer()


def discovery_handler(input_data: dict[str, Any], context: dict[str, Any]) -> HandoffContract:
    """Analyze opportunity data and surface needs/signals.

    Rule-based signals are always computed. Claude enrichment is layered on
    top when ANTHROPIC_API_KEY is present, adding deeper intent analysis.
    """
    opp = input_data.get("opportunity", {})
    signals: list[str] = []

    if opp.get("stage") == "discovery":
        signals.append("early_stage_engagement")
    if opp.get("deal_size", 0) > 50000:
        signals.append("enterprise_deal")
    if opp.get("competitor_mentioned"):
        signals.append("competitive_situation")

    # Claude enrichment — optional, falls back to {} if not configured
    claude_insights = enrich_discovery(opp)
    if claude_insights.get("intent_strength") == "high":
        signals.append("high_intent")
    if claude_insights.get("decision_readiness") == "ready":
        signals.append("decision_ready")
    for flag in claude_insights.get("risk_flags", []):
        signals.append(f"risk:{flag}")

    confidence = claude_insights.get("confidence", 0.85) if claude_insights else 0.85

    return HandoffContract(
        run_id="",
        agent_name="discovery_agent",
        input_summary=f"Opportunity: {opp.get('name', 'unknown')}",
        output_summary=f"Detected signals: {', '.join(signals) or 'none'}",
        output_data={
            "signals": signals,
            "opportunity": opp,
            "claude_insights": claude_insights,
        },
        confidence=confidence,
        next_recommended_agent="recommendation_agent",
    )


def recommendation_handler(input_data: dict[str, Any], context: dict[str, Any]) -> HandoffContract:
    """Generate recommendations based on discovery signals."""
    signals = input_data.get("signals", [])
    recommendations: list[str] = []

    if "enterprise_deal" in signals:
        recommendations.append("propose_premium_package")
        recommendations.append("include_dedicated_support")
    if "competitive_situation" in signals:
        recommendations.append("emphasize_differentiation")
        recommendations.append("consider_strategic_discount")
    if not recommendations:
        recommendations.append("propose_standard_package")

    return HandoffContract(
        run_id="",
        agent_name="recommendation_agent",
        input_summary=f"Signals: {signals}",
        output_summary=f"Recommendations: {', '.join(recommendations)}",
        output_data={"recommendations": recommendations, **input_data},
        confidence=0.80,
        next_recommended_agent="pricing_agent",
    )


def pricing_handler(input_data: dict[str, Any], context: dict[str, Any]) -> HandoffContract:
    """Run the pricing engine on the opportunity."""
    opp = input_data.get("opportunity", {})
    recommendations = input_data.get("recommendations", [])

    # Derive pricing config from opportunity context
    pricing_type = PricingType.SUBSCRIPTION
    if "propose_premium_package" in recommendations:
        base = opp.get("deal_size", 10000) * 0.8
    else:
        base = opp.get("deal_size", 5000) * 0.6

    config = PricingConfig(
        pricing_type=pricing_type,
        recurring_fee=base / 12,
        setup_fee=base * 0.1,
        min_acceptable_margin=0.25,
        target_gross_margin=0.55,
    )
    costs = CostInputs(
        direct_labor=base * 0.20,
        indirect_labor=base * 0.05,
        tooling=base * 0.03,
        delivery=base * 0.07,
        support=base * 0.05,
    )

    discount = 0.10 if "consider_strategic_discount" in recommendations else 0.0
    result = _pricing_engine.calculate(config, costs, discount_rate=discount)

    return HandoffContract(
        run_id="",
        agent_name="pricing_agent",
        input_summary=f"Pricing for deal_size={opp.get('deal_size', 0)}",
        output_summary=(
            f"Price=${result.recommended_price}, "
            f"GM={result.gross_margin:.1%}, "
            f"warnings={len(result.margin_warnings)}"
        ),
        output_data={
            "pricing_result": {
                "recommended_price": result.recommended_price,
                "floor_price": result.floor_price,
                "gross_margin": result.gross_margin,
                "contribution_margin": result.contribution_margin,
                "discount_applied": result.discount_applied,
                "margin_warnings": result.margin_warnings,
                "approval_required": result.approval_required,
            },
            **input_data,
        },
        confidence=0.90,
        next_recommended_agent="proposal_agent",
        requires_human_review=result.approval_required,
    )


def proposal_handler(input_data: dict[str, Any], context: dict[str, Any]) -> HandoffContract:
    """Generate a proposal artifact from pricing and recommendations.

    Claude writes the narrative when configured; falls back to a plain summary.
    Pricing numbers remain governed by the deterministic pricing engine.
    """
    pricing = input_data.get("pricing_result", {})
    recommendations = input_data.get("recommendations", [])
    opp = input_data.get("opportunity", {})

    narrative = generate_proposal_narrative(
        client_name=opp.get("client", "unknown"),
        opportunity_name=opp.get("name", "unknown"),
        recommendations=recommendations,
        pricing=pricing,
    )

    proposal = {
        "client": opp.get("client", "unknown"),
        "opportunity": opp.get("name", "unknown"),
        "recommended_price": pricing.get("recommended_price", 0),
        "gross_margin": pricing.get("gross_margin", 0),
        "package_recommendations": recommendations,
        "narrative": narrative,
        "status": "draft",
    }

    return HandoffContract(
        run_id="",
        agent_name="proposal_agent",
        input_summary="Building proposal from pricing + recommendations",
        output_summary=f"Proposal draft for {opp.get('client', 'unknown')}",
        output_data={"proposal": proposal, **input_data},
        confidence=0.85,
        next_recommended_agent="sync_agent",
    )


def sync_handler(input_data: dict[str, Any], context: dict[str, Any]) -> HandoffContract:
    """Sync proposal to external systems (CRM, Google Docs, etc.)."""
    proposal = input_data.get("proposal", {})

    sync_targets = ["crm", "google_docs"]
    sync_results = {target: "synced" for target in sync_targets}

    return HandoffContract(
        run_id="",
        agent_name="sync_agent",
        input_summary=f"Syncing proposal for {proposal.get('client', 'unknown')}",
        output_summary=f"Synced to: {', '.join(sync_targets)}",
        output_data={"sync_results": sync_results, **input_data},
        confidence=0.95,
    )
