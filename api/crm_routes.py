"""CRM CRUD API routes for internal frontend data management.

Provides REST endpoints for:
  - Prospects: CRUD + pipeline execution + segmentation
  - Interactions: Create + list by prospect
  - Leads: Create/update + list by prospect
  - Pipeline Results: list by prospect
  - Segment Assignments: list by prospect
  - Silence Recovery: evaluate + execute via email
  - Batch Operations: run pipeline for all prospects

All endpoints prefixed with /api/v1/crm/
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

_API_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_API_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from crm_adapter.engines.database import Database
from crm_adapter.engines.pipeline_bridge import PipelineBridge
from pipeline.silence_recovery import SilenceRecoveryEngine, LeadSilenceState
from email_execution.engines.gmail_client import GmailClient
from email_execution.engines.execution_engine import EmailExecutionEngine


# ── Router ───────────────────────────────────────────────────────

router = APIRouter(prefix="/api/v1/crm", tags=["CRM"])

# Singletons — initialized on first import
_db = Database()
_bridge = PipelineBridge(_db)
_silence = SilenceRecoveryEngine()
_gmail = GmailClient()
_email_engine = EmailExecutionEngine(gmail_client=_gmail)


# ── Request Models ───────────────────────────────────────────────

class ProspectUpsertRequest(BaseModel):
    prospect_id: Optional[str] = None
    domain: str = ""
    official_name: str = ""
    industries: List[str] = []
    buyer_personas: List[str] = []
    service_geographies: List[str] = []
    gtm_motion: str = "unknown"
    pricing_visibility: str = "unknown"
    marketing_maturity: str = "low"
    sales_complexity: str = "medium"
    measurement_maturity: str = "low"
    interaction_management_maturity: str = "low"
    # Brand fields
    brand_id: str = ""
    brand_name: str = ""
    brand_tagline: str = ""
    brand_mission: str = ""
    brand_value_propositions: List[str] = []
    brand_differentiators: List[str] = []
    brand_proof_assets: List[str] = []
    brand_compliance_claims: List[str] = []
    brand_certifications: List[str] = []
    brand_active_channels: List[str] = ["email", "web"]
    brand_target_response_time: float = 300.0
    brand_target_resolution_time: float = 3600.0
    brand_target_conversion_rate: float = 0.15
    brand_minimum_ethos_score: float = 50.0


class InteractionCreateRequest(BaseModel):
    interaction_id: Optional[str] = None
    prospect_id: str
    entity_id: str = "agent_01"
    channel: str = "email"
    timestamp: Optional[str] = None
    status: str = "open"
    response_time_seconds: Optional[float] = None
    resolution_time_seconds: Optional[float] = None
    converted: bool = False
    abandoned: bool = False
    escalated: bool = False
    sentiment_score: float = 0.5
    trust_shift_score: float = 0.0


class LeadUpsertRequest(BaseModel):
    lead_id: Optional[str] = None
    prospect_id: str
    entity_id: str = ""
    status: str = "new"
    channel: str = "email"
    source: str = ""
    score: float = 0.0
    qualified_at: Optional[str] = None
    converted_at: Optional[str] = None


class SilenceExecuteRequest(BaseModel):
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
    authority_ceiling: str = "D1"
    lead_name: str = ""
    company_name: str = ""
    execute: bool = True  # if False, evaluate only


class PipelineRunRequest(BaseModel):
    role_key: str = "sales_operator"
    base_compensation: float = 5000.0
    strategic_multiplier: float = 1.0


# ── Prospect Endpoints ───────────────────────────────────────────

@router.post("/prospects")
def create_prospect(req: ProspectUpsertRequest):
    """Create or update a prospect."""
    data = req.model_dump()
    prospect_id = _db.upsert_prospect(data)
    return {"prospect_id": prospect_id, "status": "upserted"}


@router.get("/prospects")
def list_prospects(limit: int = 100, offset: int = 0):
    """List all prospects."""
    prospects = _db.list_prospects(limit=limit, offset=offset)
    return {
        "total": _db.count_table("prospects"),
        "limit": limit,
        "offset": offset,
        "prospects": prospects,
    }


@router.get("/prospects/{prospect_id}")
def get_prospect(prospect_id: str):
    """Get a single prospect by ID."""
    prospect = _db.get_prospect(prospect_id)
    if prospect is None:
        raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
    return prospect


@router.delete("/prospects/{prospect_id}")
def delete_prospect(prospect_id: str):
    """Delete a prospect by ID."""
    prospect = _db.get_prospect(prospect_id)
    if prospect is None:
        raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
    _db.conn.execute("DELETE FROM prospects WHERE prospect_id = ?", (prospect_id,))
    _db.conn.commit()
    return {"prospect_id": prospect_id, "status": "deleted"}


# ── Pipeline Execution ───────────────────────────────────────────

@router.post("/prospects/{prospect_id}/pipeline")
def run_prospect_pipeline(prospect_id: str, req: PipelineRunRequest):
    """Run full L1→L2→L3→L4 pipeline for a prospect using DB data."""
    result = _bridge.run_pipeline_for_prospect(
        prospect_id,
        role_key=req.role_key,
        base_compensation=req.base_compensation,
        strategic_multiplier=req.strategic_multiplier,
    )
    if result is None:
        raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
    return result.summary()


@router.post("/prospects/{prospect_id}/classify")
def classify_prospect(prospect_id: str):
    """Run segmentation for a prospect using DB data."""
    segments = _bridge.classify_prospect(prospect_id)
    if segments is None:
        raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
    return {"prospect_id": prospect_id, "segments": segments}


@router.post("/pipeline/batch")
def run_batch_pipeline(limit: int = 100, role_key: str = "sales_operator"):
    """Run pipeline for all prospects in the database."""
    return _bridge.run_batch_pipeline(limit=limit, role_key=role_key)


# ── Interaction Endpoints ────────────────────────────────────────

@router.post("/interactions")
def create_interaction(req: InteractionCreateRequest):
    """Add an interaction event."""
    data = req.model_dump()
    interaction_id = _db.add_interaction(data)
    return {"interaction_id": interaction_id, "status": "created"}


@router.get("/prospects/{prospect_id}/interactions")
def list_interactions(prospect_id: str):
    """List interactions for a prospect."""
    interactions = _db.get_interactions(prospect_id)
    return {"prospect_id": prospect_id, "interactions": interactions}


# ── Lead Endpoints ───────────────────────────────────────────────

@router.post("/leads")
def create_lead(req: LeadUpsertRequest):
    """Create or update a lead."""
    data = req.model_dump()
    lead_id = _db.upsert_lead(data)
    return {"lead_id": lead_id, "status": "upserted"}


@router.get("/prospects/{prospect_id}/leads")
def list_leads(prospect_id: str):
    """List leads for a prospect."""
    leads = _db.get_leads(prospect_id)
    return {"prospect_id": prospect_id, "leads": leads}


# ── Pipeline Results ─────────────────────────────────────────────

@router.get("/prospects/{prospect_id}/results")
def list_pipeline_results(prospect_id: str, limit: int = 10):
    """List pipeline results for a prospect (most recent first)."""
    results = _db.get_pipeline_results(prospect_id, limit=limit)
    return {"prospect_id": prospect_id, "results": results}


# ── Segment Assignments ─────────────────────────────────────────

@router.get("/prospects/{prospect_id}/segments")
def list_segment_assignments(prospect_id: str):
    """List segment assignments for a prospect."""
    segments = _db.get_segment_assignments(prospect_id)
    return {"prospect_id": prospect_id, "segments": segments}


# ── Silence Recovery + Email Execution ───────────────────────────

@router.post("/silence/evaluate-and-execute")
def silence_evaluate_and_execute(req: SilenceExecuteRequest):
    """Evaluate a silent lead and optionally execute the recommended action.

    If execute=True and action is send_email, sends via Gmail (dry-run by default).
    """
    lead = LeadSilenceState(
        lead_id=req.lead_id,
        email=req.email,
        stage=req.stage,
        status="silent",
        days_since_last_touch=req.days_since_last_touch,
        previous_attempts=req.previous_attempts,
        deal_value=req.deal_value,
        owner_id="assigned" if req.owner_assigned else None,
        recent_open_signal=req.recent_open_signal,
        recent_click_signal=req.recent_click_signal,
        meeting_status=req.meeting_status,
    )

    # Evaluate
    priority = _silence.compute_priority(lead)
    passed, reason, override = _silence.apply_hard_rules(lead)
    decision = _silence.select_action(
        lead, priority, passed, override, req.authority_ceiling
    )
    decision_dict = decision.to_dict()

    response = {
        "evaluation": {
            "lead_id": req.lead_id,
            "priority_score": round(priority, 4),
            "hard_rules_passed": passed,
            "hard_rule_reason": reason,
            "selected_action": decision.selected_action,
            "authority_level": decision.authority_level,
            "policy_gate_result": decision.policy_gate_result,
            "template_hint": decision.action_payload.get("template_hint", ""),
        },
        "execution": None,
    }

    # Execute if requested
    if req.execute and decision.selected_action == "send_email":
        daily_count = _db.get_daily_action_count()
        lead_context = {
            "lead_name": req.lead_name or "there",
            "lead_email": req.email,
            "company_name": req.company_name,
            "stage": req.stage,
            "deal_value": req.deal_value,
        }
        exec_result = _email_engine.execute_decision(
            decision_dict,
            lead_context=lead_context,
            db_action_count=daily_count,
        )

        # Store evaluation in DB
        _db.store_silence_evaluation({
            "eval_id": decision.decision_id,
            "lead_id": req.lead_id,
            "priority_score": priority,
            "selected_action": decision.selected_action,
            "authority_level": decision.authority_level,
            "policy_gate_result": decision.policy_gate_result,
            "executed": exec_result.executed,
            "executed_at": exec_result.executed_at,
            "execution_result": "sent" if exec_result.executed else (exec_result.error or ""),
        })

        response["execution"] = exec_result.to_dict()

    return response


# ── Stats ────────────────────────────────────────────────────────

@router.get("/stats")
def crm_stats():
    """Get CRM database statistics."""
    return {
        "prospects": _db.count_table("prospects"),
        "interactions": _db.count_table("interactions"),
        "leads": _db.count_table("leads"),
        "pipeline_results": _db.count_table("pipeline_results"),
        "segment_assignments": _db.count_table("segment_assignments"),
        "silence_evaluations": _db.count_table("silence_evaluations"),
        "daily_actions_today": _db.get_daily_action_count(),
    }
