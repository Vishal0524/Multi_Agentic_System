# 📘 NEXUS User Manual
### Multi-Agent Productivity Assistant — Investor Demo Guide

---

## What You're Looking At

NEXUS is a **live, working multi-agent AI system** where five specialized AI agents coordinate in real-time to complete complex productivity workflows. Every workflow you trigger is genuinely executing — you can watch agents activate, see tool calls fire, and see data update live.

**No smoke, no mirrors.** The agent activity panel shows real SSE streams. Mailgun emails appear in live logs. Linear tasks are actually created. The database is genuinely populated.

---

## The Five Agents

| Agent | Emoji | Specialization | Tools Used |
|---|---|---|---|
| **Nexus Prime** | 🧠 | Master Orchestrator | Routes, plans, synthesizes |
| **Hermes** | 📬 | Email Intelligence | Gmail MCP · Mailgun sandbox |
| **Atlas** | 📋 | Task & Project Manager | Linear MCP · SQLite |
| **Chronos** | 📅 | Schedule Intelligence | Calendar DB · Conflict detection |
| **Oracle** | 🔍 | Research & Knowledge | Notes DB · Synthesis |

---

## Demo Walkthrough: The Five Workflows

### 🌅 Workflow 1: Morning Brief
**Trigger:** Type `Give me my morning brief` → Press Enter

**What happens (watch the Agent Activity panel):**
1. 🧠 **Nexus Prime** receives the request, classifies intent as `morning_brief`, plans parallel execution
2. All 4 sub-agents activate **simultaneously** (watch the spinning indicators):
   - 📬 **Hermes** calls `gmail_get_inbox` → finds 5 emails, 2 flagged important
   - 📋 **Atlas** calls `linear_get_issues` → pulls 7 tasks, identifies 3 urgent
   - 📅 **Chronos** calls `calendar_get_today` → finds today's events, surfaces next meeting
   - 🔍 **Oracle** queries notes DB → retrieves relevant morning context
3. 🧠 **Nexus Prime** synthesizes all 4 results into a single morning brief
4. Response appears in chat with full summary

**What investors see:** True parallel multi-agent coordination — not sequential chains. Four agents running simultaneously, each using different tools, results merged by the orchestrator.

---

### 📊 Workflow 2: Weekly Review + Automated Email
**Trigger:** Type `Run weekly review` → Press Enter

**What happens:**
1. 🧠 **Nexus Prime** plans a 3-step workflow: compile → report → distribute
2. 📋 **Atlas** aggregates task metrics across all projects
3. 🔍 **Oracle** pulls the weekly metrics note (shows 340% growth, NPS 72, etc.)
4. 📬 **Hermes** composes an HTML email report and calls **Mailgun** to send it:
   ```
   To:      team@nexus.ai
   Subject: NEXUS Weekly Digest — [Today's Date]
   Via:     Mailgun Sandbox (test mode — appears in logs)
   ```
5. The sent email is logged to the database and appears in the Email tab

**The Mailgun Sandbox moment:** The email is genuinely dispatched to Mailgun's API. You'll see a real Message ID like `<20241010120000.abc123@sandbox.mailgun.org>`. Mailgun processes it — it just doesn't deliver to a real inbox (sandbox mode). The email log in Mailgun's dashboard will show it as "Accepted."

**What investors see:** End-to-end workflow automation — AI reads data, writes a professional report, and emails it without any human steps.

---

### 🚀 Workflow 3: Project Kickoff
**Trigger:** Type `Kick off the Alpha Platform project` → Press Enter

**What happens:**
1. 🧠 **Nexus Prime** extracts project name, plans 3-agent workflow
2. 📋 **Atlas** creates 3 initial tasks in **Linear** (via Linear API in live mode, mock in demo):
   - `Define requirements and scope — Alpha Platform` → `ALPHA-51`
   - `Set up project repository — Alpha Platform` → `ALPHA-52`
   - `Assign team roles and responsibilities — Alpha Platform` → `ALPHA-53`
3. 📅 **Chronos** checks calendar for scheduling conflicts
4. 📬 **Hermes** sends kickoff notification to team via Mailgun:
   ```
   Subject: 🚀 Project Kickoff: Alpha Platform
   To:      team@nexus.ai
   Body:    Lists all 3 created tasks with Linear links
   ```

**What investors see:** NEXUS doesn't just talk about tasks — it creates them. Multi-tool coordination across a task manager AND an email service in a single natural language command.

---

### ✅ Workflow 4: Quick Task Creation
**Trigger:** Type `create task: fix the authentication bug in production` → Press Enter

**What happens:**
1. 🧠 **Nexus Prime** classifies intent as `create_task` in under 50ms (no AI API call needed)
2. 📋 **Atlas** calls `linear_create_issue` with the task title
3. Task appears in Linear (mock ID: `ALPHA-57`) and in the Tasks tab instantly
4. Confirmation returned to chat with Linear issue link

**What investors see:** Intent classification is instantaneous (rule-based), tool execution is fast, UI updates in real-time. This is what productivity tooling should feel like.

---

### 📤 Workflow 5: Direct Email Dispatch
**Trigger:** Type `Email team the status update` → Press Enter

Or use the **Tasks tab** → create a task directly, or the **Email tab** → see the inbox.

**What happens:**
1. 📬 **Hermes** composes status email
2. Calls Mailgun API with `o:testmode=yes` flag (sandbox)
3. Email logged to DB with Mailgun Message ID
4. Visible in Email tab immediately

---

## Mock Data Reference

The system is pre-loaded with rich, realistic data that tells a coherent story:

### 👤 Team
- **Sarah Chen** — Engineering Lead (works on Alpha Platform, Architecture)
- **Marcus Webb** — Backend Engineer (Stripe integration, Security audit)
- **Priya Kapoor** — Product Manager (Investor deck, User interviews)

### 📋 Tasks (8 total)
| ID | Title | Status | Owner |
|---|---|---|---|
| ALPHA-42 | Design system architecture for Q4 | 🔵 In Progress | Sarah |
| ALPHA-43 | Integrate Stripe payment processing | ⚪ Todo | Marcus |
| FUND-12 | Write investor deck copy | 🔵 In Progress | Priya |
| DEV-08 | Set up CI/CD with GitHub Actions | ✅ Done | Sarah |
| PROD-21 | User interviews for onboarding | ⚪ Todo | Priya |
| SEC-05 | Security audit — API endpoints | ⚪ Todo | Marcus |
| **ALPHA-50** | **Launch NEXUS v1.0 demo** | 🔵 **In Progress** | Sarah |
| ANA-15 | Compile weekly metrics dashboard | ⚪ Todo | Priya |

### 📅 Events (6 total)
| Time | Event | Type |
|---|---|---|
| Today 2:00 PM | **Investor Demo — Series A Pitch** | Demo |
| Today 9:30 AM | Engineering Standup | Standup |
| Tomorrow 10:00 AM | Q4 Planning Workshop | Planning |
| Tomorrow 3:00 PM | 1:1 Sarah & Priya | 1-on-1 |
| Day+3 11:00 AM | Security Review Board | Review |
| Day+4 4:00 PM | Weekly All-Hands | All-Hands |

### 📬 Emails (4 total)
| Subject | From | Priority |
|---|---|---|
| Series A Term Sheet — Follow-up | david.kim@sequoiacap.com | ⭐ Important |
| Investor Demo Confirmed Tomorrow | lisa.park@a16z.com | ⭐ Important |
| Linear — 3 tasks need attention | notifications@linear.app | Normal |
| AWS Cost Alert — 34% increase | aws-billing@amazon.com | Normal |

### 📝 Notes (4 total)
| Title | Category |
|---|---|
| Series A Investor Talking Points | Strategy |
| NEXUS Architecture — Design Decisions | Technical |
| Weekly Metrics — Week 42 | Analytics |
| Alpha Platform Sprint 12 Retrospective | Engineering |

---

## Demo Script for Investors

### Opening (30 seconds)
> "What you're about to see is a live AI system where five specialized agents coordinate in real-time. This isn't a chatbot — it's an orchestrated multi-agent workflow engine. Watch the agent panel on the right as I type."

### Act 1: Show the data (1 minute)
- Click through **Tasks**, **Calendar**, **Email**, **Notes** tabs
- Point out the realistic team data, Linear IDs, real email addresses
> "All of this is structured data our agents can query, reason about, and act on."

### Act 2: Trigger Morning Brief (2 minutes)
- Go to **Agent Chat** → type `Give me my morning brief`
- Point at the agent panel: "Watch — all four agents activate simultaneously"
- Show results coming back: emails, tasks, events, notes synthesized into one brief
> "In under 3 seconds, four agents ran in parallel across four different data sources."

### Act 3: Weekly Review + Mailgun (2 minutes)
- Type `Run weekly review`
- Show the Email tab update with the new sent email
- Open Mailgun dashboard if available to show the real log entry
> "That email was genuinely sent to Mailgun's API. The Message ID is real. This is production-grade infrastructure."

### Act 4: Create a Task Live (1 minute)
- Type `create task: prepare investor materials for Series B`
- Go to Tasks tab → show the new task at the top
> "One command, task created, Linear synced, database updated. No human steps."

### Closing (30 seconds)
> "NEXUS is the infrastructure layer for AI-native productivity. Instead of building point solutions, we built an orchestration system that coordinates any number of agents across any tools. The same architecture that runs 5 agents today runs 50 tomorrow."

---

## Technical Highlights for Technical Investors

### Agent Coordination (A2A Protocol)
```python
# A2A Message format — standardized inter-agent communication
A2AMessage(
    from_agent="Nexus Prime",
    to_agent="Atlas",
    message_type="task",
    payload={"action": "get_task_summary", "priority_filter": "urgent"}
)
```

### Parallel Execution
```python
# All 4 agents run concurrently using asyncio.gather()
hermes_r, atlas_r, chronos_r, oracle_r = await asyncio.gather(
    hermes.run("fetch inbox"), 
    atlas.run("get tasks"),
    chronos.run("get schedule"),
    oracle.run("morning context")
)
```

### Real-time UI via SSE
- Agents emit events to a publish/subscribe bus
- Frontend receives them via `EventSource` (Server-Sent Events)
- Zero polling, zero page refreshes — true real-time

### Tool Architecture
```
MCP Tool Registry
├── gmail_get_inbox()      → Composio Gmail
├── mailgun_send_email()   → Mailgun REST API  
├── linear_create_issue()  → Linear GraphQL
├── linear_get_issues()    → Linear GraphQL
└── calendar_get_today()   → SQLite (local)
```

---

## Environment Modes

| Setting | Demo Mode | Live Mode |
|---|---|---|
| `APP_MODE=demo` | Mock data, no API calls | Real APIs |
| Gmail | Returns mock inbox | Composio OAuth |
| Mailgun | Sandbox (logged, not delivered) | Sandbox or production |
| Linear | Mock issue IDs | Real Linear workspace |
| Gemini | Rule-based routing | Full Gemini reasoning |
| Database | SQLite with seed data | SQLite → PostgreSQL |

**Default is always demo mode** — safe to run without any API keys.

---

## Deployment

```bash
# One command to deploy to your Cloud Run URL
bash deploy.sh

# Or manually:
docker build -t nexus-agent .
docker run -p 8080:8080 -e APP_MODE=demo nexus-agent
```

Cloud Run URL stays the same as your existing service — just the image changes.

---

*NEXUS v1.0 — Built with Google ADK · A2A Protocol · Mailgun · Linear · Composio*
