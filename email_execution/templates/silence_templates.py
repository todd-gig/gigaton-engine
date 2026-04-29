"""Email templates for silence recovery actions.

Template system aligned with SilenceRecoveryEngine's template_hint values.
Each template renders subject + body given a context dict containing:
  - lead_name, lead_email, company_name, stage, deal_value
  - days_since_last_touch, previous_attempts
  - sender_name, sender_title, sender_company
"""

from typing import Dict, Any, Tuple


def _safe(ctx: Dict[str, Any], key: str, default: str = "") -> str:
    """Safely get a string value from context."""
    val = ctx.get(key, default)
    return str(val) if val else default


def render_template(template_hint: str, context: Dict[str, Any]) -> Tuple[str, str, str]:
    """Render an email template by hint name.

    Args:
        template_hint: Template key from SilenceRecoveryEngine
        context: Dict with lead/sender data for personalization

    Returns:
        Tuple of (subject, body_html, body_text)
    """
    renderer = TEMPLATE_REGISTRY.get(template_hint, _render_default)
    return renderer(context)


# ── Template Renderers ───────────────────────────────────────────

def _render_initial_follow_up(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    company = _safe(ctx, "sender_company", "")
    subject = f"Following up — quick question for you"
    body_text = (
        f"Hi {lead},\n\n"
        f"I wanted to follow up on our recent conversation. "
        f"I know things get busy, so I'm keeping this brief.\n\n"
        f"Would it be helpful to schedule a quick 15-minute call "
        f"this week to discuss how we might help with the challenges "
        f"you mentioned?\n\n"
        f"No pressure at all — just want to make sure I'm being "
        f"helpful rather than adding to the noise.\n\n"
        f"Best,\n{sender}"
        + (f"\n{company}" if company else "")
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


def _render_follow_up_2nd_touch(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    company = _safe(ctx, "sender_company", "")
    days = _safe(ctx, "days_since_last_touch", "a few")
    subject = f"Checking in — still interested in connecting?"
    body_text = (
        f"Hi {lead},\n\n"
        f"I reached out about {days} days ago and wanted to check in. "
        f"I understand priorities shift, so if now isn't the right time, "
        f"that's completely fine.\n\n"
        f"If things have changed and you'd like to revisit the conversation, "
        f"I'm here. Would any of these work for a quick chat?\n\n"
        f"- Tomorrow morning\n"
        f"- Later this week\n"
        f"- Next week works better\n\n"
        f"Either way, wishing you a great week.\n\n"
        f"Best,\n{sender}"
        + (f"\n{company}" if company else "")
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


def _render_re_engagement_3rd_touch(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    company = _safe(ctx, "sender_company", "")
    subject = f"One last thought before I close the loop"
    body_text = (
        f"Hi {lead},\n\n"
        f"I've reached out a couple of times and don't want to be "
        f"a bother. I'll keep this simple:\n\n"
        f"If you're still exploring solutions in this space, I'd love "
        f"to share a brief case study that might be relevant to your "
        f"situation. No call required — just a quick read.\n\n"
        f"If the timing isn't right, no worries at all. I'll close "
        f"the loop on my end, and you're always welcome to reach out "
        f"when it makes sense.\n\n"
        f"Best,\n{sender}"
        + (f"\n{company}" if company else "")
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


def _render_high_value_escalation(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    sender_title = _safe(ctx, "sender_title", "")
    company = _safe(ctx, "sender_company", "")
    subject = f"Personal note from {sender}"
    body_text = (
        f"Hi {lead},\n\n"
        f"I'm reaching out personally because I believe there's a "
        f"meaningful opportunity for us to work together.\n\n"
        f"I've taken a closer look at your situation and have some "
        f"specific ideas on how we could create measurable value. "
        f"Would you be open to a brief conversation?\n\n"
        f"I'm flexible on timing and happy to work around your "
        f"schedule.\n\n"
        f"Warmly,\n{sender}"
        + (f"\n{sender_title}" if sender_title else "")
        + (f"\n{company}" if company else "")
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


def _render_value_reminder(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    company = _safe(ctx, "sender_company", "")
    subject = f"A resource that might help"
    body_text = (
        f"Hi {lead},\n\n"
        f"I came across something that made me think of the "
        f"challenges you mentioned. Thought it might be useful.\n\n"
        f"No strings attached — just wanted to share in case "
        f"it's helpful for your team.\n\n"
        f"Happy to discuss further if anything resonates.\n\n"
        f"Best,\n{sender}"
        + (f"\n{company}" if company else "")
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


def _render_breakup(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    company = _safe(ctx, "sender_company", "")
    subject = f"Closing the loop"
    body_text = (
        f"Hi {lead},\n\n"
        f"I've reached out a few times and haven't heard back, "
        f"which is totally okay. I want to respect your time.\n\n"
        f"I'm going to close this on my end for now. If anything "
        f"changes down the road, my door is always open.\n\n"
        f"Wishing you and your team all the best.\n\n"
        f"Best,\n{sender}"
        + (f"\n{company}" if company else "")
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


def _render_default(ctx: Dict[str, Any]) -> Tuple[str, str, str]:
    lead = _safe(ctx, "lead_name", "there")
    sender = _safe(ctx, "sender_name", "Our Team")
    subject = f"Quick follow-up"
    body_text = (
        f"Hi {lead},\n\n"
        f"Just wanted to check in and see if there's anything "
        f"I can help with.\n\n"
        f"Best,\n{sender}"
    )
    body_html = body_text.replace("\n", "<br>")
    return subject, body_html, body_text


# ── Template Registry ────────────────────────────────────────────

TEMPLATE_REGISTRY = {
    "initial_follow_up": _render_initial_follow_up,
    "follow_up_2nd_touch": _render_follow_up_2nd_touch,
    "re_engagement_3rd_touch": _render_re_engagement_3rd_touch,
    "high_value_escalation": _render_high_value_escalation,
    "value_reminder": _render_value_reminder,
    "breakup": _render_breakup,
    "alternate_strategy_task": _render_value_reminder,  # reuse value template
    "assignment_task": _render_default,
    "default": _render_default,
}
