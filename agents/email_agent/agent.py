"""
Email Agent — Manages email drafting, sending (via Mailgun sandbox), and listing.
"""

import os
import sys
import json
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from google.adk.agents.llm_agent import Agent
from database import db

logger = logging.getLogger(__name__)


def _get_mailgun_config():
    """Get Mailgun configuration from environment."""
    api_key = os.environ.get("MAILGUN_API_KEY", "")
    domain = os.environ.get("MAILGUN_SANDBOX_DOMAIN", "")
    return api_key, domain


def _send_via_mailgun(sender: str, recipients: str, subject: str, body: str) -> dict:
    """Attempt to send email via Mailgun sandbox. Falls back to mock if not configured."""
    api_key, domain = _get_mailgun_config()

    if not api_key or not domain or api_key == "YOUR_MAILGUN_API_KEY_HERE":
        # Mock mode - log the email as if sent
        logger.info(f"[MOCK EMAIL] To: {recipients} | Subject: {subject}")
        return {
            "mode": "mock",
            "message": "Email logged in mock mode (Mailgun not configured)",
            "id": f"mock_{hash(subject) % 100000}"
        }

    try:
        import requests
        response = requests.post(
            f"https://api.mailgun.net/v3/{domain}/messages",
            auth=("api", api_key),
            data={
                "from": f"Productivity Assistant <mailgun@{domain}>",
                "to": recipients.split(","),
                "subject": subject,
                "text": body,
                "o:testmode": "yes"  # Sandbox test mode - no real delivery
            },
            timeout=10
        )
        if response.status_code == 200:
            return {"mode": "mailgun_sandbox", "message": "Email sent via Mailgun sandbox (test mode)", "response": response.json()}
        else:
            return {"mode": "mock", "message": f"Mailgun returned {response.status_code}, falling back to mock mode"}
    except Exception as e:
        logger.warning(f"Mailgun send failed: {e}, using mock mode")
        return {"mode": "mock", "message": f"Mailgun unavailable, email logged in mock mode"}


# ─── TOOL FUNCTIONS ─────────────────────────────────────────

def send_email(subject: str, recipients: str, body: str, sender: str = "assistant@company.com") -> dict:
    """Send an email via Mailgun sandbox (test mode) or mock mode.
    
    Args:
        subject: Email subject line (required).
        recipients: Comma-separated list of recipient email addresses (required).
        body: Email body text (required).
        sender: Sender email address (defaults to assistant@company.com).
    
    Returns:
        Dictionary with send status and confirmation details.
    """
    # Try sending via Mailgun
    send_result = _send_via_mailgun(sender, recipients, subject, body)

    # Save to database
    email = db.create_email(
        subject=subject, sender=sender, recipients=recipients,
        body=body, status="sent", thread_id=f"thread_{hash(subject) % 100000}"
    )

    return {
        "status": "success",
        "message": f"Email '{subject}' sent to {recipients}",
        "delivery": send_result,
        "email": email
    }


def draft_email(subject: str, recipients: str, body: str, sender: str = "assistant@company.com") -> dict:
    """Create an email draft without sending it.
    
    Args:
        subject: Email subject line (required).
        recipients: Comma-separated list of recipient email addresses (required).
        body: Email body text (required).
        sender: Sender email address.
    
    Returns:
        Dictionary with the created draft details.
    """
    email = db.create_email(
        subject=subject, sender=sender, recipients=recipients,
        body=body, status="draft"
    )
    return {"status": "success", "message": f"Draft '{subject}' saved", "email": email}


def list_emails(status: str = "") -> dict:
    """List all emails, optionally filtered by status.
    
    Args:
        status: Filter by email status (draft, sent, received, failed). Leave empty for all.
    
    Returns:
        Dictionary with list of emails and count.
    """
    emails = db.list_emails(status=status if status else None)
    return {"status": "success", "count": len(emails), "emails": emails}


# ─── AGENT DEFINITION ──────────────────────────────────────

email_agent = Agent(
    model="gemini-2.0-flash",
    name="email_agent",
    description="Manages emails - send via Mailgun sandbox, draft, and list email communications.",
    instruction="""You are the Email Agent, a specialized AI assistant for email management.

Your capabilities:
- Send emails via Mailgun sandbox (test mode - no real delivery, safe for demos)
- Create email drafts for review before sending
- List all emails (sent, received, drafts)

When composing emails:
- Write professional, concise email content
- Include proper greetings and sign-offs
- Format the body with clear paragraphs

When listing emails, show:
- 📧 Subject line
- 👤 Sender/Recipients
- 📊 Status (sent/draft/received)
- 🕐 Timestamp

Note: Emails are sent via Mailgun sandbox test mode, meaning they are logged but not delivered to real inboxes. This is perfect for demos and testing.""",
    tools=[send_email, draft_email, list_emails],
)
