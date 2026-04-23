#!/usr/bin/env python3
"""
Gigaton Engine CLI — L1→L3→L4 Pipeline Demo

Usage:
  python -m pipeline.cli demo          Full pipeline demo (3 prospect scenarios)
  python -m pipeline.cli prospect      L1→L3 prospect analysis only
  python -m pipeline.cli scenario N    Run a specific scenario (1–3)
"""
import sys
import os
import json

# Ensure project root is on path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from datetime import datetime, timedelta

from l1_sensing.models.prospect import (
    ProspectProfile, CapabilitySummary, MaturityLevel, GTMMotion, PricingVisibility,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l4_execution.models.interaction import InteractionEvent
from pipeline.engine import GigatonEngine


# ─────────────────────────────────────────────────────────────
# DEMO SCENARIOS
# ─────────────────────────────────────────────────────────────

def _recent_iso(days_ago: int = 3) -> str:
    return (datetime.now() - timedelta(days=days_ago)).isoformat()


SCENARIOS = {
    1: {
        "name": "High-Fit SaaS Prospect → Auto-Execute",
        "description": "Strong signals, recent data, well-qualified prospect with successful interactions",
        "prospect": ProspectProfile(
            prospect_id="P001",
            domain="acmewidgets.com",
            official_name="Acme Widgets Inc.",
            industries=["Manufacturing", "E-commerce"],
            buyer_personas=["VP Marketing", "CMO"],
            service_geographies=["North America", "Europe"],
            gtm_motion=GTMMotion.SALES_LED,
            pricing_visibility=PricingVisibility.PUBLIC,
            capability_summary=CapabilitySummary(
                marketing_maturity=MaturityLevel.LOW,
                sales_complexity=MaturityLevel.MEDIUM,
                measurement_maturity=MaturityLevel.LOW,
                interaction_management_maturity=MaturityLevel.LOW,
            ),
            last_verified_at=_recent_iso(2),
            evidence_ids=["E001", "E002", "E003", "E004", "E005"],
        ),
        "inferences": [
            InferenceRecord(
                object_id="INF001", prospect_id="P001",
                inference_type=InferenceType.PAIN_POINT,
                statement="No attribution model — spending blindly on paid search",
                confidence=0.92, evidence_ids=["E001"],
            ),
            InferenceRecord(
                object_id="INF002", prospect_id="P001",
                inference_type=InferenceType.SERVICE_FIT,
                statement="Brand experience engineering + measurement infrastructure",
                confidence=0.88, evidence_ids=["E002", "E003"],
            ),
            InferenceRecord(
                object_id="INF003", prospect_id="P001",
                inference_type=InferenceType.VALUE_ESTIMATE,
                statement="Est. $2.4M annual marketing spend — 15-20% efficiency gain achievable",
                confidence=0.85, evidence_ids=["E004"],
            ),
        ],
        "interactions": [
            InteractionEvent(
                interaction_id="INT001", entity_id="actor_sales_01",
                channel="email", timestamp=_recent_iso(5),
                status="resolved", response_time_seconds=180,
                resolution_time_seconds=3600, converted=True,
                sentiment_score=0.8, trust_shift_score=0.3,
            ),
            InteractionEvent(
                interaction_id="INT002", entity_id="actor_sales_01",
                channel="voice", timestamp=_recent_iso(3),
                status="resolved", response_time_seconds=60,
                resolution_time_seconds=1800, converted=True,
                sentiment_score=0.9, trust_shift_score=0.4,
            ),
        ],
        "role_key": "sales_operator",
        "expected_verdict": "auto_execute",
    },
    2: {
        "name": "Mid-Tier Prospect → Escalate (Degraded Trust)",
        "description": "Moderate signals, weak source reliability — triggers RTQL degradation and escalation",
        "prospect": ProspectProfile(
            prospect_id="P002",
            domain="bigboxretail.com",
            official_name="BigBox Retail Corp.",
            industries=["Retail"],
            buyer_personas=["Director of Digital"],
            service_geographies=["North America"],
            gtm_motion=GTMMotion.HYBRID,
            pricing_visibility=PricingVisibility.CONTACT_SALES,
            capability_summary=CapabilitySummary(
                marketing_maturity=MaturityLevel.MEDIUM,
                sales_complexity=MaturityLevel.HIGH,
                measurement_maturity=MaturityLevel.LOW,
                interaction_management_maturity=MaturityLevel.MEDIUM,
            ),
            last_verified_at=_recent_iso(45),
            evidence_ids=["E010"],
        ),
        "inferences": [
            InferenceRecord(
                object_id="INF010", prospect_id="P002",
                inference_type=InferenceType.BUSINESS_GOAL,
                statement="Expand DTC channel to reduce wholesale dependency",
                confidence=0.35, evidence_ids=["E010"],
            ),
        ],
        "interactions": [
            InteractionEvent(
                interaction_id="INT010", entity_id="actor_ops_01",
                channel="web", timestamp=_recent_iso(10),
                status="active", response_time_seconds=900,
                converted=False, sentiment_score=0.55, trust_shift_score=0.1,
            ),
        ],
        "role_key": "operations_manager",
        "expected_verdict": "escalate_tier_1",
    },
    3: {
        "name": "Weak Signal Prospect → Needs Data",
        "description": "Insufficient intelligence — triggers data completeness gate",
        "prospect": ProspectProfile(
            prospect_id="P003",
            domain="mysterycorp.io",
            official_name="Mystery Corp",
            industries=[],
            buyer_personas=[],
            service_geographies=[],
            gtm_motion=GTMMotion.UNKNOWN,
            pricing_visibility=PricingVisibility.UNKNOWN,
            capability_summary=CapabilitySummary(),
            last_verified_at="",
            evidence_ids=[],
        ),
        "inferences": [
            InferenceRecord(
                object_id="INF020", prospect_id="P003",
                inference_type=InferenceType.GTM_MOTION,
                statement="Possibly PLG based on website copy — very low confidence",
                confidence=0.25, evidence_ids=[],
            ),
        ],
        "interactions": [
            InteractionEvent(
                interaction_id="INT020", entity_id="actor_auto_01",
                channel="web", timestamp=_recent_iso(1),
                status="abandoned", abandoned=True,
                sentiment_score=0.3, trust_shift_score=-0.2,
            ),
        ],
        "role_key": "automation_system_builder",
        "expected_verdict": "needs_data",
    },
}


# ─────────────────────────────────────────────────────────────
# OUTPUT FORMATTING
# ─────────────────────────────────────────────────────────────

def print_result(result, scenario_spec: dict):
    """Print a pipeline result in readable format."""
    expected = scenario_spec["expected_verdict"]
    passed = result.verdict == expected
    status = "✓ PASS" if passed else "✗ FAIL"

    print(f"\n{'─'*70}")
    print(f"  Scenario: {scenario_spec['name']}")
    print(f"  {scenario_spec['description']}")
    print(f"{'─'*70}")

    # L1 — Prospect Sensing
    a = result.prospect_assessment
    print(f"\n  ▸ L1 SENSING — Prospect Value Assessment")
    print(f"    Prospect:     {result.prospect_name} ({result.prospect_id})")
    print(f"    Fit Score:    {a.total:.1f}/100")
    print(f"    Components:   need={a.need:.0f}  service_fit={a.service_fit:.0f}  "
          f"readiness={a.readiness:.0f}  uplift={a.expected_uplift:.0f}  "
          f"scale={a.economic_scale:.0f}  confidence={a.confidence:.0f}")
    if a.priority_gaps:
        print(f"    Gaps:         {', '.join(a.priority_gaps)}")

    # L3 — Qualification
    print(f"\n  ▸ L3 QUALIFICATION — Decision Engine")
    print(f"    Decision:     {result.decision_id}")
    print(f"    Verdict:      {result.verdict}  [{status}]  (expected: {expected})")
    print(f"    Value:        {result.value_score:.3f}")
    print(f"    Trust:        {result.trust_score:.3f}")
    print(f"    RTQL:         stage {result.rtql_stage}/7  ×{result.rtql_multiplier:.2f}")
    print(f"    Priority:     {result.priority_score:.3f}")
    certs = result.certificates
    cert_str = "  ".join(f"{k}:{'✓' if v else '✗'}" for k, v in certs.items())
    print(f"    Certificates: {cert_str}")
    if result.blocking_gates:
        print(f"    Blocking:     {', '.join(result.blocking_gates)}")

    # L4 — Execution
    print(f"\n  ▸ L4 EXECUTION — Interaction Matrix")
    print(f"    Interactions: {result.interaction_count}")
    print(f"    Avg NOCS:     {result.avg_nocs:.2f}")
    print(f"    Total Comp:   ${result.total_compensation:,.2f}")
    for ir in result.interaction_results:
        print(f"      [{ir.channel}] {ir.interaction_id}: "
              f"NOCS={ir.nocs.final_nocs:.1f}  comp=${ir.compensation_total:,.2f}  "
              f"ethos={ir.ethos_coefficient:.2f}")

    return passed


def cmd_demo():
    """Run all 3 demo scenarios."""
    print("\n" + "=" * 70)
    print("  GIGATON ENGINE — L1→L3→L4 UNIFIED PIPELINE DEMO")
    print("  Brand + Interaction → Revenue → Predictable Profitability")
    print("=" * 70)

    engine = GigatonEngine()
    results = []

    for n in sorted(SCENARIOS.keys()):
        spec = SCENARIOS[n]
        result = engine.run(
            prospect=spec["prospect"],
            inferences=spec["inferences"],
            interactions=spec["interactions"],
            role_key=spec["role_key"],
        )
        passed = print_result(result, spec)
        results.append(passed)

    total_passed = sum(results)
    print(f"\n{'='*70}")
    print(f"  SUMMARY: {total_passed}/{len(results)} scenarios correct")
    print("=" * 70)
    return results


def cmd_prospect():
    """Run L1→L3 only for the first scenario (no L4)."""
    print("\n" + "=" * 70)
    print("  L1→L3 PROSPECT QUALIFICATION")
    print("=" * 70)

    engine = GigatonEngine()
    spec = SCENARIOS[1]
    l1_l3 = engine.run_l1_l3(
        prospect=spec["prospect"],
        inferences=spec["inferences"],
    )

    assessment = l1_l3["assessment"]
    decision = l1_l3["decision"]

    print(f"\n  Prospect: {spec['prospect'].official_name}")
    print(f"  Fit Score: {assessment.total:.1f}/100")
    print(f"  Verdict: {decision.verdict.value}")
    print(f"  Value: {decision.value_score:.3f}  Trust: {decision.trust_score:.3f}")
    print(f"  Priority: {decision.priority_score:.3f}")
    print(f"  RTQL: stage {decision.rtql_stage}/7  ×{decision.rtql_multiplier:.2f}")


def cmd_scenario(n: int):
    """Run a specific scenario."""
    if n not in SCENARIOS:
        print(f"  Error: scenario {n} not found. Available: {list(SCENARIOS.keys())}")
        sys.exit(1)

    engine = GigatonEngine()
    spec = SCENARIOS[n]
    result = engine.run(
        prospect=spec["prospect"],
        inferences=spec["inferences"],
        interactions=spec["interactions"],
        role_key=spec["role_key"],
    )
    print_result(result, spec)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1].lower()
    if cmd == "demo":
        cmd_demo()
    elif cmd == "prospect":
        cmd_prospect()
    elif cmd == "scenario" and len(sys.argv) >= 3:
        cmd_scenario(int(sys.argv[2]))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
