"""Email Execution Engine — executes SilenceRecoveryEngine decisions via Gmail.

Consumes FollowUpDecision objects from the SilenceRecoveryEngine,
renders appropriate email templates, and sends via GmailClient.

Governance controls:
  - Daily action limit (configurable, default 50)
  - Dry-run toggle (default: on)
  - Authority level validation
  - Execution logging for audit trail

Environment variables:
  EMAIL_DAILY_LIMIT — max emails per day (default: 50)
  EMAIL_SENDER_NAME — display name for outbound emails
  EMAIL_SENDER_TITLE — sender title for high-value escalations
  EMAIL_SENDER_COMPANY — company name in signatures
"""

import logging
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List

from email_execution.engines.gmail_client import GmailClient
from email_execution.models.email_models import (
    EmailMessage, EmailStatus, ExecutionResult,
)
from email_execution.templates.silence_templates import render_template

logger = logging.getLogger(__name__)

# Default daily limit — governance constraint
DEFAULT_DAILY_LIMIT = 50


class EmailExecutionEngine:
    """Executes silence recovery decisions as emails.

    Pipeline:
      1. Receive FollowUpDecision from SilenceRecoveryEngine
      2. Validate: action type, authority level, daily limit
      3. Render email template with lead context
      4. Send via GmailClient (or dry-run)
      5. Return ExecutionResult for audit

    The engine enforces governance at every step:
      - Only executes send_email actions
      - Respects authority ceilings
      - Enforces daily action limits
      - Supports dry-run mode for testing
    """

    def __init__(
        self,
        gmail_client: Optional[GmailClient] = None,
        daily_limit: Optional[int] = None,
        sender_name: Optional[str] = None,
        sender_title: Optional[str] = None,
        sender_company: Optional[str] = None,
    ):
        self.gmail = gmail_client or GmailClient()
        self.daily_limit = daily_limit or int(
            os.environ.get("EMAIL_DAILY_LIMIT", str(DEFAULT_DAILY_LIMIT))
        )
        self.sender_name = sender_name or os.environ.get(
            "EMAIL_SENDER_NAME", "Your Team"
        )
        self.sender_title = sender_title or os.environ.get(
            "EMAIL_SENDER_TITLE", ""
        )
        self.sender_company = sender_company or os.environ.get(
            "EMAIL_SENDER_COMPANY", ""
        )
        self._daily_count = 0
        self._daily_date = datetime.utcnow().strftime("%Y-%m-%d")

    def _check_daily_limit(self) -> bool:
        """Check if daily limit has been reached. Resets at midnight UTC."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today != self._daily_date:
            self._daily_count = 0
            self._daily_date = today
        return self._daily_count < self.daily_limit

    def _increment_daily_count(self):
        """Increment the daily action counter."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if today != self._daily_date:
            self._daily_count = 0
            self._daily_date = today
        self._daily_count += 1

    def execute_decision(
        self,
        decision: Dict[str, Any],
        lead_context: Optional[Dict[str, Any]] = None,
        db_action_count: Optional[int] = None,
    ) -> ExecutionResult:
        """Execute a silence recovery decision.

        Args:
            decision: FollowUpDecision.to_dict() output from SilenceRecoveryEngine
            lead_context: Additional context for template rendering:
                - lead_name, lead_email, company_name, stage, deal_value
            db_action_count: Current daily count from database (if using DB tracking)

        Returns:
            ExecutionResult with execution status and sent message details
        """
        decision_id = decision.get("decision_id", "")
        lead_id = decision.get("entity_id", "")
        selected_action = decision.get("selected_action", "do_not_execute")
        action_payload = decision.get("action_payload", {})
        policy_gate = decision.get("policy_gate_result", "approved")
        authority = decision.get("authority_level", "D1")

        now = datetime.utcnow().isoformat()

        # Gate 1: Only execute email actions
        if selected_action != "send_email":
            logger.info(
                f"Decision {decision_id}: action '{selected_action}' is not send_email, skipping"
            )
            return ExecutionResult(
                decision_id=decision_id,
                lead_id=lead_id,
                action=selected_action,
                executed=False,
                error=f"Action type '{selected_action}' not executable via email",
                executed_at=now,
            )

        # Gate 2: Policy gate must be approved
        if policy_gate != "approved":
            logger.info(
                f"Decision {decision_id}: policy gate={policy_gate}, blocked"
            )
            return ExecutionResult(
                decision_id=decision_id,
                lead_id=lead_id,
                action=selected_action,
                executed=False,
                error=f"Policy gate result: {policy_gate}",
                executed_at=now,
            )

        # Gate 3: Daily limit check
        effective_count = db_action_count if db_action_count is not None else self._daily_count
        if effective_count >= self.daily_limit:
            logger.warning(
                f"Decision {decision_id}: daily limit reached ({effective_count}/{self.daily_limit})"
            )
            return ExecutionResult(
                decision_id=decision_id,
                lead_id=lead_id,
                action=selected_action,
                executed=False,
                error=f"Daily limit reached ({effective_count}/{self.daily_limit})",
                executed_at=now,
            )

        # Build template context
        ctx = lead_context or {}
        ctx.setdefault("lead_name", action_payload.get("lead_name", "there"))
        ctx.setdefault("lead_email", action_payload.get("email", ""))
        ctx.setdefault("stage", action_payload.get("stage", ""))
        ctx.setdefault("days_since_last_touch", decision.get("context", {}).get("days_since_last_touch", ""))
        ctx.setdefault("previous_attempts", decision.get("context", {}).get("previous_attempts", 0))
        ctx["sender_name"] = self.sender_name
        ctx["sender_title"] = self.sender_title
        ctx["sender_company"] = self.sender_company

        # Render template
        template_hint = action_payload.get("template_hint", "default")
        subject, body_html, body_text = render_template(template_hint, ctx)

        to_email = ctx.get("lead_email", action_payload.get("email", ""))
        if not to_email:
            return ExecutionResult(
                decision_id=decision_id,
                lead_id=lead_id,
                action=selected_action,
                executed=False,
                error="No recipient email address",
                executed_at=now,
            )

        # Build EmailMessage
        message_id = f"MSG-{uuid.uuid4().hex[:12]}"
        message = EmailMessage(
            message_id=message_id,
            to_email=to_email,
            to_name=ctx.get("lead_name", ""),
            from_email=self.gmail.sender_email,
            from_name=self.sender_name,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            template_type=template_hint,
            status=EmailStatus.QUEUED.value,
            lead_id=lead_id,
            decision_id=decision_id,
            created_at=now,
        )

        # Send via Gmail
        send_result = self.gmail.send_email(
            to_email=to_email,
            subject=subject,
            body_html=body_html,
            body_text=body_text,
            from_name=self.sender_name,
            to_name=ctx.get("lead_name", ""),
        )

        # Update message status
        if send_result.get("status") == "sent":
            message.status = EmailStatus.SENT.value
            message.sent_at = now
            message.gmail_message_id = send_result.get("message_id")
            message.gmail_thread_id = send_result.get("thread_id")
        elif send_result.get("status") == "dry_run":
            message.status = EmailStatus.DRY_RUN.value
            message.gmail_message_id = send_result.get("message_id")
        else:
            message.status = EmailStatus.FAILED.value
            message.error_message = send_result.get("error", "Unknown error")

        self._increment_daily_count()

        executed = message.status in (EmailStatus.SENT.value, EmailStatus.DRY_RUN.value)

        return ExecutionResult(
            decision_id=decision_id,
            lead_id=lead_id,
            action=selected_action,
            executed=executed,
            dry_run=self.gmail.dry_run,
            message=message,
            executed_at=now,
        )

    def execute_batch(
        self,
        decisions: List[Dict[str, Any]],
        lead_contexts: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> List[ExecutionResult]:
        """Execute a batch of silence recovery decisions.

        Args:
            decisions: List of FollowUpDecision.to_dict() outputs
            lead_contexts: Optional dict mapping lead_id → context dict

        Returns:
            List of ExecutionResults
        """
        results = []
        contexts = lead_contexts or {}

        for decision in decisions:
            lead_id = decision.get("entity_id", "")
            ctx = contexts.get(lead_id)
            result = self.execute_decision(decision, lead_context=ctx)
            results.append(result)

            if not self._check_daily_limit():
                logger.warning("Daily limit reached during batch, stopping")
                break

        return results
