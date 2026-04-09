"""
NEXUS Demo Seed Data
Populates the database with rich mock data for investor demo
"""
import json
import uuid
from datetime import datetime, timedelta
from database.db import (
    AsyncSessionLocal, Task, ScheduleEvent, Note, EmailRecord,
    AgentActivity, WorkflowRun, Base, engine
)


def ts(days_offset=0, hour=9, minute=0):
    """Generate ISO timestamp relative to today"""
    dt = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
    dt += timedelta(days=days_offset)
    return dt.isoformat()


TASKS = [
    {
        "id": "task-001", "title": "Design system architecture for Q4 platform",
        "description": "Define microservices boundaries, API contracts, and data flow diagrams for the new platform.",
        "status": "in_progress", "priority": "urgent", "assignee": "Sarah Chen",
        "project": "Alpha Platform", "due_date": ts(2),
        "linear_id": "ALPHA-42", "tags": json.dumps(["architecture", "backend", "q4"]),
    },
    {
        "id": "task-002", "title": "Integrate Stripe payment processing",
        "description": "Add subscription billing with Stripe, including webhook handlers for payment events.",
        "status": "todo", "priority": "high", "assignee": "Marcus Webb",
        "project": "Alpha Platform", "due_date": ts(5),
        "linear_id": "ALPHA-43", "tags": json.dumps(["payments", "backend"]),
    },
    {
        "id": "task-003", "title": "Write investor deck copy",
        "description": "Update pitch deck with latest traction metrics and updated TAM analysis.",
        "status": "in_progress", "priority": "urgent", "assignee": "Priya Kapoor",
        "project": "Fundraising", "due_date": ts(1),
        "linear_id": "FUND-12", "tags": json.dumps(["investors", "deck"]),
    },
    {
        "id": "task-004", "title": "Set up CI/CD pipeline with GitHub Actions",
        "description": "Automate test → build → deploy across staging and production environments.",
        "status": "done", "priority": "high", "assignee": "Sarah Chen",
        "project": "DevOps", "due_date": ts(-2),
        "linear_id": "DEV-08", "tags": json.dumps(["devops", "automation"]),
    },
    {
        "id": "task-005", "title": "User interviews for onboarding redesign",
        "description": "Conduct 10 user interviews, synthesize findings into redesign brief.",
        "status": "todo", "priority": "medium", "assignee": "Priya Kapoor",
        "project": "Product", "due_date": ts(7),
        "linear_id": "PROD-21", "tags": json.dumps(["research", "ux"]),
    },
    {
        "id": "task-006", "title": "Security audit — API endpoints",
        "description": "Review all public API endpoints for authentication gaps and rate limiting.",
        "status": "todo", "priority": "high", "assignee": "Marcus Webb",
        "project": "Security", "due_date": ts(4),
        "linear_id": "SEC-05", "tags": json.dumps(["security", "api"]),
    },
    {
        "id": "task-007", "title": "Launch NEXUS v1.0 demo environment",
        "description": "Deploy the multi-agent system to demo servers, seed with mock data, test all workflows.",
        "status": "in_progress", "priority": "urgent", "assignee": "Sarah Chen",
        "project": "Alpha Platform", "due_date": ts(0),
        "linear_id": "ALPHA-50", "tags": json.dumps(["launch", "demo", "nexus"]),
    },
    {
        "id": "task-008", "title": "Compile weekly metrics dashboard",
        "description": "Pull MAU, DAU, churn rate, and NPS from analytics and prepare executive summary.",
        "status": "todo", "priority": "medium", "assignee": "Priya Kapoor",
        "project": "Analytics", "due_date": ts(1),
        "linear_id": "ANA-15", "tags": json.dumps(["metrics", "weekly"]),
    },
]

EVENTS = [
    {
        "id": "evt-001", "title": "Investor Demo — Series A Pitch",
        "description": "Live demonstration of NEXUS multi-agent system for Series A investors. Full workflow showcase.",
        "start_time": ts(0, 14, 0), "end_time": ts(0, 15, 30),
        "attendees": json.dumps(["Sarah Chen", "Marcus Webb", "Priya Kapoor", "David Kim (Sequoia)", "Lisa Park (a16z)"]),
        "location": "HQ — Board Room A", "meeting_link": "https://meet.google.com/abc-defg-hij",
        "event_type": "demo",
    },
    {
        "id": "evt-002", "title": "Engineering Standup",
        "description": "Daily sync — blockers, progress, priorities.",
        "start_time": ts(0, 9, 30), "end_time": ts(0, 10, 0),
        "attendees": json.dumps(["Sarah Chen", "Marcus Webb", "Dev Team"]),
        "location": "Slack Huddle", "event_type": "standup",
    },
    {
        "id": "evt-003", "title": "Q4 Planning Workshop",
        "description": "OKR setting, roadmap prioritization, and resource allocation for Q4.",
        "start_time": ts(1, 10, 0), "end_time": ts(1, 12, 0),
        "attendees": json.dumps(["Sarah Chen", "Marcus Webb", "Priya Kapoor", "James Liu (CFO)"]),
        "location": "HQ — War Room", "event_type": "planning",
    },
    {
        "id": "evt-004", "title": "1:1 — Sarah & Priya",
        "description": "Weekly product-engineering alignment sync.",
        "start_time": ts(1, 15, 0), "end_time": ts(1, 16, 0),
        "attendees": json.dumps(["Sarah Chen", "Priya Kapoor"]),
        "event_type": "1on1",
    },
    {
        "id": "evt-005", "title": "Security Review Board",
        "description": "Review API security audit findings with external consultant.",
        "start_time": ts(3, 11, 0), "end_time": ts(3, 12, 0),
        "attendees": json.dumps(["Marcus Webb", "Sarah Chen", "Alex Patel (SecurityCo)"]),
        "meeting_link": "https://zoom.us/j/987654321", "event_type": "review",
    },
    {
        "id": "evt-006", "title": "Weekly Team All-Hands",
        "description": "Company-wide weekly sync — wins, metrics, shoutouts.",
        "start_time": ts(4, 16, 0), "end_time": ts(4, 17, 0),
        "attendees": json.dumps(["Entire Company"]),
        "location": "HQ — Main Hall", "event_type": "allhands",
    },
]

NOTES = [
    {
        "id": "note-001",
        "title": "Series A Investor Talking Points",
        "content": """## Key Metrics to Highlight
- 340% MoM growth in active users
- 94% retention rate at 90 days
- NPS score: 72 (industry avg: 31)
- $180K ARR, growing 22% MoM

## NEXUS Demo Flow
1. Morning Brief workflow → all 4 agents activate simultaneously
2. Show real-time agent coordination panel
3. Mailgun sandbox email delivery (live logs)
4. Linear task creation via Atlas agent
5. Weekly report generation + send

## Investor Questions to Prepare For
- "How does this differ from LangChain agents?" → ADK native, A2A protocol, production-grade
- "What's the moat?" → Proprietary workflow orchestration + domain-specific fine-tuning roadmap
- "Revenue model?" → SaaS per-seat + workflow execution credits
""",
        "tags": json.dumps(["investors", "series-a", "demo"]),
        "category": "Strategy",
    },
    {
        "id": "note-002",
        "title": "NEXUS Architecture — Design Decisions",
        "content": """## Why Google ADK?
- Native Gemini integration with function calling
- Built-in tool registry and agent session management
- Production-grade vs research-grade (LangChain)

## A2A Protocol Benefits
- Standardized inter-agent communication
- Audit trail by default
- Retry logic and error propagation built-in

## MCP Tool Selection
- **Gmail via Composio**: Best-in-class OAuth handling
- **Mailgun**: Sandbox mode perfect for demo + production-ready
- **Linear**: Most developer-friendly PM tool API

## Database Design
- SQLite for portability (demo) → PostgreSQL for production
- All agent activities logged for explainability dashboard
""",
        "tags": json.dumps(["architecture", "technical", "adk"]),
        "category": "Technical",
    },
    {
        "id": "note-003",
        "title": "Weekly Metrics — Week 42",
        "content": """## Product Metrics
| Metric | This Week | Last Week | Δ |
|--------|-----------|-----------|---|
| DAU | 1,247 | 1,089 | +14.5% |
| Tasks Created | 8,932 | 7,441 | +20% |
| Workflows Run | 2,103 | 1,876 | +12.1% |
| Agent API Calls | 47,821 | 39,204 | +22% |

## Highlights
- NEXUS Morning Brief adopted by 89% of power users
- Mailgun integration delivered 2,847 automated reports
- Linear sync processed 1,203 task updates with zero failures

## Next Week Focus
- Launch Chronos calendar conflict detection
- A/B test new onboarding flow
- Prepare Series A materials
""",
        "tags": json.dumps(["metrics", "weekly", "product"]),
        "category": "Analytics",
    },
    {
        "id": "note-004",
        "title": "Alpha Platform — Sprint 12 Retrospective",
        "content": """## What went well ✅
- Payment integration shipped 2 days early
- CI/CD pipeline now under 4 min end-to-end
- Zero P0 incidents this sprint

## What needs improvement 🔧
- Test coverage dropped to 74% (target: 85%)
- Too many context switches for Sarah — need better async handoffs
- Documentation lag on new API endpoints

## Action Items
- [ ] Marcus: Bring test coverage back to 85% by EOW
- [ ] Sarah: Document 3 new endpoints in Notion
- [ ] Priya: Create ticket templates for better async handoffs

## Velocity
- Story points committed: 42
- Story points delivered: 39 (92.8% — above team average!)
""",
        "tags": json.dumps(["engineering", "sprint", "retro"]),
        "category": "Engineering",
    },
]

EMAILS = [
    {
        "id": "email-001",
        "subject": "Re: Series A Term Sheet — Follow-up Questions",
        "sender": "david.kim@sequoiacap.com",
        "recipients": json.dumps(["sarah@nexus.ai"]),
        "body_preview": "Hi Sarah, great call yesterday. We'd like to schedule a technical deep-dive with our engineering partner. Can you share the architecture docs and set up a 90-min session next week?",
        "status": "received", "is_important": True,
    },
    {
        "id": "email-002",
        "subject": "[NEXUS] Weekly Digest — Week 42 Summary",
        "sender": "nexus-agent@sandbox.mailgun.org",
        "recipients": json.dumps(["team@nexus.ai"]),
        "body_preview": "Your NEXUS weekly digest is ready. This week: 8,932 tasks processed, 2,103 workflows executed, 99.97% uptime. Top agent: Atlas with 23,421 actions.",
        "status": "sent", "mailgun_id": "mailgun-20241001-weekly",
        "is_important": False,
    },
    {
        "id": "email-003",
        "subject": "Linear — 3 tasks require your attention",
        "sender": "notifications@linear.app",
        "recipients": json.dumps(["sarah@nexus.ai"]),
        "body_preview": "ALPHA-42 is due in 2 days. ALPHA-50 is due today. FUND-12 is marked urgent by Priya.",
        "status": "received", "is_important": True,
    },
    {
        "id": "email-004",
        "subject": "Investor Demo Confirmed — Tomorrow 2PM",
        "sender": "lisa.park@a16z.com",
        "recipients": json.dumps(["sarah@nexus.ai", "marcus@nexus.ai"]),
        "body_preview": "Confirmed for tomorrow at 2PM PST. We'll have 3 partners joining. Please have the live demo ready — we'll want to see the multi-agent orchestration in real-time.",
        "status": "received", "is_important": True,
    },
]


async def seed_database():
    """Seed the database with demo data"""
    from database.db import init_db

    print("🌱 Initializing database schema...")
    await init_db()

    async with AsyncSessionLocal() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        count = await session.execute(select(func.count()).select_from(Task))
        if count.scalar() > 0:
            print("✅ Database already seeded — skipping")
            return

        print("🌱 Seeding tasks...")
        for task_data in TASKS:
            task = Task(**task_data)
            session.add(task)

        print("🌱 Seeding calendar events...")
        for event_data in EVENTS:
            event = ScheduleEvent(**event_data)
            session.add(event)

        print("🌱 Seeding notes...")
        for note_data in NOTES:
            note = Note(**note_data)
            session.add(note)

        print("🌱 Seeding email records...")
        for email_data in EMAILS:
            email = EmailRecord(**email_data)
            session.add(email)

        await session.commit()
        print("✅ Demo data seeded successfully!")
        print(f"   → {len(TASKS)} tasks | {len(EVENTS)} events | {len(NOTES)} notes | {len(EMAILS)} emails")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_database())
