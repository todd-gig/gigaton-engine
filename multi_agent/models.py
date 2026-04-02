"""Data models for multi-agent coordination."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class AgentRole(str, Enum):
    DISCOVERY = "discovery_agent"
    RECOMMENDATION = "recommendation_agent"
    PRICING = "pricing_agent"
    PROPOSAL = "proposal_agent"
    SYNC = "sync_agent"
    QA_REVIEW = "qa_review_agent"


class MessageType(str, Enum):
    TASK_REQUEST = "task_request"
    TASK_RESULT = "task_result"
    SCHEMA_ERROR = "schema_error"
    ESCALATION = "escalation"
    APPROVAL_REQUEST = "approval_request"
    APPROVAL_RESULT = "approval_result"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentMessage:
    sender_agent: str
    target_agent: str
    message_type: MessageType
    payload: dict[str, Any]
    correlation_id: str
    message_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class HandoffContract:
    run_id: str
    agent_name: str
    input_summary: str
    output_summary: str
    output_data: dict[str, Any]
    confidence: float  # 0.0–1.0
    next_recommended_agent: str | None = None
    requires_human_review: bool = False


@dataclass
class ApprovalGate:
    gate_id: str = field(default_factory=lambda: str(uuid4()))
    run_id: str = ""
    agent_name: str = ""
    reason: str = ""
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewer: str = ""
    reviewed_at: str | None = None


@dataclass
class ExecutionLog:
    run_id: str
    agent_name: str
    action: str
    detail: str = ""
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


@dataclass
class WorkflowRun:
    run_id: str = field(default_factory=lambda: str(uuid4()))
    status: RunStatus = RunStatus.PENDING
    agents_sequence: list[str] = field(default_factory=list)
    current_agent_index: int = 0
    handoffs: list[HandoffContract] = field(default_factory=list)
    approval_gates: list[ApprovalGate] = field(default_factory=list)
    execution_log: list[ExecutionLog] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

    @property
    def current_agent(self) -> str | None:
        if self.current_agent_index < len(self.agents_sequence):
            return self.agents_sequence[self.current_agent_index]
        return None
