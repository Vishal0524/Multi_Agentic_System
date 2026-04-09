"""
NEXUS MCP Tool Wrappers
Adapts Gmail (Composio), Mailgun, Linear, and Calendar tools
into a unified interface for ADK agents.

In DEMO MODE: returns rich mock responses without hitting real APIs.
"""
import os
import uuid
import json
import httpx
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

APP_MODE = os.getenv("APP_MODE", "demo")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "demo")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "sandbox.mailgun.org")
MAILGUN_FROM = os.getenv("MAILGUN_FROM_EMAIL", f"nexus@{MAILGUN_DOMAIN}")
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY", "demo")
LINEAR_TEAM_ID = os.getenv("LINEAR_TEAM_ID", "demo-team")


def is_demo() -> bool:
    return APP_MODE == "demo" or MAILGUN_API_KEY == "demo"


# ─── Gmail Tool ────────────────────────────────────────────────────────────────

async def gmail_get_inbox(max_results: int = 10) -> Dict:
    """Fetch recent emails from Gmail via Composio MCP"""
    if is_demo():
        return {
            "success": True,
            "source": "demo",
            "emails": [
                {
                    "id": "gmail-001",
                    "subject": "Re: Series A Term Sheet — Follow-up Questions",
                    "from": "david.kim@sequoiacap.com",
                    "snippet": "Hi Sarah, great call yesterday. We'd like to schedule a technical deep-dive with our engineering partner.",
                    "date": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "important": True,
                    "labels": ["INBOX", "IMPORTANT"],
                },
                {
                    "id": "gmail-002",
                    "subject": "Investor Demo Confirmed — Tomorrow 2PM",
                    "from": "lisa.park@a16z.com",
                    "snippet": "Confirmed for tomorrow at 2PM PST. We'll have 3 partners joining. Please have the live demo ready.",
                    "date": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "important": True,
                    "labels": ["INBOX", "IMPORTANT"],
                },
                {
                    "id": "gmail-003",
                    "subject": "Linear — 3 tasks require your attention",
                    "from": "notifications@linear.app",
                    "snippet": "ALPHA-42 is due in 2 days. ALPHA-50 is due today. FUND-12 is marked urgent by Priya.",
                    "date": (datetime.now() - timedelta(hours=8)).isoformat(),
                    "important": False,
                    "labels": ["INBOX"],
                },
                {
                    "id": "gmail-004",
                    "subject": "AWS Cost Alert — Spending up 34% this month",
                    "from": "aws-billing@amazon.com",
                    "snippet": "Your AWS bill for this month is projected to be $4,280 — 34% higher than last month due to increased EC2 usage.",
                    "date": (datetime.now() - timedelta(hours=12)).isoformat(),
                    "important": False,
                    "labels": ["INBOX"],
                },
                {
                    "id": "gmail-005",
                    "subject": "Welcome to NEXUS — Your setup is complete",
                    "from": "noreply@nexus.ai",
                    "snippet": "Your NEXUS multi-agent workspace is ready. 4 agents are standing by.",
                    "date": (datetime.now() - timedelta(days=1)).isoformat(),
                    "important": False,
                    "labels": ["INBOX"],
                },
            ]
        }

    # Live: use Composio Gmail MCP
    try:
        import composio_google
        # Composio Gmail integration would be initialized here
        return {"success": False, "error": "Composio not configured in live mode"}
    except Exception as e:
        logger.error(f"Gmail tool error: {e}")
        return {"success": False, "error": str(e)}


async def gmail_get_important() -> Dict:
    """Get important/starred emails"""
    result = await gmail_get_inbox()
    if result["success"]:
        result["emails"] = [e for e in result["emails"] if e.get("important")]
    return result


# ─── Mailgun Tool ──────────────────────────────────────────────────────────────

async def mailgun_send_email(
    to: List[str],
    subject: str,
    body_html: str,
    body_text: Optional[str] = None,
) -> Dict:
    """
    Send email via Mailgun.
    In demo/sandbox mode: email appears in Mailgun logs but NOT in real inboxes.
    """
    if is_demo():
        msg_id = f"demo-{uuid.uuid4().hex[:12]}@sandbox.mailgun.org"
        logger.info(f"[MAILGUN DEMO] Sending: '{subject}' → {to}")
        return {
            "success": True,
            "source": "mailgun_sandbox",
            "message_id": msg_id,
            "message": f"Email queued in Mailgun sandbox (test mode — not delivered to real inboxes)",
            "to": to,
            "subject": subject,
            "preview": body_text[:200] if body_text else body_html[:200],
        }

    # Live Mailgun API call
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
                auth=("api", MAILGUN_API_KEY),
                data={
                    "from": MAILGUN_FROM,
                    "to": to,
                    "subject": subject,
                    "html": body_html,
                    "text": body_text or "",
                    "o:testmode": "yes",  # Always use test mode for safety
                },
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            return {
                "success": True,
                "source": "mailgun_live",
                "message_id": data.get("id"),
                "message": data.get("message"),
                "to": to,
                "subject": subject,
            }
    except Exception as e:
        logger.error(f"Mailgun error: {e}")
        return {"success": False, "error": str(e)}


# ─── Linear Tool ──────────────────────────────────────────────────────────────

MOCK_LINEAR_ISSUES = [
    {"id": "ALPHA-42", "title": "Design system architecture for Q4 platform", "state": "In Progress", "priority": 1, "assignee": "Sarah Chen", "dueDate": "2024-10-15"},
    {"id": "ALPHA-43", "title": "Integrate Stripe payment processing", "state": "Todo", "priority": 2, "assignee": "Marcus Webb", "dueDate": "2024-10-18"},
    {"id": "ALPHA-50", "title": "Launch NEXUS v1.0 demo environment", "state": "In Progress", "priority": 1, "assignee": "Sarah Chen", "dueDate": "2024-10-10"},
    {"id": "FUND-12", "title": "Write investor deck copy", "state": "In Progress", "priority": 1, "assignee": "Priya Kapoor", "dueDate": "2024-10-11"},
    {"id": "DEV-08", "title": "Set up CI/CD pipeline with GitHub Actions", "state": "Done", "priority": 2, "assignee": "Sarah Chen", "dueDate": "2024-10-08"},
]


async def linear_get_issues(team_id: Optional[str] = None, status: Optional[str] = None) -> Dict:
    """Fetch issues from Linear"""
    if is_demo():
        issues = MOCK_LINEAR_ISSUES
        if status:
            issues = [i for i in issues if i["state"].lower().replace(" ", "_") == status.lower()]
        return {"success": True, "source": "demo", "issues": issues, "total": len(issues)}

    try:
        async with httpx.AsyncClient() as client:
            query = """
            query Issues($teamId: String) {
              issues(filter: { team: { id: { eq: $teamId } } }) {
                nodes {
                  id identifier title state { name } priority
                  assignee { name } dueDate
                }
              }
            }
            """
            response = await client.post(
                "https://api.linear.app/graphql",
                headers={"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"},
                json={"query": query, "variables": {"teamId": team_id or LINEAR_TEAM_ID}},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            issues = data.get("data", {}).get("issues", {}).get("nodes", [])
            return {"success": True, "source": "linear_live", "issues": issues, "total": len(issues)}
    except Exception as e:
        logger.error(f"Linear error: {e}")
        return {"success": False, "error": str(e)}


async def linear_create_issue(
    title: str,
    description: str = "",
    priority: int = 2,
    assignee_id: Optional[str] = None,
) -> Dict:
    """Create a new issue in Linear"""
    if is_demo():
        issue_id = f"ALPHA-{uuid.uuid4().int % 100 + 51}"
        return {
            "success": True,
            "source": "demo",
            "issue": {
                "id": issue_id, "title": title, "description": description,
                "state": "Todo", "priority": priority,
                "url": f"https://linear.app/team/issue/{issue_id}",
            },
            "message": f"Issue {issue_id} created in Linear (demo mode)",
        }

    try:
        async with httpx.AsyncClient() as client:
            mutation = """
            mutation CreateIssue($input: IssueCreateInput!) {
              issueCreate(input: $input) {
                success issue { id identifier title url }
              }
            }
            """
            variables = {
                "input": {
                    "teamId": LINEAR_TEAM_ID,
                    "title": title,
                    "description": description,
                    "priority": priority,
                }
            }
            response = await client.post(
                "https://api.linear.app/graphql",
                headers={"Authorization": LINEAR_API_KEY, "Content-Type": "application/json"},
                json={"query": mutation, "variables": variables},
                timeout=15.0,
            )
            response.raise_for_status()
            data = response.json()
            issue = data.get("data", {}).get("issueCreate", {}).get("issue", {})
            return {"success": True, "source": "linear_live", "issue": issue}
    except Exception as e:
        logger.error(f"Linear create error: {e}")
        return {"success": False, "error": str(e)}


async def linear_update_issue(issue_id: str, status: str) -> Dict:
    """Update an issue's status in Linear"""
    if is_demo():
        return {
            "success": True, "source": "demo",
            "message": f"Issue {issue_id} updated to '{status}' in Linear (demo mode)",
        }

    # Live Linear update would go here
    return {"success": False, "error": "Not configured"}


# ─── Calendar Tool ─────────────────────────────────────────────────────────────

async def calendar_get_today() -> Dict:
    """Get today's calendar events"""
    from database.db import db_get_events
    events = await db_get_events()
    today = datetime.now().date().isoformat()
    today_events = [e for e in events if e["start_time"].startswith(today)]
    return {
        "success": True,
        "source": "local_db",
        "date": today,
        "events": today_events,
        "count": len(today_events),
    }


async def calendar_get_week() -> Dict:
    """Get this week's calendar events"""
    from database.db import db_get_events
    events = await db_get_events()
    return {
        "success": True,
        "source": "local_db",
        "events": events,
        "count": len(events),
    }


async def calendar_check_conflicts(start: str, end: str) -> Dict:
    """Check for scheduling conflicts"""
    from database.db import db_get_events
    events = await db_get_events()
    conflicts = []
    for e in events:
        if e["start_time"] < end and e["end_time"] > start:
            conflicts.append(e)
    return {
        "success": True,
        "has_conflicts": len(conflicts) > 0,
        "conflicts": conflicts,
    }


# ─── Tool Registry (ADK-compatible) ────────────────────────────────────────────

TOOL_REGISTRY = {
    "gmail_get_inbox": gmail_get_inbox,
    "gmail_get_important": gmail_get_important,
    "mailgun_send_email": mailgun_send_email,
    "linear_get_issues": linear_get_issues,
    "linear_create_issue": linear_create_issue,
    "linear_update_issue": linear_update_issue,
    "calendar_get_today": calendar_get_today,
    "calendar_get_week": calendar_get_week,
    "calendar_check_conflicts": calendar_check_conflicts,
}


async def execute_tool(tool_name: str, **kwargs) -> Dict:
    """Execute a registered tool by name"""
    if tool_name not in TOOL_REGISTRY:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    try:
        result = await TOOL_REGISTRY[tool_name](**kwargs)
        return result
    except Exception as e:
        logger.error(f"Tool execution error [{tool_name}]: {e}")
        return {"success": False, "error": str(e)}
