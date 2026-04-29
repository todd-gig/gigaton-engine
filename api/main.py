"""
Gigaton Engine API — Unified Sovereign Intelligence Service.

FastAPI application exposing the full L1→L4 pipeline, silence recovery,
segmentation, and enrichment as governed API endpoints.

Endpoints:
  POST /api/v1/pipeline/run          — Full L1→L3→L4 pipeline
  POST /api/v1/pipeline/prospect     — L1→L3 prospect qualification only
  POST /api/v1/pipeline/nix          — Next Interaction Experience recommendation
  POST /api/v1/silence/evaluate      — Silence recovery evaluation
  POST /api/v1/segmentation/classify — Customer segmentation
  POST /api/v1/enrichment/segment    — Apollo enrichment for a segment
  GET  /api/v1/health                — Health check
  GET  /api/v1/status                — System status with module inventory
"""
import sys
import os
import time
from datetime import datetime

# Ensure project root is on path
_API_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_API_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

from pipeline.engine import GigatonEngine
from l1_sensing.models.prospect import (
    ProspectProfile, CapabilitySummary, MaturityLevel, GTMMotion, PricingVisibility,
)
from l1_sensing.models.inference import InferenceRecord, InferenceType
from l2_brand_experience.models.brand_profile import BrandProfile
from l2_brand_experience.engines.brand_experience_engine import BrandExperienceEngine
from l4_execution.models.interaction import InteractionEvent
from l4_execution.engines.nix_engine import NIXEngine
from segmentation.engines.segmentation_engine import SegmentationEngine, InteractionPerformanceContext
from apollo_enrichment.engines.enrichment_engine import EnrichmentEngine
from apollo_enrichment.engines.apollo_client import ApolloClient
from pipeline.silence_recovery import SilenceRecoveryEngine, LeadSilenceState


# ── App setup ─────────────────────────────────────────────────────

app = FastAPI(
    title="Gigaton Engine API",
    description="Unified Sovereign Intelligence — L1→L4 Pipeline + Silence Recovery + Segmentation + Enrichment + CRM",
    version="1.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include CRM CRUD routes
try:
    from api.crm_routes import router as crm_router
    app.include_router(crm_router)
except ImportError:
    pass  # CRM routes optional — may not be available in all deployments

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ────────────────────────────────────────────────────

_engine = GigatonEngine()
_nix = NIXEngine()
_segmentation = SegmentationEngine()
from apollo_enrichment.engines.apollo_client import create_apollo_client
_enrichment = EnrichmentEngine(apollo_client=create_apollo_client())
_silence = SilenceRecoveryEngine()
_boot_time = datetime.utcnow().isoformat()


# ── Request/Response models ───────────────────────────────────────

class CapabilitySummaryRequest(BaseModel):
    marketing_maturity: str = "low"
    sales_complexity: str = "medium"
    measurement_maturity: str = "low"
    interaction_management_maturity: str = "low"

class ProspectRequest(BaseModel):
    prospect_id: str
    domain: str = ""
    official_name: str = ""
    industries: List[str] = []
    buyer_personas: List[str] = []
    service_geographies: List[str] = []
    gtm_motion: str = "unknown"
    pricing_visibility: str = "unknown"
    capability_summary: Optional[CapabilitySummaryRequest] = None
    last_verified_at: str = ""
    evidence_ids: List[str] = []

class InferenceRequest(BaseModel):
    object_id: str
    prospect_id: str
    inference_type: str = "pain_point"
    statement: str = ""
    confidence: float = 0.5
    evidence_ids: List[str] = []

class InteractionRequest(BaseModel):
    interaction_id: str
    entity_id: str = "agent_01"
    channel: str = "email"
    timestamp: str = ""
    status: str = "resolved"
    response_time_seconds: Optional[float] = None
    resolution_time_seconds: Optional[float] = None
    converted: bool = False
    abandoned: bool = False
    escalated: bool = False
    sentiment_score: float = 0.5
    trust_shift_score: float = 0.0

class BrandProfileRequest(BaseModel):
    brand_id: str = "default"
    brand_name: str = "Default Brand"
    tagline: str = ""
    mission: str = ""
    value_propositions: List[str] = []
    differentiators: List[str] = []
    proof_assets: List[str] = []
    compliance_claims: List[str] = []
    certifications: List[str] = []
    active_channels: List[str] = ["email", "web"]
    target_response_time_seconds: float = 300.0
    target_resolution_time_seconds: float = 3600.0
    target_conversion_rate: float = 0.15
    minimum_ethos_score: float = 50.0

class PipelineRunRequest(BaseModel):
    prospect: ProspectRequest
    inferences: List[InferenceRequest] = []
    interactions: List[InteractionRequest] = []
    brand_profile: Optional[BrandProfileRequest] = None
    role_key: str = "sales_operator"
    base_compensation: float = 5000.0
    strategic_multiplier: float = 1.0

class ProspectOnlyRequest(BaseModel):
    prospect: ProspectRequest
    inferences: List[InferenceRequest] = []
    brand_profile: Optional[BrandProfileRequest] = None

class NIXRequest(BaseModel):
    prospect: ProspectRequest
    inferences: List[InferenceRequest] = []
    interactions: List[InteractionRequest] = []
    brand_profile: Optional[BrandProfileRequest] = None
    role_key: str = "sales_operator"
    prior_channels: List[str] = []

class SilenceEvalRequest(BaseModel):
    lead_id: str
    email: str = ""
    stage: str = "silent"
    days_since_last_touch: int = 0
    previous_attempts: int = 0
    deal_value: float = 0.0
    owner_assigned: bool = True
    recent_open_signal: bool = False
    recent_click_signal: bool = False
    meeting_status: str = ""
    account_tier: str = "standard"
    authority_ceiling: str = "D1"

class SegmentRequest(BaseModel):
    prospect: ProspectRequest
    inferences: List[InferenceRequest] = []
    brand_profile: Optional[BrandProfileRequest] = None
    interactions: List[InteractionRequest] = []

class EnrichSegmentRequest(BaseModel):
    segment_key: str
    max_results: int = 25


# ── Helpers ───────────────────────────────────────────────────────

def _to_maturity(s: str) -> MaturityLevel:
    mapping = {"unknown": MaturityLevel.UNKNOWN, "low": MaturityLevel.LOW,
               "medium": MaturityLevel.MEDIUM, "high": MaturityLevel.HIGH}
    return mapping.get(s.lower(), MaturityLevel.UNKNOWN)

def _to_gtm(s: str) -> GTMMotion:
    mapping = {"unknown": GTMMotion.UNKNOWN, "sales_led": GTMMotion.SALES_LED,
               "plg": GTMMotion.PLG, "hybrid": GTMMotion.HYBRID}
    return mapping.get(s.lower(), GTMMotion.UNKNOWN)

def _to_pricing(s: str) -> PricingVisibility:
    mapping = {"unknown": PricingVisibility.UNKNOWN, "public": PricingVisibility.PUBLIC,
               "contact_sales": PricingVisibility.CONTACT_SALES}
    return mapping.get(s.lower(), PricingVisibility.UNKNOWN)

def _to_inference_type(s: str) -> InferenceType:
    mapping = {"pain_point": InferenceType.PAIN_POINT, "service_fit": InferenceType.SERVICE_FIT,
               "value_estimate": InferenceType.VALUE_ESTIMATE, "business_goal": InferenceType.BUSINESS_GOAL,
               "gtm_motion": InferenceType.GTM_MOTION}
    return mapping.get(s.lower(), InferenceType.PAIN_POINT)

def _build_brand_profile(req) -> Optional[BrandProfile]:
    """Build BrandProfile from request, or return None to use engine default."""
    if req is None:
        return None
    return BrandProfile(
        brand_id=req.brand_id, brand_name=req.brand_name,
        tagline=req.tagline, mission=req.mission,
        value_propositions=req.value_propositions, differentiators=req.differentiators,
        proof_assets=req.proof_assets, compliance_claims=req.compliance_claims,
        certifications=req.certifications, active_channels=req.active_channels,
        target_response_time_seconds=req.target_response_time_seconds,
        target_resolution_time_seconds=req.target_resolution_time_seconds,
        target_conversion_rate=req.target_conversion_rate,
        minimum_ethos_score=req.minimum_ethos_score,
    )

def _build_prospect(req: ProspectRequest) -> ProspectProfile:
    caps = CapabilitySummary()
    if req.capability_summary:
        caps = CapabilitySummary(
            marketing_maturity=_to_maturity(req.capability_summary.marketing_maturity),
            sales_complexity=_to_maturity(req.capability_summary.sales_complexity),
            measurement_maturity=_to_maturity(req.capability_summary.measurement_maturity),
            interaction_management_maturity=_to_maturity(req.capability_summary.interaction_management_maturity),
        )
    return ProspectProfile(
        prospect_id=req.prospect_id, domain=req.domain, official_name=req.official_name,
        industries=req.industries, buyer_personas=req.buyer_personas,
        service_geographies=req.service_geographies, gtm_motion=_to_gtm(req.gtm_motion),
        pricing_visibility=_to_pricing(req.pricing_visibility), capability_summary=caps,
        last_verified_at=req.last_verified_at, evidence_ids=req.evidence_ids,
    )

def _build_inferences(reqs: List[InferenceRequest]) -> List[InferenceRecord]:
    return [InferenceRecord(
        object_id=r.object_id, prospect_id=r.prospect_id,
        inference_type=_to_inference_type(r.inference_type),
        statement=r.statement, confidence=r.confidence, evidence_ids=r.evidence_ids,
    ) for r in reqs]

def _build_interactions(reqs: List[InteractionRequest]) -> List[InteractionEvent]:
    return [InteractionEvent(
        interaction_id=r.interaction_id, entity_id=r.entity_id, channel=r.channel,
        timestamp=r.timestamp or datetime.utcnow().isoformat(), status=r.status,
        response_time_seconds=r.response_time_seconds, resolution_time_seconds=r.resolution_time_seconds,
        converted=r.converted, abandoned=r.abandoned, escalated=r.escalated,
        sentiment_score=r.sentiment_score, trust_shift_score=r.trust_shift_score,
    ) for r in reqs]


# ── Endpoints ─────────────────────────────────────────────────────

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/v1/status")
def status():
    return {
        "engine": "Gigaton Sovereign Intelligence Engine",
        "version": "1.0.0",
        "boot_time": _boot_time,
        "modules": {
            "l1_sensing": "operational",
            "l2_brand_experience": "integrated",
            "l3_qualification": "operational",
            "l3_causal_engine": "operational",
            "l3_learning_engine": "operational",
            "l3_gap_engine": "operational",
            "l3_roi_engine": "operational",
            "l3_rtql_advanced": "operational",
            "l3_weighted_scoring": "operational",
            "l3_intelligence_engine": "operational",
            "l4_execution": "operational",
            "l4_nix_engine": "operational",
            "segmentation": "operational",
            "apollo_enrichment": "operational (mock mode)",
            "silence_recovery": "operational",
            "crm_adapter": "operational",
            "email_execution": "operational (dry-run default)",
            "apollo_enrichment": f"operational ({'real' if os.environ.get('APOLLO_API_KEY') else 'mock'} mode)",
            "governance": "operational",
            "state_machine": "operational",
            "audit": "operational",
        },
        "test_count": 776,
        "module_count": 53,
    }


@app.post("/api/v1/pipeline/run")
def pipeline_run(req: PipelineRunRequest):
    """Full L1→L2→L3→L4 pipeline execution."""
    start = time.time()
    prospect = _build_prospect(req.prospect)
    inferences = _build_inferences(req.inferences)
    interactions = _build_interactions(req.interactions)
    brand_profile = _build_brand_profile(req.brand_profile)

    result = _engine.run(
        prospect=prospect, inferences=inferences, interactions=interactions,
        brand_profile=brand_profile, role_key=req.role_key,
        base_compensation=req.base_compensation,
        strategic_multiplier=req.strategic_multiplier,
    )

    elapsed = time.time() - start
    summary = result.summary()
    summary["execution_time_ms"] = round(elapsed * 1000, 1)
    return summary


@app.post("/api/v1/pipeline/prospect")
def pipeline_prospect(req: ProspectOnlyRequest):
    """L1→L2→L3 prospect qualification only."""
    prospect = _build_prospect(req.prospect)
    inferences = _build_inferences(req.inferences)
    brand_profile = _build_brand_profile(req.brand_profile)
    l1_l3 = _engine.run_l1_l3(prospect=prospect, inferences=inferences, brand_profile=brand_profile)

    assessment = l1_l3["assessment"]
    decision = l1_l3["decision"]

    return {
        "prospect_id": req.prospect.prospect_id,
        "fit_score": round(assessment.total, 2),
        "verdict": decision.verdict.value,
        "value_score": round(decision.value_score, 3),
        "trust_score": round(decision.trust_score, 3),
        "priority_score": round(decision.priority_score, 3),
        "rtql_stage": decision.rtql_stage,
        "certificates": {
            "QC": decision.qc_pass, "VC": decision.vc_pass,
            "TC": decision.tc_pass, "EC": decision.ec_pass,
        },
        "blocking_gates": decision.blocking_gates,
        "priority_gaps": assessment.priority_gaps,
        "best_fit_services": assessment.best_fit_services,
    }


@app.post("/api/v1/pipeline/nix")
def pipeline_nix(req: NIXRequest):
    """Next Interaction Experience recommendation."""
    prospect = _build_prospect(req.prospect)
    inferences = _build_inferences(req.inferences)
    interactions = _build_interactions(req.interactions)
    brand_profile = _build_brand_profile(req.brand_profile)

    result = _engine.run(
        prospect=prospect, inferences=inferences, interactions=interactions,
        brand_profile=brand_profile, role_key=req.role_key,
    )

    nix_result = _nix.recommend(
        result=result,
        prior_channels=req.prior_channels,
    )
    return nix_result.to_dict()


@app.post("/api/v1/silence/evaluate")
def silence_evaluate(req: SilenceEvalRequest):
    """Evaluate a silent lead and recommend next action."""
    lead = LeadSilenceState(
        lead_id=req.lead_id, email=req.email, stage=req.stage,
        status=req.stage,
        days_since_last_touch=req.days_since_last_touch,
        previous_attempts=req.previous_attempts, deal_value=req.deal_value,
        owner_id="assigned" if req.owner_assigned else None,
        recent_open_signal=req.recent_open_signal,
        recent_click_signal=req.recent_click_signal, meeting_status=req.meeting_status,
    )

    decision = _silence.evaluate_lead(lead)
    # SilenceRecoveryEngine may return a dict or dataclass
    if isinstance(decision, dict):
        return decision
    return {
        "lead_id": getattr(decision, 'lead_id', req.lead_id),
        "priority_score": round(getattr(decision, 'priority_score', 0), 3),
        "selected_action": getattr(decision, 'selected_action', 'do_not_execute'),
        "authority_level": getattr(decision, 'authority_level', 'D1'),
        "policy_gate_result": getattr(decision, 'policy_gate_result', 'approved'),
        "reasoning": getattr(decision, 'reasoning', ''),
    }


@app.post("/api/v1/segmentation/classify")
def segmentation_classify(req: SegmentRequest):
    """Classify a prospect into customer segments using L1 + L2 + L4 data."""
    from l1_sensing.engines.prospect_value_engine import ProspectValueEngine
    prospect = _build_prospect(req.prospect)
    inferences = _build_inferences(req.inferences)
    assessment = ProspectValueEngine.score_prospect(prospect, inferences)

    # L2: Brand assessment (optional, enhances segmentation precision)
    brand_assessment = None
    brand_profile = _build_brand_profile(req.brand_profile)
    if brand_profile is not None:
        interactions = _build_interactions(req.interactions)
        brand_assessment = BrandExperienceEngine.assess(brand_profile, interactions)

    # L4: Interaction performance context (optional)
    interaction_context = None
    if req.interactions:
        interactions = _build_interactions(req.interactions)
        interaction_context = InteractionPerformanceContext.from_interactions(interactions)

    segments = _segmentation.classify(
        prospect, assessment, brand_assessment, interaction_context,
    )

    return {
        "prospect_id": req.prospect.prospect_id,
        "fit_score": round(assessment.total, 2),
        "brand_experience_score": round(brand_assessment.brand_experience_score, 2) if brand_assessment else None,
        "matched_segments": [
            {
                "segment_id": s.segment_id,
                "segment_name": s.segment_name,
                "priority_tier": s.priority_tier,
                "gap_pattern": s.primary_gap_pattern,
                "service_packages": s.service_package_fit,
            }
            for s in segments
        ],
    }


@app.post("/api/v1/enrichment/segment")
def enrichment_segment(req: EnrichSegmentRequest):
    """Enrich leads for a customer segment via Apollo."""
    result = _enrichment.enrich_segment(req.segment_key, max_results=req.max_results)
    return {
        "segment_key": req.segment_key,
        "total_found": result.total_found,
        "enrichment_rate": round(result.enrichment_rate, 2),
        "leads": [
            {
                "lead_id": l.lead_id,
                "name": l.full_name(),
                "title": l.title,
                "email": l.email,
                "company": l.company_name,
                "fit_score": round(l.fit_score, 1),
            }
            for l in result.leads
        ],
    }
