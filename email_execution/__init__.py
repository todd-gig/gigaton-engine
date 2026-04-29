"""Email Execution — Gmail-based email sending for silence recovery actions.

Env vars:
  GMAIL_CREDENTIALS_JSON — OAuth2 credentials file path
  GMAIL_TOKEN_JSON — cached token path
  GMAIL_SENDER_EMAIL — sender email address
  GMAIL_DRY_RUN — "true"/"false" (default: "true")
  EMAIL_DAILY_LIMIT — max emails/day (default: 50)
  EMAIL_SENDER_NAME — display name
  EMAIL_SENDER_TITLE — title for escalation emails
  EMAIL_SENDER_COMPANY — company name in signatures
"""
