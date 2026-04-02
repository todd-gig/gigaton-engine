"""Startup wiring — registers agents and event handlers, connecting all subsystems."""
from __future__ import annotations

from typing import Any

from multi_agent.api import supervisor
from trigger_engine.api import queue_manager
from trigger_engine.models import Job

from .agents import (
    discovery_handler,
    pricing_handler,
    proposal_handler,
    recommendation_handler,
    sync_handler,
)


def wire_agents() -> None:
    """Register all agent handlers with the supervisor."""
    supervisor.register_agent("discovery_agent", discovery_handler)
    supervisor.register_agent("recommendation_agent", recommendation_handler)
    supervisor.register_agent("pricing_agent", pricing_handler, requires_approval=True)
    supervisor.register_agent("proposal_agent", proposal_handler)
    supervisor.register_agent("sync_agent", sync_handler)


def wire_event_handlers() -> None:
    """Register queue handlers that route events to agent workflows."""

    def opportunity_event_handler(job: Job) -> dict[str, Any]:
        """When an opportunity event arrives, kick off the full agent workflow."""
        event_data = job.payload.get("event", {})
        event_payload = event_data.get("payload", {})
        event_type = event_data.get("event_type", "")

        if event_type in ("opportunity.created", "opportunity.updated"):
            run = supervisor.create_run(
                agents_sequence=[
                    "discovery_agent",
                    "recommendation_agent",
                    "pricing_agent",
                    "proposal_agent",
                    "sync_agent",
                ],
                context={"opportunity": event_payload},
            )
            # Run until completion or approval gate
            supervisor.run_all(run.run_id)
            return {"run_id": run.run_id, "status": run.status.value}

        return {"skipped": True, "reason": f"unhandled event_type={event_type}"}

    queue_manager.register_handler("normalized_event_handler", opportunity_event_handler)


def wire_all() -> None:
    """Single entry point to wire everything."""
    wire_agents()
    wire_event_handlers()
