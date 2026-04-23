"""
Dashboard data generator — Runs the pipeline and produces structured dashboard data.

Executes the 3 CLI scenarios through the GigatonEngine pipeline and generates
synthetic L2 brand data (since L2 is not yet wired into the pipeline).

Produces a dict structure organized by layer with all metrics needed for rendering.
"""
import sys
import os
from typing import Dict, Any, List

# Ensure project root is on path
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from pipeline.engine import GigatonEngine
from pipeline.cli import SCENARIOS
from l2_brand_experience.models.brand_coherence import BrandCoherenceScore
from l2_brand_experience.models.brand_assessment import BrandExperienceAssessment
from segmentation.segment_library import SEGMENT_LIBRARY
from l4_execution.models.role_profile import ROLE_PROFILES
from l4_execution.engines.nix_engine import NIXEngine


def _generate_synthetic_l2_data(scenario_name: str) -> BrandExperienceAssessment:
    """Generate synthetic L2 brand experience data for dashboard demo."""
    # Create realistic demo values that vary by scenario
    scenario_adjustments = {
        1: {"ethos_base": 75, "consistency": 80, "proof_ratio": 0.85, "trust_quality": 78},
        2: {"ethos_base": 55, "consistency": 60, "proof_ratio": 0.55, "trust_quality": 58},
        3: {"ethos_base": 35, "consistency": 40, "proof_ratio": 0.35, "trust_quality": 38},
    }

    # Determine scenario number from name
    scenario_num = 1
    if "Mid-Tier" in scenario_name:
        scenario_num = 2
    elif "Weak Signal" in scenario_name:
        scenario_num = 3

    adj = scenario_adjustments.get(scenario_num, scenario_adjustments[1])

    coherence = BrandCoherenceScore(
        truthfulness_explainability=adj["ethos_base"] + 5,
        human_centered_technology=adj["ethos_base"],
        long_term_value_creation=adj["ethos_base"] - 3,
        cost_roi_discipline=adj["ethos_base"] + 2,
        human_agency_respect=adj["ethos_base"],
        trust_contribution=adj["ethos_base"] - 5,
        manipulation_avoidance=adj["ethos_base"] + 1,
        composite_score=adj["ethos_base"],
        coefficient=0.5 + (adj["ethos_base"] / 200),  # Scale 0.5-1.25
    )

    return BrandExperienceAssessment(
        brand_id=f"BRAND_SCENARIO_{scenario_num}",
        coherence=coherence,
        channel_consistency_score=adj["consistency"],
        proof_to_promise_ratio=adj["proof_ratio"],
        trust_layer_quality=adj["trust_quality"],
        avg_response_performance=0.7 + (adj["consistency"] / 500),
        avg_resolution_performance=0.65 + (adj["consistency"] / 600),
        conversion_performance=0.5 + (adj["consistency"] / 800),
        brand_experience_score=adj["consistency"],
    )


def generate_dashboard_data() -> Dict[str, Any]:
    """
    Run pipeline on 3 scenarios and generate complete dashboard data structure.

    Returns:
        Dict with keys:
        - scenarios: List of scenario results with L1/L3/L4 data
        - summary: Executive summary metrics
        - l1_analysis: Component breakdowns
        - l2_analysis: Brand coherence and experience data
        - l3_analysis: Decision verdicts and qualifications
        - l4_analysis: NOCS and compensation data
        - segmentation: Customer segment data
        - verdicts_distribution: Count of each verdict type
    """
    engine = GigatonEngine()
    nix_engine = NIXEngine()
    scenario_results = []
    verdicts = []
    total_prospects = 0
    all_value_scores = []
    all_trust_scores = []
    all_fit_scores = []
    all_compensation = []

    # Run all 3 scenarios
    for scenario_num, scenario_config in SCENARIOS.items():
        prospect = scenario_config["prospect"]
        inferences = scenario_config["inferences"]
        interactions = scenario_config["interactions"]
        role_key = scenario_config["role_key"]

        # Run the full pipeline
        pipeline_result = engine.run(prospect, inferences, interactions, role_key)

        # Extract metrics
        fit_score = round(pipeline_result.prospect_assessment.total, 2)
        all_fit_scores.append(fit_score)
        all_value_scores.append(pipeline_result.value_score)
        all_trust_scores.append(pipeline_result.trust_score)
        all_compensation.append(pipeline_result.total_compensation)
        verdicts.append(pipeline_result.verdict)
        total_prospects += 1

        # Generate synthetic L2 data
        l2_assessment = _generate_synthetic_l2_data(scenario_config["name"])

        # Generate Next Interaction Experience recommendation
        prior_channels = [i.channel for i in interactions]
        brand_coherence = {
            "truthfulness_explainability": l2_assessment.coherence.truthfulness_explainability,
            "human_centered_technology": l2_assessment.coherence.human_centered_technology,
            "long_term_value_creation": l2_assessment.coherence.long_term_value_creation,
            "cost_roi_discipline": l2_assessment.coherence.cost_roi_discipline,
            "human_agency_respect": l2_assessment.coherence.human_agency_respect,
            "trust_contribution": l2_assessment.coherence.trust_contribution,
            "manipulation_avoidance": l2_assessment.coherence.manipulation_avoidance,
        }
        nix_result = nix_engine.recommend(
            result=pipeline_result,
            prior_channels=prior_channels,
            brand_coherence_data=brand_coherence,
        )

        # Build scenario result dict
        scenario_result = {
            "scenario_num": scenario_num,
            "scenario_name": scenario_config["name"],
            "description": scenario_config["description"],
            "expected_verdict": scenario_config["expected_verdict"],

            # L1 data
            "l1": {
                "prospect_id": prospect.prospect_id,
                "prospect_name": prospect.official_name,
                "need": round(pipeline_result.prospect_assessment.need, 2),
                "service_fit": round(pipeline_result.prospect_assessment.service_fit, 2),
                "readiness": round(pipeline_result.prospect_assessment.readiness, 2),
                "accessibility": round(pipeline_result.prospect_assessment.accessibility, 2),
                "expected_uplift": round(pipeline_result.prospect_assessment.expected_uplift, 2),
                "economic_scale": round(pipeline_result.prospect_assessment.economic_scale, 2),
                "confidence": round(pipeline_result.prospect_assessment.confidence, 2),
                "total_fit_score": fit_score,
                "best_fit_services": pipeline_result.prospect_assessment.best_fit_services,
                "priority_gaps": pipeline_result.prospect_assessment.priority_gaps,
            },

            # L2 data (synthetic)
            "l2": {
                "brand_id": l2_assessment.brand_id,
                "coherence": {
                    "truthfulness_explainability": round(l2_assessment.coherence.truthfulness_explainability, 1),
                    "human_centered_technology": round(l2_assessment.coherence.human_centered_technology, 1),
                    "long_term_value_creation": round(l2_assessment.coherence.long_term_value_creation, 1),
                    "cost_roi_discipline": round(l2_assessment.coherence.cost_roi_discipline, 1),
                    "human_agency_respect": round(l2_assessment.coherence.human_agency_respect, 1),
                    "trust_contribution": round(l2_assessment.coherence.trust_contribution, 1),
                    "manipulation_avoidance": round(l2_assessment.coherence.manipulation_avoidance, 1),
                    "composite_score": round(l2_assessment.coherence.composite_score, 1),
                    "coefficient": round(l2_assessment.coherence.coefficient, 3),
                },
                "channel_consistency_score": round(l2_assessment.channel_consistency_score, 2),
                "proof_to_promise_ratio": round(l2_assessment.proof_to_promise_ratio, 3),
                "trust_layer_quality": round(l2_assessment.trust_layer_quality, 2),
                "brand_experience_score": round(l2_assessment.brand_experience_score, 2),
            },

            # L3 data
            "l3": {
                "decision_id": pipeline_result.decision_id,
                "verdict": pipeline_result.verdict,
                "value_score": round(pipeline_result.value_score, 3),
                "trust_score": round(pipeline_result.trust_score, 3),
                "rtql_stage": pipeline_result.rtql_stage,
                "rtql_multiplier": round(pipeline_result.rtql_multiplier, 2),
                "priority_score": round(pipeline_result.priority_score, 3),
                "certificates": pipeline_result.certificates,
                "blocking_gates": pipeline_result.blocking_gates,
            },

            # L4 data
            "l4": {
                "interaction_count": pipeline_result.interaction_count,
                "total_compensation": round(pipeline_result.total_compensation, 2),
                "avg_nocs": round(pipeline_result.avg_nocs, 2),
                "role_key": role_key,
                "interactions": [
                    {
                        "interaction_id": ir.interaction_id,
                        "channel": ir.channel,
                        "nocs": round(ir.nocs.final_nocs, 2),
                        "compensation_total": round(ir.compensation_total, 2),
                        "compensation_variable": round(ir.compensation_variable, 2),
                        "ethos_coefficient": round(ir.ethos_coefficient, 3),
                    }
                    for ir in pipeline_result.interaction_results
                ],
            },

            # NIX — Next Interaction Experience
            "nix": nix_result.to_dict(),
        }

        scenario_results.append(scenario_result)

    # Compute executive summary
    verdict_dist = {v: verdicts.count(v) for v in set(verdicts)}

    summary = {
        "total_prospects": total_prospects,
        "avg_fit_score": round(sum(all_fit_scores) / len(all_fit_scores), 2) if all_fit_scores else 0,
        "avg_value_score": round(sum(all_value_scores) / len(all_value_scores), 3) if all_value_scores else 0,
        "avg_trust_score": round(sum(all_trust_scores) / len(all_trust_scores), 3) if all_trust_scores else 0,
        "total_compensation_pool": round(sum(all_compensation), 2),
        "verdicts_distribution": verdict_dist,
        "layer_statuses": {
            "l1": "healthy",
            "l2": "ready",
            "l3": "operational",
            "l4": "active",
        },
    }

    # Build segmentation data
    segments = []
    for seg_id, segment in SEGMENT_LIBRARY.items():
        segments.append({
            "segment_id": segment.segment_id,
            "segment_name": segment.segment_name,
            "description": segment.description,
            "expected_value_range": segment.expected_value_range,
            "priority_tier": segment.priority_tier,
            "primary_gap_pattern": segment.primary_gap_pattern,
            "service_packages": segment.service_package_fit,
            "apollo_targeting": {
                "industries": segment.apollo_targeting.industries,
                "titles": segment.apollo_targeting.titles,
                "seniority_levels": segment.apollo_targeting.seniority_levels,
                "keywords": segment.apollo_targeting.keywords,
            },
        })

    # Build role profiles reference
    roles_data = []
    for role_id, role in ROLE_PROFILES.items():
        roles_data.append({
            "role_id": role.role_id,
            "role_name": role.role_name,
            "benchmark_weights": {k: round(v, 3) for k, v in role.benchmark_weights.items()},
        })

    return {
        "timestamp": "2026-04-21",
        "scenarios": scenario_results,
        "summary": summary,
        "segmentation": {
            "segments": segments,
            "segment_count": len(segments),
        },
        "roles": roles_data,
        "l1_components": ["need", "service_fit", "readiness", "accessibility", "expected_uplift", "economic_scale", "confidence"],
        "l2_ethos_dimensions": [
            "truthfulness_explainability",
            "human_centered_technology",
            "long_term_value_creation",
            "cost_roi_discipline",
            "human_agency_respect",
            "trust_contribution",
            "manipulation_avoidance",
        ],
    }
