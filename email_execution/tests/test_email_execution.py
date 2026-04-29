"""Tests for email execution engine."""

import sys
import os
import pytest

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from email_execution.engines.gmail_client import GmailClient
from email_execution.engines.execution_engine import EmailExecutionEngine
from email_execution.models.email_models import EmailStatus, TemplateType
from email_execution.templates.silence_templates import render_template, TEMPLATE_REGISTRY


class TestTemplateRendering:
    def test_all_templates_render(self):
        ctx = {
            "lead_name": "Sarah",
            "sender_name": "Todd",
            "sender_company": "Turtle Island",
            "sender_title": "CX Architect",
            "days_since_last_touch": "5",
        }
        for key in TEMPLATE_REGISTRY:
            subject, html, text = render_template(key, ctx)
            assert len(subject) > 0, f"Template {key} has empty subject"
            assert len(html) > 0, f"Template {key} has empty html"
            assert len(text) > 0, f"Template {key} has empty text"
            assert "Sarah" in text, f"Template {key} missing lead name"

    def test_initial_follow_up(self):
        subject, html, text = render_template("initial_follow_up", {
            "lead_name": "Alice",
            "sender_name": "Bob",
        })
        assert "follow up" in subject.lower() or "following" in subject.lower()
        assert "Alice" in text
        assert "Bob" in text

    def test_breakup_template(self):
        subject, html, text = render_template("breakup", {
            "lead_name": "Dave",
            "sender_name": "Eve",
        })
        assert "Dave" in text
        assert "close" in text.lower() or "loop" in text.lower()

    def test_missing_context_uses_defaults(self):
        subject, html, text = render_template("initial_follow_up", {})
        assert "there" in text  # default lead_name
        assert len(subject) > 0


class TestGmailClientDryRun:
    def test_dry_run_returns_mock_id(self):
        client = GmailClient(dry_run=True)
        result = client.send_email(
            to_email="test@example.com",
            subject="Test",
            body_html="<p>Hello</p>",
            body_text="Hello",
        )
        assert result["status"] == "dry_run"
        assert result["dry_run"] is True
        assert result["message_id"].startswith("dry_run_")

    def test_is_configured_in_dry_run(self):
        client = GmailClient(dry_run=True)
        assert client.is_configured() is True

    def test_default_is_dry_run(self):
        client = GmailClient()
        assert client.dry_run is True


class TestEmailExecutionEngine:
    @pytest.fixture
    def engine(self):
        gmail = GmailClient(dry_run=True, sender_email="sender@example.com")
        return EmailExecutionEngine(
            gmail_client=gmail,
            daily_limit=10,
            sender_name="Test Sender",
            sender_company="Test Corp",
        )

    def test_execute_send_email(self, engine):
        decision = {
            "decision_id": "DEC-001",
            "entity_id": "lead-001",
            "selected_action": "send_email",
            "action_payload": {
                "email": "lead@example.com",
                "template_hint": "initial_follow_up",
                "lead_name": "Sarah",
            },
            "policy_gate_result": "approved",
            "authority_level": "D1",
            "context": {"days_since_last_touch": 5},
        }
        result = engine.execute_decision(decision)
        assert result.executed is True
        assert result.dry_run is True
        assert result.message is not None
        assert result.message.status == EmailStatus.DRY_RUN.value
        assert result.message.to_email == "lead@example.com"

    def test_skip_non_email_action(self, engine):
        decision = {
            "decision_id": "DEC-002",
            "entity_id": "lead-002",
            "selected_action": "create_task",
            "action_payload": {},
            "policy_gate_result": "approved",
        }
        result = engine.execute_decision(decision)
        assert result.executed is False
        assert "not executable" in result.error

    def test_blocked_by_policy_gate(self, engine):
        decision = {
            "decision_id": "DEC-003",
            "entity_id": "lead-003",
            "selected_action": "send_email",
            "action_payload": {"email": "x@y.com"},
            "policy_gate_result": "blocked",
        }
        result = engine.execute_decision(decision)
        assert result.executed is False

    def test_daily_limit_enforcement(self, engine):
        decision = {
            "decision_id": "DEC-004",
            "entity_id": "lead-004",
            "selected_action": "send_email",
            "action_payload": {
                "email": "lead@example.com",
                "template_hint": "default",
            },
            "policy_gate_result": "approved",
            "context": {},
        }
        # Send up to limit
        for i in range(10):
            result = engine.execute_decision(decision)
            assert result.executed is True

        # 11th should be blocked
        result = engine.execute_decision(decision)
        assert result.executed is False
        assert "Daily limit" in result.error

    def test_missing_email(self, engine):
        decision = {
            "decision_id": "DEC-005",
            "entity_id": "lead-005",
            "selected_action": "send_email",
            "action_payload": {"template_hint": "default"},
            "policy_gate_result": "approved",
            "context": {},
        }
        result = engine.execute_decision(decision)
        assert result.executed is False
        assert "No recipient" in result.error

    def test_batch_execution(self, engine):
        decisions = [
            {
                "decision_id": f"DEC-B{i}",
                "entity_id": f"lead-b{i}",
                "selected_action": "send_email",
                "action_payload": {
                    "email": f"lead{i}@example.com",
                    "template_hint": "initial_follow_up",
                },
                "policy_gate_result": "approved",
                "context": {},
            }
            for i in range(3)
        ]
        results = engine.execute_batch(decisions)
        assert len(results) == 3
        assert all(r.executed for r in results)

    def test_template_context_from_decision(self, engine):
        decision = {
            "decision_id": "DEC-006",
            "entity_id": "lead-006",
            "selected_action": "send_email",
            "action_payload": {
                "email": "alice@example.com",
                "template_hint": "follow_up_2nd_touch",
                "lead_name": "Alice",
            },
            "policy_gate_result": "approved",
            "context": {"days_since_last_touch": 7},
        }
        result = engine.execute_decision(decision)
        assert result.executed is True
        assert "Alice" in result.message.body_text or "there" in result.message.body_text
