"""FastAPI routes for Multi-Agent Coordination."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .models import ApprovalStatus, RunStatus
from .supervisor import Supervisor

router = APIRouter(prefix="/agents", tags=["agents"])

# Shared supervisor instance — agents registered at startup via integration layer
supervisor = Supervisor()


# ── Schemas ────────────────────────────────────────────────────────────


class CreateRunRequest(BaseModel):
    agents_sequence: list[str]
    context: dict[str, Any] = {}


class ApprovalAction(BaseModel):
    gate_id: str
    reviewer: str


class HandoffSchema(BaseModel):
    agent_name: str
    output_summary: str
    confidence: float
    requires_human_review: bool


class GateSchema(BaseModel):
    gate_id: str
    agent_name: str
    reason: str
    status: ApprovalStatus


class LogEntrySchema(BaseModel):
    agent_name: str
    action: str
    detail: str
    timestamp: str


class RunResponse(BaseModel):
    run_id: str
    status: RunStatus
    current_agent: str | None
    handoffs: list[HandoffSchema]
    approval_gates: list[GateSchema]
    execution_log: list[LogEntrySchema]


def _run_to_response(run) -> RunResponse:
    return RunResponse(
        run_id=run.run_id,
        status=run.status,
        current_agent=run.current_agent,
        handoffs=[
            HandoffSchema(
                agent_name=h.agent_name,
                output_summary=h.output_summary,
                confidence=h.confidence,
                requires_human_review=h.requires_human_review,
            )
            for h in run.handoffs
        ],
        approval_gates=[
            GateSchema(
                gate_id=g.gate_id,
                agent_name=g.agent_name,
                reason=g.reason,
                status=g.status,
            )
            for g in run.approval_gates
        ],
        execution_log=[
            LogEntrySchema(
                agent_name=e.agent_name,
                action=e.action,
                detail=e.detail,
                timestamp=e.timestamp,
            )
            for e in run.execution_log
        ],
    )


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/runs", response_model=RunResponse)
def create_run(req: CreateRunRequest) -> RunResponse:
    run = supervisor.create_run(req.agents_sequence, req.context)
    return _run_to_response(run)


@router.post("/runs/{run_id}/step", response_model=RunResponse)
def step_run(run_id: str) -> RunResponse:
    try:
        run = supervisor.step(run_id)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _run_to_response(run)


@router.post("/runs/{run_id}/run-all", response_model=RunResponse)
def run_all(run_id: str) -> RunResponse:
    try:
        run = supervisor.run_all(run_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _run_to_response(run)


@router.post("/runs/{run_id}/approve", response_model=RunResponse)
def approve_gate(run_id: str, action: ApprovalAction) -> RunResponse:
    try:
        run = supervisor.approve(run_id, action.gate_id, action.reviewer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _run_to_response(run)


@router.post("/runs/{run_id}/reject", response_model=RunResponse)
def reject_gate(run_id: str, action: ApprovalAction) -> RunResponse:
    try:
        run = supervisor.reject(run_id, action.gate_id, action.reviewer)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _run_to_response(run)


@router.get("/runs/{run_id}", response_model=RunResponse)
def get_run(run_id: str) -> RunResponse:
    run = supervisor.get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return _run_to_response(run)
