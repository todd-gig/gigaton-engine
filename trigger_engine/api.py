"""FastAPI routes for the Trigger & Event Engine."""
from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import APIRouter, Request
from pydantic import BaseModel

from .models import Job, JobStatus, NormalizedEvent, QueueName
from .queue import QueueManager

router = APIRouter(prefix="/events", tags=["events"])

# Shared queue manager — handlers registered at startup via integration layer
queue_manager = QueueManager()

# ── Idempotency dedup window (in-memory for simplicity) ───────────────
_seen_event_ids: set[str] = set()


# ── Schemas ────────────────────────────────────────────────────────────


class WebhookResponse(BaseModel):
    status: str
    event_id: str


class JobSchema(BaseModel):
    job_id: str
    job_type: str
    event_id: str
    status: JobStatus
    retry_count: int
    error: str


class QueueStatusResponse(BaseModel):
    queue: str
    depth: int


class EventLogSchema(BaseModel):
    event_id: str
    event_type: str
    job_id: str
    status: str
    detail: str
    timestamp: str


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/webhook", response_model=WebhookResponse)
async def receive_webhook(request: Request) -> WebhookResponse:
    """Receive external webhook, normalize, and enqueue. Always responds fast."""
    payload = await request.json()

    event = NormalizedEvent(
        event_type=payload.get("type", "unknown"),
        payload=payload,
        event_id=payload.get("id", str(uuid4())),
        source=payload.get("source", "external"),
    )

    # Idempotency check
    if event.event_id in _seen_event_ids:
        return WebhookResponse(status="duplicate", event_id=event.event_id)
    _seen_event_ids.add(event.event_id)

    job = Job(
        job_type="normalized_event_handler",
        payload={"event": event.__dict__},
        event_id=event.event_id,
        correlation_id=event.event_id,
    )
    queue_manager.enqueue(job)

    return WebhookResponse(status="accepted", event_id=event.event_id)


@router.post("/internal", response_model=WebhookResponse)
def emit_internal_event(event_type: str, payload: dict[str, Any] = {}) -> WebhookResponse:
    """Emit an internal domain/agent/sync/approval event."""
    event = NormalizedEvent(event_type=event_type, payload=payload, source="internal")
    job = Job(
        job_type="normalized_event_handler",
        payload={"event": event.__dict__},
        event_id=event.event_id,
        correlation_id=event.event_id,
    )
    queue_manager.enqueue(job)
    return WebhookResponse(status="accepted", event_id=event.event_id)


@router.post("/process", response_model=list[JobSchema])
def process_queue(queue: QueueName = QueueName.INGEST) -> list[JobSchema]:
    """Manually trigger processing of all jobs in a queue."""
    jobs = queue_manager.process_all(queue)
    return [
        JobSchema(
            job_id=j.job_id,
            job_type=j.job_type,
            event_id=j.event_id,
            status=j.status,
            retry_count=j.retry_count,
            error=j.error,
        )
        for j in jobs
    ]


@router.get("/dead-letters", response_model=list[JobSchema])
def get_dead_letters() -> list[JobSchema]:
    jobs = queue_manager.get_dead_letters()
    return [
        JobSchema(
            job_id=j.job_id,
            job_type=j.job_type,
            event_id=j.event_id,
            status=j.status,
            retry_count=j.retry_count,
            error=j.error,
        )
        for j in jobs
    ]


@router.get("/log", response_model=list[EventLogSchema])
def get_event_log() -> list[EventLogSchema]:
    logs = queue_manager.get_event_log()
    return [
        EventLogSchema(
            event_id=lg.event_id,
            event_type=lg.event_type,
            job_id=lg.job_id,
            status=lg.status,
            detail=lg.detail,
            timestamp=lg.timestamp,
        )
        for lg in logs
    ]


@router.get("/queue-status", response_model=list[QueueStatusResponse])
def queue_status() -> list[QueueStatusResponse]:
    return [
        QueueStatusResponse(queue=q.value, depth=queue_manager.queue_depth(q))
        for q in QueueName
    ]
