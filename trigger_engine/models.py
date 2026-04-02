"""Data models for the trigger and event engine."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


# ── Event taxonomy (mirrors 004_event_taxonomy.md) ─────────────────────


class EventCategory(str, Enum):
    DOMAIN = "domain"
    AGENT = "agent"
    SYNC = "sync"
    APPROVAL = "approval"


EVENT_TYPES = {
    # Domain events
    "opportunity.created",
    "opportunity.updated",
    "client.need_detected",
    "recommendation.generated",
    "pricing.review_requested",
    # Agent events
    "agent.deployed",
    "agent.started",
    "agent.completed",
    "agent.failed",
    "agent.escalated",
    # Sync events
    "google.sheet.imported",
    "google.sheet.exported",
    "google.doc.created",
    "gmail.draft.created",
    # Approval events
    "approval.requested",
    "approval.granted",
    "approval.rejected",
}


class JobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class QueueName(str, Enum):
    INGEST = "ingest_queue"
    WORKFLOW = "workflow_queue"
    AGENT = "agent_queue"
    ARTIFACT = "artifact_queue"
    SYNC = "sync_queue"
    RETRY = "retry_queue"
    DEAD_LETTER = "dead_letter_queue"


@dataclass
class NormalizedEvent:
    event_type: str
    payload: dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = "external"
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    @property
    def category(self) -> EventCategory | None:
        prefix = self.event_type.split(".")[0]
        mapping = {
            "opportunity": EventCategory.DOMAIN,
            "client": EventCategory.DOMAIN,
            "recommendation": EventCategory.DOMAIN,
            "pricing": EventCategory.DOMAIN,
            "agent": EventCategory.AGENT,
            "google": EventCategory.SYNC,
            "gmail": EventCategory.SYNC,
            "approval": EventCategory.APPROVAL,
        }
        return mapping.get(prefix)


@dataclass
class Job:
    job_type: str
    payload: dict[str, Any]
    job_id: str = field(default_factory=lambda: str(uuid4()))
    event_id: str = ""
    correlation_id: str = ""
    queue: QueueName = QueueName.INGEST
    status: JobStatus = JobStatus.QUEUED
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    error: str = ""


@dataclass
class EventLog:
    event_id: str
    event_type: str
    job_id: str
    status: str
    detail: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
