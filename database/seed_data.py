"""
Seed data for the Multi-Agent Productivity Assistant demo.
Populates the database with realistic mock data around a 'Q2 Product Launch' scenario.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_database, get_connection


def seed_database():
    """Seed the database with impressive demo data."""
    init_database()
    conn = get_connection()
    cursor = conn.cursor()

    # Clear existing data
    for table in ["tasks", "events", "emails", "notes"]:
        cursor.execute(f"DELETE FROM {table}")

    # ─── TASKS ─────────────────────────────────────────────
    tasks = [
        ("Finalize Q2 Product Launch Deck", "Complete the investor-ready presentation with market analysis, product roadmap, and financial projections", "in_progress", "critical", "Sarah Chen", "Q2 Product Launch", "2026-04-15"),
        ("Review API Documentation", "Ensure all REST endpoints are documented with examples and error codes", "done", "high", "Mike Rivera", "Platform API", "2026-04-10"),
        ("Design Onboarding Flow", "Create user onboarding wireframes with 5-step progressive disclosure", "in_progress", "high", "Priya Sharma", "UX Redesign", "2026-04-12"),
        ("Set Up CI/CD Pipeline", "Configure GitHub Actions with automated testing, linting, and staging deployment", "done", "high", "Alex Kim", "Infrastructure", "2026-04-08"),
        ("Prepare Demo Environment", "Spin up sandbox with mock data for investor demo on April 20th", "todo", "critical", "Sarah Chen", "Q2 Product Launch", "2026-04-18"),
        ("Write Blog Post: AI Agents", "Draft thought-leadership article about multi-agent systems for company blog", "todo", "medium", "Jordan Lee", "Marketing", "2026-04-20"),
        ("Security Audit - Auth Module", "Penetration testing and code review for authentication and authorization flows", "in_progress", "critical", "Alex Kim", "Security", "2026-04-14"),
        ("Customer Feedback Analysis", "Analyze 500+ NPS responses and create actionable insights dashboard", "todo", "medium", "Priya Sharma", "Product Research", "2026-04-22"),
        ("Update Pricing Page", "Refresh pricing tiers with new enterprise plan and comparison table", "blocked", "high", "Jordan Lee", "Marketing", "2026-04-16"),
        ("Mobile App Performance Audit", "Profile and optimize React Native app - target <2s cold start time", "todo", "medium", "Mike Rivera", "Mobile App", "2026-04-25"),
        ("Integrate Analytics SDK", "Add Mixpanel tracking for key user events and funnel metrics", "in_progress", "medium", "Mike Rivera", "Platform API", "2026-04-13"),
        ("Quarterly OKR Review", "Compile OKR progress report for Q1 and set Q2 objectives", "done", "high", "Sarah Chen", "Operations", "2026-04-05"),
    ]
    cursor.executemany(
        "INSERT INTO tasks (title, description, status, priority, assignee, project, due_date) VALUES (?,?,?,?,?,?,?)",
        tasks
    )

    # ─── EVENTS ────────────────────────────────────────────
    events = [
        ("Daily Standup", "Quick sync on blockers and progress", "2026-04-09T09:00:00", "2026-04-09T09:15:00", "Virtual - Zoom", "Team", "standup"),
        ("Q2 Launch Strategy Meeting", "Review go-to-market strategy and timeline for product launch", "2026-04-09T10:00:00", "2026-04-09T11:30:00", "Conference Room A", "Sarah Chen, Mike Rivera, Priya Sharma, Jordan Lee", "meeting"),
        ("Design Review: Onboarding", "Review and iterate on onboarding flow wireframes", "2026-04-09T14:00:00", "2026-04-09T15:00:00", "Virtual - Figma", "Priya Sharma, Sarah Chen", "meeting"),
        ("Deep Work: API Documentation", "Focus time for completing API docs - no interruptions", "2026-04-09T15:30:00", "2026-04-09T17:30:00", "Remote", "Mike Rivera", "focus_time"),
        ("1:1 with CTO", "Weekly sync on technical roadmap and team capacity", "2026-04-10T10:00:00", "2026-04-10T10:45:00", "CTO Office", "Sarah Chen", "meeting"),
        ("Investor Demo Rehearsal", "Full run-through of product demo with Q&A prep", "2026-04-18T14:00:00", "2026-04-18T16:00:00", "Board Room", "All Hands", "meeting"),
        ("Sprint Retrospective", "Q1 Sprint 6 retro - what went well, improvements, action items", "2026-04-11T16:00:00", "2026-04-11T17:00:00", "Virtual - Zoom", "Engineering Team", "meeting"),
        ("Product Launch Day 🚀", "Official Q2 product launch - all hands on deck", "2026-04-20T09:00:00", "2026-04-20T18:00:00", "HQ + Virtual", "All Company", "deadline"),
    ]
    cursor.executemany(
        "INSERT INTO events (title, description, start_time, end_time, location, attendees, event_type) VALUES (?,?,?,?,?,?,?)",
        events
    )

    # ─── EMAILS ────────────────────────────────────────────
    emails = [
        ("Q2 Launch Deck - Draft v3 Ready for Review", "sarah@company.com", "team@company.com, cto@company.com",
         "Hi Team,\n\nI've uploaded the latest draft of the Q2 Launch Deck (v3) to the shared drive. Key updates:\n\n• Updated market size analysis with 2026 projections\n• Added competitive landscape slide\n• Included customer testimonials from beta program\n• Financial projections revised per CFO feedback\n\nPlease review by EOD Thursday. Looking forward to your feedback!\n\nBest,\nSarah",
         "sent", "thread_launch_001", "2026-04-08T14:30:00"),

        ("Re: API Rate Limiting Discussion", "mike@company.com", "alex@company.com, sarah@company.com",
         "Alex,\n\nGood catch on the rate limiting. I've implemented the token bucket algorithm with these defaults:\n\n• 100 requests/minute for free tier\n• 1000 requests/minute for pro tier\n• 10000 requests/minute for enterprise\n\nAlso added Redis-backed distributed rate limiting for the cluster. PR is up: #472\n\nMike",
         "sent", "thread_api_002", "2026-04-08T16:15:00"),

        ("Investor Meeting Confirmation - April 20", "partnerships@vcfirm.com", "sarah@company.com, ceo@company.com",
         "Dear Sarah,\n\nThis confirms our partners' attendance at your product demo on April 20th at 2:00 PM PST.\n\nAttending from our side:\n• John Park (Managing Partner)\n• Lisa Wong (Principal)\n• David Chen (Associate)\n\nWe're excited to see the multi-agent platform in action. Please share any pre-read materials at your convenience.\n\nBest regards,\nVC Firm Partnerships Team",
         "received", "thread_investor_003", "2026-04-07T10:00:00"),

        ("Security Audit Findings - Preliminary Report", "alex@company.com", "sarah@company.com, cto@company.com",
         "Team,\n\nPreliminary findings from the auth module security audit:\n\n✅ PASSED: JWT token rotation\n✅ PASSED: CORS policy configuration\n✅ PASSED: SQL injection prevention\n⚠️ REVIEW: Session timeout set to 24h (recommend 4h)\n⚠️ REVIEW: Missing rate limiting on /auth/reset-password\n\nFull report with remediation recommendations coming Friday.\n\nAlex",
         "received", "thread_security_004", "2026-04-08T11:00:00"),

        ("Welcome to the Beta Program! 🎉", "sarah@company.com", "beta-users@company.com",
         "Dear Beta Users,\n\nThank you for joining our Multi-Agent Productivity Platform beta! Here's what you need to know:\n\n📋 Getting Started Guide: docs.company.com/beta\n💬 Feedback Channel: #beta-feedback on Slack\n🐛 Bug Reports: beta-bugs@company.com\n📅 Beta Period: April 8 - May 8, 2026\n\nYour feedback is invaluable in shaping the future of productivity. Happy exploring!\n\nBest,\nThe Product Team",
         "sent", "thread_beta_005", "2026-04-08T09:00:00"),
    ]
    cursor.executemany(
        "INSERT INTO emails (subject, sender, recipients, body, status, thread_id, sent_at) VALUES (?,?,?,?,?,?,?)",
        emails
    )

    # ─── NOTES ─────────────────────────────────────────────
    notes = [
        ("Q2 Launch Checklist", "## Pre-Launch (April 8-19)\n- [x] Finalize product positioning\n- [x] Complete API documentation\n- [ ] Security audit sign-off\n- [ ] Performance benchmarks\n- [ ] Demo environment ready\n\n## Launch Day (April 20)\n- [ ] Press release goes live 9 AM\n- [ ] Product Hunt submission\n- [ ] Social media campaign\n- [ ] Investor demo at 2 PM\n- [ ] Team celebration 🎉",
         "launch,q2,checklist", "project"),

        ("Multi-Agent Architecture Decision", "## Decision: Hub-and-Spoke Agent Topology\n\n**Context:** Need to decide agent coordination pattern for v2.\n\n**Decision:** Adopted hub-and-spoke with a root orchestrator agent routing to specialized sub-agents.\n\n**Rationale:**\n- Better separation of concerns\n- Easier to add new agent capabilities\n- Cleaner error handling and fallback\n- Supports A2A protocol for future cross-org agent communication\n\n**Sub-agents:**\n1. Task Manager Agent\n2. Calendar Agent\n3. Email Agent\n4. Notes & Knowledge Agent",
         "architecture,agents,decision", "technical"),

        ("Customer Feedback Highlights - March", "## Top Requests\n1. **Natural language task creation** (78% of users)\n2. **Calendar conflict detection** (65%)\n3. **Email summarization** (52%)\n4. **Cross-app workflow automation** (48%)\n\n## Satisfaction Scores\n- Overall NPS: 72 (+8 from Feb)\n- Task Management: 4.5/5\n- Email Integration: 3.8/5\n- Mobile Experience: 3.2/5\n\n## Key Quote\n> \"This is the first AI tool that actually understands my workflow rather than just being another chatbot.\" — Enterprise Beta User",
         "feedback,customers,nps", "research"),

        ("Sprint 6 Retro Notes", "## What Went Well 🎯\n- API response times down 40% after Redis caching\n- Zero critical bugs in production this sprint\n- Successfully onboarded 50 new beta users\n\n## Improvements Needed 🔧\n- Need better error messages for API consumers\n- CI pipeline takes 12 min - target <5 min\n- More thorough code reviews before merge\n\n## Action Items\n- [ ] @mike: Add structured error response format\n- [ ] @alex: Parallelize CI test suites\n- [ ] @all: Min 2 reviewers per PR",
         "sprint,retro,team", "meetings"),

        ("Competitive Analysis Summary", "## Key Competitors\n\n| Feature | Us | Competitor A | Competitor B |\n|---------|-----|-------------|-------------|\n| Multi-Agent | ✅ | ❌ | Partial |\n| A2A Protocol | ✅ | ❌ | ❌ |\n| MCP Tools | ✅ | ✅ | ❌ |\n| Custom Workflows | ✅ | Partial | ✅ |\n| On-Premise | Planned | ✅ | ❌ |\n\n## Our Differentiator\nOnly platform with true multi-agent coordination using A2A protocol + MCP tool integration. This enables cross-organizational agent communication that no competitor offers.",
         "competitive,analysis,market", "research"),

        ("Meeting Notes: CTO Sync April 7", "## Key Decisions\n1. **Go with Gemini 2.0 Flash** for all agent models (cost/performance balance)\n2. **SQLite for v1**, migrate to PostgreSQL for v2 production\n3. **A2A protocol** approved for inter-agent communication standard\n\n## Technical Direction\n- FastAPI for serving the agent system as API\n- Custom web UI for demo (not adk web - need premium look)\n- Focus on task management + calendar as primary demo workflows\n\n## Timeline\n- April 18: Demo rehearsal\n- April 20: Investor demo\n- May 1: Public beta launch",
         "meeting,cto,decisions", "meetings"),
    ]
    cursor.executemany(
        "INSERT INTO notes (title, content, tags, category) VALUES (?,?,?,?)",
        notes
    )

    conn.commit()
    conn.close()
    print("✅ Database seeded with demo data successfully!")
    print(f"   📋 {len(tasks)} tasks")
    print(f"   📅 {len(events)} events")
    print(f"   📧 {len(emails)} emails")
    print(f"   📝 {len(notes)} notes")


if __name__ == "__main__":
    seed_database()
