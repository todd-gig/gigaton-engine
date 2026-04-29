"""Gmail API client for sending emails via Google Workspace.

Authentication via OAuth2 service account or user credentials.
Controlled by environment variables:
  GMAIL_CREDENTIALS_JSON — path to OAuth2 credentials JSON file
  GMAIL_TOKEN_JSON — path to stored token (auto-refreshed)
  GMAIL_SENDER_EMAIL — sender email address
  GMAIL_DRY_RUN — if "true", log but don't send (default: "true")

Requires: google-auth, google-auth-oauthlib, google-api-python-client
"""

import base64
import json
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class GmailClient:
    """Gmail API client with OAuth2 authentication.

    Supports two modes:
      - dry_run=True (default): logs email content, returns mock message ID
      - dry_run=False: sends via Gmail API

    Environment-driven configuration:
      GMAIL_CREDENTIALS_JSON — path to OAuth2 credentials
      GMAIL_TOKEN_JSON — path to cached token
      GMAIL_SENDER_EMAIL — default from address
      GMAIL_DRY_RUN — "true"/"false" (default: "true")
    """

    SCOPES = ["https://www.googleapis.com/auth/gmail.send"]

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        token_path: Optional[str] = None,
        sender_email: Optional[str] = None,
        dry_run: Optional[bool] = None,
    ):
        self.credentials_path = credentials_path or os.environ.get(
            "GMAIL_CREDENTIALS_JSON", ""
        )
        self.token_path = token_path or os.environ.get(
            "GMAIL_TOKEN_JSON", "token.json"
        )
        self.sender_email = sender_email or os.environ.get(
            "GMAIL_SENDER_EMAIL", ""
        )

        # Default to dry run unless explicitly disabled
        if dry_run is not None:
            self.dry_run = dry_run
        else:
            self.dry_run = os.environ.get("GMAIL_DRY_RUN", "true").lower() != "false"

        self._service = None

    def _get_service(self):
        """Initialize Gmail API service with OAuth2 credentials.

        Lazily creates the service on first use. Handles token refresh.
        """
        if self._service is not None:
            return self._service

        if self.dry_run:
            logger.info("Gmail client in DRY RUN mode — no API service needed")
            return None

        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
        except ImportError:
            raise RuntimeError(
                "Gmail API requires google-auth, google-auth-oauthlib, "
                "and google-api-python-client. Install with:\n"
                "  pip install google-auth google-auth-oauthlib google-api-python-client"
            )

        creds = None

        # Load existing token
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, self.SCOPES)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not self.credentials_path or not os.path.exists(self.credentials_path):
                    raise RuntimeError(
                        f"Gmail credentials file not found: {self.credentials_path}. "
                        f"Set GMAIL_CREDENTIALS_JSON env var to your OAuth2 credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, self.SCOPES
                )
                creds = flow.run_local_server(port=0)

            # Save token for next run
            with open(self.token_path, "w") as token_file:
                token_file.write(creds.to_json())

        self._service = build("gmail", "v1", credentials=creds)
        logger.info("Gmail API service initialized successfully")
        return self._service

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_html: str,
        body_text: str = "",
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        to_name: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send an email via Gmail API.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            body_html: HTML body content
            body_text: Plain text body (fallback)
            from_email: Sender email (defaults to GMAIL_SENDER_EMAIL)
            from_name: Sender display name
            to_name: Recipient display name
            thread_id: Gmail thread ID to reply into (optional)

        Returns:
            Dict with keys: message_id, thread_id, status, dry_run
        """
        sender = from_email or self.sender_email
        if from_name:
            sender_header = f"{from_name} <{sender}>"
        else:
            sender_header = sender

        if to_name:
            to_header = f"{to_name} <{to_email}>"
        else:
            to_header = to_email

        # DRY RUN mode
        if self.dry_run:
            logger.info(
                f"[DRY RUN] Would send email:\n"
                f"  From: {sender_header}\n"
                f"  To: {to_header}\n"
                f"  Subject: {subject}\n"
                f"  Body length: {len(body_html)} chars"
            )
            import uuid
            mock_id = f"dry_run_{uuid.uuid4().hex[:12]}"
            return {
                "message_id": mock_id,
                "thread_id": thread_id or f"thread_{mock_id}",
                "status": "dry_run",
                "dry_run": True,
            }

        # Build MIME message
        message = MIMEMultipart("alternative")
        message["to"] = to_header
        message["from"] = sender_header
        message["subject"] = subject

        if body_text:
            message.attach(MIMEText(body_text, "plain"))
        message.attach(MIMEText(body_html, "html"))

        # Encode for Gmail API
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
        body = {"raw": raw}
        if thread_id:
            body["threadId"] = thread_id

        # Send via Gmail API
        service = self._get_service()
        try:
            sent = service.users().messages().send(
                userId="me", body=body
            ).execute()

            result = {
                "message_id": sent.get("id", ""),
                "thread_id": sent.get("threadId", ""),
                "status": "sent",
                "dry_run": False,
            }
            logger.info(f"Email sent: {result['message_id']} to {to_email}")
            return result

        except Exception as e:
            logger.error(f"Gmail send failed: {e}")
            return {
                "message_id": "",
                "thread_id": "",
                "status": "failed",
                "dry_run": False,
                "error": str(e),
            }

    def is_configured(self) -> bool:
        """Check if Gmail client has minimum configuration for sending."""
        if self.dry_run:
            return True
        return bool(self.credentials_path and self.sender_email)
