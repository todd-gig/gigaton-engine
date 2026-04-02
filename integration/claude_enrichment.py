"""
claude_enrichment.py
Claude-powered enrichment for the multi-agent pipeline.

Adds natural-language reasoning to the discovery and proposal stages
without touching the pricing computation (which remains deterministic
and margin-governed). Claude discovers signal; Python governs price.

Required env var:
    ANTHROPIC_API_KEY — Anthropic API key
"""
from __future__ import annotations

import json
import os
from typing import Any

try:
    import anthropic
    _ANTHROPIC_AVAILABLE = True
except ImportError:
    _ANTHROPIC_AVAILABLE = False


MODEL = "claude-opus-4-6"
_client: "anthropic.Anthropic | None" = None


def _get_client() -> "anthropic.Anthropic":
    global _client
    if not _ANTHROPIC_AVAILABLE:
        raise RuntimeError(
            "anthropic package is not installed. "
            "Run: pip install anthropic"
        )
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY env var is required for Claude enrichment")
        _client = anthropic.Anthropic(api_key=api_key)
    return _client


def is_available() -> bool:
    """True if Claude enrichment is configured and available."""
    return _ANTHROPIC_AVAILABLE and bool(os.environ.get("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Discovery enrichment
# ---------------------------------------------------------------------------

def enrich_discovery(opportunity: dict[str, Any]) -> dict[str, Any]:
    """
    Use Claude to perform deep signal analysis on an opportunity.
    Returns enriched signals dict to supplement rule-based discovery.

    Falls back to empty dict if Claude is not configured.
    """
    if not is_available():
        return {}

    prompt = f"""You are a B2B sales intelligence analyst. Analyze this sales opportunity and extract signals.

OPPORTUNITY:
{json.dumps(opportunity, indent=2)}

Return ONLY valid JSON with this schema:
{{
  "intent_strength": "high|medium|low",
  "decision_readiness": "ready|evaluating|early",
  "risk_flags": ["string"],
  "opportunity_summary": "one sentence",
  "recommended_approach": "consultative|transactional|enterprise|strategic",
  "confidence": 0.0-1.0
}}

Return ONLY the JSON object."""

    client = _get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=512,
        messages=[{"role": "user", "content": prompt}],
    )

    text = message.content[0].text if message.content else "{}"
    try:
        import re
        match = re.search(r"\{[\s\S]*\}", text)
        return json.loads(match.group(0)) if match else {}
    except (json.JSONDecodeError, AttributeError):
        return {}


# ---------------------------------------------------------------------------
# Proposal narrative generation
# ---------------------------------------------------------------------------

def generate_proposal_narrative(
    client_name: str,
    opportunity_name: str,
    recommendations: list[str],
    pricing: dict[str, Any],
) -> str:
    """
    Use Claude to write a professional proposal narrative.
    Returns a markdown string suitable for inclusion in a proposal document.

    Falls back to a plain-text summary if Claude is not configured.
    """
    if not is_available():
        return _fallback_narrative(client_name, opportunity_name, recommendations, pricing)

    prompt = f"""You are a senior account executive writing a B2B proposal for a property technology company.

Write a professional proposal narrative (3-4 paragraphs) in markdown.

CLIENT: {client_name}
OPPORTUNITY: {opportunity_name}
RECOMMENDED PACKAGES: {', '.join(recommendations)}
PROPOSED PRICE: ${pricing.get('recommended_price', 0):,.2f}
GROSS MARGIN: {pricing.get('gross_margin', 0):.1%}
APPROVAL REQUIRED: {pricing.get('approval_required', False)}

Guidelines:
- Lead with the business outcome, not the product
- Reference the specific packages by name
- Justify the investment with ROI framing
- Close with a clear call to action
- Professional but conversational tone
- Do NOT include price/margin numbers (those appear separately)

Return only the markdown narrative."""

    client = _get_client()
    message = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text if message.content else _fallback_narrative(
        client_name, opportunity_name, recommendations, pricing
    )


def _fallback_narrative(
    client_name: str,
    opportunity_name: str,
    recommendations: list[str],
    pricing: dict[str, Any],
) -> str:
    packages = ", ".join(recommendations) if recommendations else "standard package"
    return (
        f"## Proposal for {client_name}\n\n"
        f"**Opportunity:** {opportunity_name}\n\n"
        f"We recommend the following: {packages}.\n\n"
        f"Proposed price: ${pricing.get('recommended_price', 0):,.2f}"
    )
