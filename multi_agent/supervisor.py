"""Supervisor agent — routes tasks, validates outputs, manages workflow runs."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

from .models import (
    AgentMessage,
    ApprovalGate,
    ApprovalStatus,
    ExecutionLog,
    HandoffContract,
    RunStatus,
    WorkflowRun,
)


AgentHandler = Callable[[dict[str, Any], dict[str, Any]], HandoffContract]


class Supervisor:
    """Orchestrates a sequence of agents, enforces contracts, and manages approvals."""

    def __init__(self) -> None:
        self._handlers: dict[str, AgentHandler] = {}
        self._approval_gates: set[str] = set()  # agent names requiring approval
        self._runs: dict[str, WorkflowRun] = {}

    # ── Registration ───────────────────────────────────────────────────

    def register_agent(
        self,
        agent_name: str,
        handler: AgentHandler,
        requires_approval: bool = False,
    ) -> None:
        self._handlers[agent_name] = handler
        if requires_approval:
            self._approval_gates.add(agent_name)

    # ── Workflow lifecycle ─────────────────────────────────────────────

    def create_run(
        self,
        agents_sequence: list[str],
        context: dict[str, Any] | None = None,
    ) -> WorkflowRun:
        run = WorkflowRun(
            agents_sequence=agents_sequence,
            context=context or {},
        )
        self._runs[run.run_id] = run
        self._log(run, "supervisor", "run_created", f"agents={agents_sequence}")
        return run

    def get_run(self, run_id: str) -> WorkflowRun | None:
        return self._runs.get(run_id)

    def step(self, run_id: str) -> WorkflowRun:
        """Execute the next agent in the sequence. Returns updated run."""
        run = self._runs.get(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        if run.status in (RunStatus.COMPLETED, RunStatus.FAILED):
            return run

        if run.status == RunStatus.AWAITING_APPROVAL:
            raise RuntimeError(
                f"Run {run_id} is awaiting approval before it can proceed"
            )

        agent_name = run.current_agent
        if agent_name is None:
            run.status = RunStatus.COMPLETED
            self._log(run, "supervisor", "run_completed")
            return run

        handler = self._handlers.get(agent_name)
        if handler is None:
            run.status = RunStatus.FAILED
            self._log(run, "supervisor", "agent_not_found", agent_name)
            return run

        run.status = RunStatus.RUNNING
        self._log(run, agent_name, "agent_started")

        # Build input from prior handoff or run context
        input_data = run.context.copy()
        if run.handoffs:
            input_data.update(run.handoffs[-1].output_data)

        try:
            handoff = handler(input_data, run.context)
            handoff.run_id = run.run_id
        except Exception as exc:
            run.status = RunStatus.FAILED
            self._log(run, agent_name, "agent_failed", str(exc))
            return run

        # Validate handoff contract
        if not self._validate_handoff(handoff):
            run.status = RunStatus.FAILED
            self._log(run, agent_name, "invalid_handoff")
            return run

        run.handoffs.append(handoff)
        self._log(run, agent_name, "agent_completed", handoff.output_summary)

        # Check approval gate
        if agent_name in self._approval_gates or handoff.requires_human_review:
            gate = ApprovalGate(
                run_id=run.run_id,
                agent_name=agent_name,
                reason=f"Output from {agent_name} requires review",
            )
            run.approval_gates.append(gate)
            run.status = RunStatus.AWAITING_APPROVAL
            self._log(run, "supervisor", "approval_requested", gate.gate_id)
            return run

        # Advance to next agent
        run.current_agent_index += 1
        if run.current_agent_index >= len(run.agents_sequence):
            run.status = RunStatus.COMPLETED
            self._log(run, "supervisor", "run_completed")
        else:
            run.status = RunStatus.PENDING

        return run

    def approve(self, run_id: str, gate_id: str, reviewer: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        gate = next((g for g in run.approval_gates if g.gate_id == gate_id), None)
        if gate is None:
            raise ValueError(f"Gate {gate_id} not found")

        gate.status = ApprovalStatus.APPROVED
        gate.reviewer = reviewer
        gate.reviewed_at = datetime.now(timezone.utc).isoformat()
        self._log(run, "supervisor", "approval_granted", f"by {reviewer}")

        # Advance
        run.current_agent_index += 1
        if run.current_agent_index >= len(run.agents_sequence):
            run.status = RunStatus.COMPLETED
            self._log(run, "supervisor", "run_completed")
        else:
            run.status = RunStatus.PENDING

        return run

    def reject(self, run_id: str, gate_id: str, reviewer: str) -> WorkflowRun:
        run = self._runs.get(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        gate = next((g for g in run.approval_gates if g.gate_id == gate_id), None)
        if gate is None:
            raise ValueError(f"Gate {gate_id} not found")

        gate.status = ApprovalStatus.REJECTED
        gate.reviewer = reviewer
        gate.reviewed_at = datetime.now(timezone.utc).isoformat()
        run.status = RunStatus.FAILED
        self._log(run, "supervisor", "approval_rejected", f"by {reviewer}")
        return run

    def run_all(self, run_id: str) -> WorkflowRun:
        """Step through all agents until completion, failure, or approval gate."""
        run = self._runs.get(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")

        while run.status in (RunStatus.PENDING, RunStatus.RUNNING):
            run = self.step(run_id)
        return run

    # ── Messaging ──────────────────────────────────────────────────────

    def send_message(self, message: AgentMessage) -> None:
        """Record a message in the execution log of the associated run."""
        run = self._runs.get(message.correlation_id)
        if run:
            self._log(
                run,
                message.sender_agent,
                f"message:{message.message_type.value}",
                f"to={message.target_agent}",
            )

    # ── Internal ───────────────────────────────────────────────────────

    @staticmethod
    def _validate_handoff(handoff: HandoffContract) -> bool:
        return bool(handoff.agent_name and handoff.output_summary)

    @staticmethod
    def _log(
        run: WorkflowRun, agent: str, action: str, detail: str = ""
    ) -> None:
        run.execution_log.append(
            ExecutionLog(
                run_id=run.run_id,
                agent_name=agent,
                action=action,
                detail=detail,
            )
        )
