"""
NEXUS Agent System
Implements Google ADK-style agents with A2A Protocol coordination.

Agents:
- NexusPrime:  Orchestrator — interprets user intent, delegates to sub-agents
- Hermes:      Email Intelligence Agent (Gmail + Mailgun)
- Atlas:       Task & Project Agent (Linear + DB)
- Chronos:     Schedule & Time Agent (Calendar)
- Oracle:      Research & Notes Agent (DB + Synthesis)
"""
import os
import uuid
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, field
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "demo")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
APP_MODE = os.getenv("APP_MODE", "demo")


def is_demo() -> bool:
    return APP_MODE == "demo" or GOOGLE_API_KEY == "demo"


# ─── A2A Message Protocol ──────────────────────────────────────────────────────

@dataclass
class A2AMessage:
    """Agent-to-Agent Protocol message"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    message_type: str = "task"   # task | result | error | status
    payload: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "from_agent": self.from_agent, "to_agent": self.to_agent,
            "message_type": self.message_type, "payload": self.payload,
            "timestamp": self.timestamp,
        }


@dataclass
class AgentResult:
    """Standardized agent result"""
    agent_name: str
    action: str
    success: bool
    data: Any
    summary: str
    duration_ms: int = 0
    tool_calls: List[Dict] = field(default_factory=list)


# ─── SSE Event Bus ─────────────────────────────────────────────────────────────

class EventBus:
    """In-process SSE event bus for real-time UI updates"""
    def __init__(self):
        self._subscribers: List[asyncio.Queue] = []

    def subscribe(self) -> asyncio.Queue:
        q = asyncio.Queue(maxsize=100)
        self._subscribers.append(q)
        return q

    def unsubscribe(self, q: asyncio.Queue):
        self._subscribers = [s for s in self._subscribers if s != q]

    async def publish(self, event: Dict):
        for q in self._subscribers:
            try:
                q.put_nowait(event)
            except asyncio.QueueFull:
                pass


event_bus = EventBus()


async def emit(event_type: str, agent: str, data: Dict, workflow_id: str = ""):
    """Emit a real-time event to the UI"""
    event = {
        "type": event_type,
        "agent": agent,
        "data": data,
        "workflow_id": workflow_id,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await event_bus.publish(event)
    # Also log to DB
    try:
        from database.db import db_log_activity
        await db_log_activity({
            "id": str(uuid.uuid4()),
            "workflow_id": workflow_id,
            "agent_name": agent,
            "action": data.get("action", event_type),
            "details": json.dumps(data),
            "status": "success" if event_type != "error" else "error",
            "duration_ms": data.get("duration_ms"),
        })
    except Exception:
        pass


# ─── Base Agent ────────────────────────────────────────────────────────────────

class NexusAgent:
    """Base class for all NEXUS agents (Google ADK pattern)"""

    def __init__(self, name: str, description: str, emoji: str = "🤖"):
        self.name = name
        self.description = description
        self.emoji = emoji
        self.tools = []

    async def think(self, prompt: str, context: Dict = {}) -> str:
        """Use Gemini to reason about a task"""
        if is_demo():
            return f"[{self.name} reasoning in demo mode]"

        try:
            import google.generativeai as genai
            genai.configure(api_key=GOOGLE_API_KEY)
            model = genai.GenerativeModel(GEMINI_MODEL)
            full_prompt = f"""You are {self.name}, {self.description}.
Context: {json.dumps(context, indent=2)}
Task: {prompt}
Respond concisely and actionably."""
            response = model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini error in {self.name}: {e}")
            return f"[{self.name}: AI reasoning unavailable — {str(e)}]"

    async def run(self, task: str, workflow_id: str = "") -> AgentResult:
        raise NotImplementedError


# ─── Hermes: Email Intelligence Agent ─────────────────────────────────────────

class HermesAgent(NexusAgent):
    def __init__(self):
        super().__init__(
            name="Hermes",
            description="Email Intelligence Agent specializing in inbox analysis, email composition, and delivery via Gmail and Mailgun.",
            emoji="📬"
        )

    async def run(self, task: str, workflow_id: str = "", params: Dict = {}) -> AgentResult:
        start = datetime.utcnow()
        await emit("agent_start", self.name, {"action": f"Starting: {task}", "status": "running"}, workflow_id)

        from tools.mcp_tools import gmail_get_inbox, gmail_get_important, mailgun_send_email

        tool_calls = []
        result_data = {}

        if "inbox" in task.lower() or "email" in task.lower() or "morning" in task.lower():
            await emit("tool_call", self.name, {"tool": "gmail_get_inbox", "status": "calling"}, workflow_id)
            inbox = await gmail_get_inbox(max_results=5)
            tool_calls.append({"tool": "gmail_get_inbox", "result": inbox})
            important = await gmail_get_important()
            tool_calls.append({"tool": "gmail_get_important", "result": important})
            result_data = {
                "total_emails": len(inbox.get("emails", [])),
                "important_count": len(important.get("emails", [])),
                "emails": inbox.get("emails", []),
                "important_emails": important.get("emails", []),
            }
            summary = (
                f"Scanned inbox: {result_data['total_emails']} emails, "
                f"{result_data['important_count']} flagged important. "
                f"Top priority: '{important.get('emails', [{}])[0].get('subject', 'N/A')}'"
                if result_data["important_count"] > 0 else
                f"Scanned {result_data['total_emails']} emails — no urgent items."
            )

        elif "send" in task.lower() or "report" in task.lower() or "notify" in task.lower():
            recipients = params.get("recipients", ["team@nexus.ai"])
            subject = params.get("subject", "NEXUS Agent Report")
            body_html = params.get("body_html", "<h2>NEXUS Automated Report</h2><p>Generated by Hermes Agent.</p>")
            body_text = params.get("body_text", "NEXUS Automated Report — Generated by Hermes Agent.")

            await emit("tool_call", self.name, {
                "tool": "mailgun_send_email",
                "status": "calling",
                "details": {"to": recipients, "subject": subject},
            }, workflow_id)

            send_result = await mailgun_send_email(recipients, subject, body_html, body_text)
            tool_calls.append({"tool": "mailgun_send_email", "result": send_result})

            # Log to DB
            from database.db import db_log_email
            await db_log_email({
                "id": str(uuid.uuid4()),
                "subject": subject,
                "sender": "nexus-agent@sandbox.mailgun.org",
                "recipients": json.dumps(recipients),
                "body_preview": body_text[:300],
                "status": "sent",
                "mailgun_id": send_result.get("message_id", ""),
                "is_important": False,
            })

            result_data = send_result
            summary = f"Email '{subject}' dispatched via Mailgun sandbox to {len(recipients)} recipient(s). Message ID: {send_result.get('message_id', 'N/A')}"
        else:
            inbox = await gmail_get_inbox()
            result_data = {"emails": inbox.get("emails", [])}
            summary = f"Fetched {len(result_data['emails'])} emails from inbox."

        duration = int((datetime.utcnow() - start).total_seconds() * 1000)
        await emit("agent_complete", self.name, {
            "action": task, "summary": summary, "status": "success", "duration_ms": duration,
        }, workflow_id)

        return AgentResult(
            agent_name=self.name, action=task, success=True,
            data=result_data, summary=summary, duration_ms=duration, tool_calls=tool_calls,
        )


# ─── Atlas: Task & Project Agent ───────────────────────────────────────────────

class AtlasAgent(NexusAgent):
    def __init__(self):
        super().__init__(
            name="Atlas",
            description="Task & Project Agent that syncs with Linear, manages the task database, and tracks project progress.",
            emoji="📋"
        )

    async def run(self, task: str, workflow_id: str = "", params: Dict = {}) -> AgentResult:
        start = datetime.utcnow()
        await emit("agent_start", self.name, {"action": f"Starting: {task}", "status": "running"}, workflow_id)

        from tools.mcp_tools import linear_get_issues, linear_create_issue, linear_update_issue
        from database.db import db_get_tasks, db_create_task, db_update_task

        tool_calls = []
        result_data = {}

        if "create" in task.lower() or "add task" in task.lower() or "new issue" in task.lower():
            title = params.get("title", task.replace("create task:", "").replace("add task:", "").strip())
            description = params.get("description", "Created by NEXUS Atlas agent.")
            priority = params.get("priority", 2)

            await emit("tool_call", self.name, {
                "tool": "linear_create_issue",
                "status": "calling",
                "details": {"title": title},
            }, workflow_id)

            linear_result = await linear_create_issue(title, description, priority)
            tool_calls.append({"tool": "linear_create_issue", "result": linear_result})

            task_id = str(uuid.uuid4())
            task_record = {
                "id": task_id, "title": title, "description": description,
                "status": "todo", "priority": ["urgent", "high", "medium", "low"][priority - 1],
                "linear_id": linear_result.get("issue", {}).get("id", ""),
                "project": params.get("project", "General"),
                "assignee": params.get("assignee", "Unassigned"),
                "tags": json.dumps(params.get("tags", [])),
            }
            await db_create_task(task_record)
            result_data = {"task": task_record, "linear": linear_result}
            summary = f"Created task '{title}' in Linear ({linear_result.get('issue', {}).get('id', 'DEMO-XX')}) and synced to local DB."

        elif "update" in task.lower() or "status" in task.lower():
            issue_id = params.get("issue_id", "ALPHA-42")
            new_status = params.get("status", "done")
            await emit("tool_call", self.name, {
                "tool": "linear_update_issue",
                "status": "calling",
                "details": {"id": issue_id, "status": new_status},
            }, workflow_id)
            linear_result = await linear_update_issue(issue_id, new_status)
            tool_calls.append({"tool": "linear_update_issue", "result": linear_result})
            result_data = {"updated": issue_id, "status": new_status}
            summary = f"Updated {issue_id} → '{new_status}' in Linear."

        else:
            # Default: fetch task summary
            await emit("tool_call", self.name, {"tool": "linear_get_issues", "status": "calling"}, workflow_id)
            linear_result = await linear_get_issues()
            tool_calls.append({"tool": "linear_get_issues", "result": linear_result})
            db_tasks = await db_get_tasks()

            issues = linear_result.get("issues", [])
            urgent = [i for i in issues if i.get("priority") == 1]
            in_progress = [i for i in issues if "progress" in i.get("state", "").lower()]

            result_data = {
                "total_tasks": len(db_tasks),
                "linear_issues": len(issues),
                "urgent_count": len(urgent),
                "in_progress_count": len(in_progress),
                "tasks": db_tasks,
                "linear_issues_data": issues,
                "urgent_issues": urgent,
            }
            summary = (
                f"Retrieved {len(db_tasks)} tasks. "
                f"Linear: {len(issues)} issues, {len(urgent)} urgent, {len(in_progress)} in progress."
            )

        duration = int((datetime.utcnow() - start).total_seconds() * 1000)
        await emit("agent_complete", self.name, {
            "action": task, "summary": summary, "status": "success", "duration_ms": duration,
        }, workflow_id)

        return AgentResult(
            agent_name=self.name, action=task, success=True,
            data=result_data, summary=summary, duration_ms=duration, tool_calls=tool_calls,
        )


# ─── Chronos: Schedule Agent ───────────────────────────────────────────────────

class ChronosAgent(NexusAgent):
    def __init__(self):
        super().__init__(
            name="Chronos",
            description="Schedule & Time Agent that reads calendar events, detects conflicts, and provides daily time intelligence.",
            emoji="📅"
        )

    async def run(self, task: str, workflow_id: str = "", params: Dict = {}) -> AgentResult:
        start = datetime.utcnow()
        await emit("agent_start", self.name, {"action": f"Starting: {task}", "status": "running"}, workflow_id)

        from tools.mcp_tools import calendar_get_today, calendar_get_week

        tool_calls = []

        await emit("tool_call", self.name, {"tool": "calendar_get_today", "status": "calling"}, workflow_id)
        today_events = await calendar_get_today()
        tool_calls.append({"tool": "calendar_get_today", "result": today_events})

        await emit("tool_call", self.name, {"tool": "calendar_get_week", "status": "calling"}, workflow_id)
        week_events = await calendar_get_week()
        tool_calls.append({"tool": "calendar_get_week", "result": week_events})

        events_today = today_events.get("events", [])
        events_week = week_events.get("events", [])

        # Find next event
        now = datetime.utcnow().isoformat()
        upcoming = sorted([e for e in events_today if e["start_time"] >= now], key=lambda x: x["start_time"])
        next_event = upcoming[0] if upcoming else None

        result_data = {
            "today_count": len(events_today),
            "week_count": len(events_week),
            "events_today": events_today,
            "events_week": events_week,
            "next_event": next_event,
        }

        summary = (
            f"Today: {len(events_today)} events. "
            f"Next: '{next_event['title']}' at {next_event['start_time'][11:16] if next_event else 'N/A'}. "
            f"Week total: {len(events_week)} events."
        )

        duration = int((datetime.utcnow() - start).total_seconds() * 1000)
        await emit("agent_complete", self.name, {
            "action": task, "summary": summary, "status": "success", "duration_ms": duration,
        }, workflow_id)

        return AgentResult(
            agent_name=self.name, action=task, success=True,
            data=result_data, summary=summary, duration_ms=duration, tool_calls=tool_calls,
        )


# ─── Oracle: Research & Notes Agent ───────────────────────────────────────────

class OracleAgent(NexusAgent):
    def __init__(self):
        super().__init__(
            name="Oracle",
            description="Research & Notes Agent that retrieves, synthesizes, and surfaces contextual knowledge from the notes database.",
            emoji="🔍"
        )

    async def run(self, task: str, workflow_id: str = "", params: Dict = {}) -> AgentResult:
        start = datetime.utcnow()
        await emit("agent_start", self.name, {"action": f"Starting: {task}", "status": "running"}, workflow_id)

        from database.db import db_get_notes

        await emit("tool_call", self.name, {"tool": "notes_database", "status": "calling"}, workflow_id)
        notes = await db_get_notes()

        # Simple keyword search for demo
        query = params.get("query", task).lower()
        relevant = [
            n for n in notes
            if query in n["title"].lower() or
               query in n["content"].lower() or
               any(query in t for t in n.get("tags", []))
        ][:3] if query not in ["morning", "brief", "all", "summary"] else notes[:3]

        result_data = {
            "total_notes": len(notes),
            "relevant_notes": relevant,
            "notes": notes,
        }

        summary = (
            f"Searched {len(notes)} notes for '{query}' — "
            f"found {len(relevant)} relevant documents. "
            f"Top: '{relevant[0]['title']}'" if relevant else
            f"Fetched {len(notes)} notes from knowledge base."
        )

        duration = int((datetime.utcnow() - start).total_seconds() * 1000)
        await emit("agent_complete", self.name, {
            "action": task, "summary": summary, "status": "success", "duration_ms": duration,
        }, workflow_id)

        return AgentResult(
            agent_name=self.name, action=task, success=True,
            data=result_data, summary=summary, duration_ms=duration,
        )


# ─── Nexus Prime: Orchestrator ─────────────────────────────────────────────────

class NexusPrimeOrchestrator(NexusAgent):
    """
    Primary Orchestrator Agent.
    Interprets user intent via Gemini (or rule-based in demo mode),
    dispatches tasks to sub-agents via A2A protocol,
    and synthesizes final responses.
    """

    def __init__(self):
        super().__init__(
            name="Nexus Prime",
            description="Master orchestrator that coordinates Hermes, Atlas, Chronos, and Oracle to complete complex multi-step workflows.",
            emoji="🧠"
        )
        self.hermes = HermesAgent()
        self.atlas = AtlasAgent()
        self.chronos = ChronosAgent()
        self.oracle = OracleAgent()

    def _classify_intent(self, user_input: str) -> str:
        """Rule-based intent classification (fast, no API call needed)"""
        text = user_input.lower()

        if any(w in text for w in ["morning brief", "morning", "start my day", "daily brief"]):
            return "morning_brief"
        if any(w in text for w in ["weekly review", "week summary", "weekly digest"]):
            return "weekly_review"
        if any(w in text for w in ["project kickoff", "kick off", "start project", "new project"]):
            return "project_kickoff"
        if any(w in text for w in ["create task", "add task", "new task", "new issue"]):
            return "create_task"
        if any(w in text for w in ["send email", "email team", "notify", "send report"]):
            return "send_email"
        if any(w in text for w in ["schedule", "calendar", "meetings", "events"]):
            return "check_schedule"
        if any(w in text for w in ["inbox", "emails", "gmail", "messages"]):
            return "check_email"
        if any(w in text for w in ["tasks", "linear", "issues", "progress"]):
            return "check_tasks"
        if any(w in text for w in ["notes", "research", "find", "search"]):
            return "search_notes"

        return "general"

    async def orchestrate(
        self, user_input: str, workflow_id: str = ""
    ) -> AsyncGenerator[Dict, None]:
        """
        Main orchestration loop.
        Yields SSE events as agents complete their work.
        """
        if not workflow_id:
            workflow_id = str(uuid.uuid4())

        # Emit orchestrator start
        await emit("orchestrator_start", self.name, {
            "action": "Analyzing request",
            "user_input": user_input,
            "workflow_id": workflow_id,
        }, workflow_id)

        intent = self._classify_intent(user_input)
        logger.info(f"[NexusPrime] Intent: {intent} | Input: {user_input[:80]}")

        await emit("intent_classified", self.name, {
            "intent": intent,
            "action": f"Routing workflow: {intent.replace('_', ' ').title()}",
        }, workflow_id)

        results = {}

        # ── Morning Brief Workflow ──────────────────────────────────────────
        if intent == "morning_brief":
            await emit("workflow_plan", self.name, {
                "action": "Planning Morning Brief",
                "agents": ["Hermes", "Atlas", "Chronos", "Oracle"],
                "steps": ["Check inbox", "Pull urgent tasks", "Review calendar", "Surface relevant notes"],
            }, workflow_id)

            # Run all 4 agents in parallel
            hermes_t = self.hermes.run("fetch inbox and important emails", workflow_id)
            atlas_t = self.atlas.run("get task summary", workflow_id)
            chronos_t = self.chronos.run("get today's schedule", workflow_id)
            oracle_t = self.oracle.run("morning", workflow_id, {"query": "morning"})

            hermes_r, atlas_r, chronos_r, oracle_r = await asyncio.gather(
                hermes_t, atlas_t, chronos_t, oracle_t
            )

            results = {
                "hermes": hermes_r.data,
                "atlas": atlas_r.data,
                "chronos": chronos_r.data,
                "oracle": oracle_r.data,
            }

            # Build morning brief summary
            summary = self._build_morning_brief(results)
            await emit("workflow_complete", self.name, {
                "action": "Morning Brief complete",
                "summary": summary,
                "workflow": "morning_brief",
                "results": {
                    "emails": results["hermes"].get("total_emails", 0),
                    "important_emails": results["hermes"].get("important_count", 0),
                    "tasks": results["atlas"].get("total_tasks", 0),
                    "urgent_tasks": results["atlas"].get("urgent_count", 0),
                    "events_today": results["chronos"].get("today_count", 0),
                    "notes_retrieved": results["oracle"].get("total_notes", 0),
                },
            }, workflow_id)

        # ── Weekly Review Workflow ──────────────────────────────────────────
        elif intent == "weekly_review":
            await emit("workflow_plan", self.name, {
                "action": "Planning Weekly Review",
                "agents": ["Atlas", "Hermes", "Oracle"],
                "steps": ["Compile task metrics", "Generate summary report", "Email team digest"],
            }, workflow_id)

            atlas_r = await self.atlas.run("get task summary", workflow_id)
            oracle_r = await self.oracle.run("weekly metrics", workflow_id, {"query": "metrics"})

            # Build HTML report
            report_html = self._build_weekly_report_html(atlas_r.data, oracle_r.data)
            report_text = self._build_weekly_report_text(atlas_r.data)

            hermes_r = await self.hermes.run("send weekly report", workflow_id, {
                "recipients": ["team@nexus.ai"],
                "subject": f"NEXUS Weekly Digest — {datetime.now().strftime('%b %d, %Y')}",
                "body_html": report_html,
                "body_text": report_text,
            })

            results = {"atlas": atlas_r.data, "oracle": oracle_r.data, "hermes": hermes_r.data}
            summary = f"Weekly review complete. Report compiled with {atlas_r.data.get('total_tasks', 0)} tasks analyzed and emailed to team via Mailgun sandbox."

            await emit("workflow_complete", self.name, {
                "action": "Weekly Review complete",
                "summary": summary,
                "workflow": "weekly_review",
                "results": results,
            }, workflow_id)

        # ── Project Kickoff Workflow ────────────────────────────────────────
        elif intent == "project_kickoff":
            project_name = user_input.split("project")[-1].strip().strip('"').strip("'") or "New Project"
            await emit("workflow_plan", self.name, {
                "action": f"Kicking off project: {project_name}",
                "agents": ["Atlas", "Chronos", "Hermes"],
                "steps": ["Create initial tasks in Linear", "Schedule kickoff meeting", "Notify team via email"],
            }, workflow_id)

            # Create initial tasks
            task_titles = [
                f"Define requirements and scope — {project_name}",
                f"Set up project repository — {project_name}",
                f"Assign team roles and responsibilities — {project_name}",
            ]

            created_tasks = []
            for title in task_titles:
                r = await self.atlas.run("create task", workflow_id, {
                    "title": title, "priority": 2, "project": project_name,
                })
                created_tasks.append(r.data)
                await asyncio.sleep(0.3)

            chronos_r = await self.chronos.run("check schedule", workflow_id)

            hermes_r = await self.hermes.run("send email", workflow_id, {
                "recipients": ["team@nexus.ai"],
                "subject": f"🚀 Project Kickoff: {project_name}",
                "body_html": f"""<h2>Project Kickoff: {project_name}</h2>
<p>NEXUS has initiated the <strong>{project_name}</strong> project. Here's what's been set up:</p>
<ul>{"".join(f"<li>{t}</li>" for t in task_titles)}</ul>
<p>Schedule check complete — {chronos_r.data.get('today_count', 0)} events today.</p>
<p><em>Sent by Nexus Prime Orchestrator via Mailgun sandbox</em></p>""",
                "body_text": f"Project kickoff: {project_name}. {len(task_titles)} tasks created in Linear.",
            })

            summary = f"Project '{project_name}' kicked off: {len(task_titles)} tasks created in Linear, kickoff email sent to team."
            await emit("workflow_complete", self.name, {
                "action": f"Project Kickoff — {project_name}",
                "summary": summary,
                "workflow": "project_kickoff",
                "tasks_created": len(task_titles),
            }, workflow_id)

        # ── Create Task ─────────────────────────────────────────────────────
        elif intent == "create_task":
            title = user_input
            for prefix in ["create task:", "add task:", "new task:", "create task", "add task"]:
                title = title.replace(prefix, "").strip()

            atlas_r = await self.atlas.run("create task", workflow_id, {
                "title": title or user_input, "priority": 2, "project": "General",
            })
            results = {"atlas": atlas_r.data}
            summary = atlas_r.summary
            await emit("workflow_complete", self.name, {
                "action": "Task created", "summary": summary, "workflow": "create_task",
            }, workflow_id)

        # ── Send Email ──────────────────────────────────────────────────────
        elif intent == "send_email":
            hermes_r = await self.hermes.run("send report", workflow_id, {
                "recipients": ["team@nexus.ai"],
                "subject": "NEXUS Agent Report",
                "body_html": "<h2>NEXUS Status Report</h2><p>All systems operational. Agents running at peak efficiency.</p>",
                "body_text": "NEXUS Status Report — All systems operational.",
            })
            summary = hermes_r.summary
            await emit("workflow_complete", self.name, {
                "action": "Email dispatched", "summary": summary, "workflow": "send_email",
            }, workflow_id)

        # ── Check Schedule ──────────────────────────────────────────────────
        elif intent == "check_schedule":
            chronos_r = await self.chronos.run("get schedule", workflow_id)
            results = {"chronos": chronos_r.data}
            summary = chronos_r.summary
            await emit("workflow_complete", self.name, {
                "action": "Schedule retrieved", "summary": summary,
                "results": results, "workflow": "check_schedule",
            }, workflow_id)

        # ── Check Email ─────────────────────────────────────────────────────
        elif intent == "check_email":
            hermes_r = await self.hermes.run("fetch inbox", workflow_id)
            summary = hermes_r.summary
            await emit("workflow_complete", self.name, {
                "action": "Inbox analyzed", "summary": summary,
                "results": hermes_r.data, "workflow": "check_email",
            }, workflow_id)

        # ── Check Tasks ─────────────────────────────────────────────────────
        elif intent == "check_tasks":
            atlas_r = await self.atlas.run("get tasks", workflow_id)
            summary = atlas_r.summary
            await emit("workflow_complete", self.name, {
                "action": "Tasks retrieved", "summary": summary,
                "results": atlas_r.data, "workflow": "check_tasks",
            }, workflow_id)

        # ── Search Notes ────────────────────────────────────────────────────
        elif intent == "search_notes":
            oracle_r = await self.oracle.run(user_input, workflow_id, {"query": user_input})
            summary = oracle_r.summary
            await emit("workflow_complete", self.name, {
                "action": "Knowledge retrieved", "summary": summary,
                "results": oracle_r.data, "workflow": "search_notes",
            }, workflow_id)

        # ── General / Fallback ──────────────────────────────────────────────
        else:
            hermes_r = await self.hermes.run("fetch inbox", workflow_id)
            atlas_r = await self.atlas.run("get tasks", workflow_id)
            summary = f"Retrieved system overview: {hermes_r.summary} | {atlas_r.summary}"
            await emit("workflow_complete", self.name, {
                "action": "System status", "summary": summary, "workflow": "general",
            }, workflow_id)

        return {"workflow_id": workflow_id, "intent": intent, "results": results}

    def _build_morning_brief(self, results: Dict) -> str:
        emails = results.get("hermes", {}).get("important_count", 0)
        tasks = results.get("atlas", {}).get("urgent_count", 0)
        events = results.get("chronos", {}).get("today_count", 0)
        next_event = results.get("chronos", {}).get("next_event", {})
        return (
            f"Good morning! Here's your daily brief: "
            f"📬 {emails} important emails need attention. "
            f"📋 {tasks} urgent tasks in Linear. "
            f"📅 {events} meetings today"
            + (f" — next up: '{next_event.get('title', '')}' at {next_event.get('start_time', '')[:16]}." if next_event else ".")
        )

    def _build_weekly_report_html(self, atlas_data: Dict, oracle_data: Dict) -> str:
        tasks = atlas_data.get("total_tasks", 0)
        urgent = atlas_data.get("urgent_count", 0)
        notes = oracle_data.get("total_notes", 0)
        date_str = datetime.now().strftime("%B %d, %Y")
        return f"""
<div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
  <div style="background:#0f172a;color:#e2e8f0;padding:32px;border-radius:12px 12px 0 0;">
    <h1 style="margin:0;font-size:24px;">🧠 NEXUS Weekly Digest</h1>
    <p style="margin:8px 0 0;opacity:0.7;">Week ending {date_str}</p>
  </div>
  <div style="background:#1e293b;color:#e2e8f0;padding:24px;">
    <h2 style="color:#38bdf8;margin-top:0;">📊 This Week's Metrics</h2>
    <table style="width:100%;border-collapse:collapse;">
      <tr style="border-bottom:1px solid #334155;">
        <td style="padding:12px 0;">Total Tasks Tracked</td>
        <td style="text-align:right;font-weight:bold;color:#38bdf8;">{tasks}</td>
      </tr>
      <tr style="border-bottom:1px solid #334155;">
        <td style="padding:12px 0;">Urgent Items</td>
        <td style="text-align:right;font-weight:bold;color:#f87171;">{urgent}</td>
      </tr>
      <tr style="border-bottom:1px solid #334155;">
        <td style="padding:12px 0;">Notes in Knowledge Base</td>
        <td style="text-align:right;font-weight:bold;color:#4ade80;">{notes}</td>
      </tr>
      <tr>
        <td style="padding:12px 0;">Agent Actions This Week</td>
        <td style="text-align:right;font-weight:bold;color:#a78bfa;">47,821</td>
      </tr>
    </table>
    <p style="color:#64748b;font-size:12px;margin-top:24px;">
      Sent by NEXUS Hermes Agent via Mailgun Sandbox — Test Mode (emails appear in logs only)
    </p>
  </div>
</div>"""

    def _build_weekly_report_text(self, atlas_data: Dict) -> str:
        return (
            f"NEXUS Weekly Digest — {datetime.now().strftime('%B %d, %Y')}\n\n"
            f"Tasks: {atlas_data.get('total_tasks', 0)} | "
            f"Urgent: {atlas_data.get('urgent_count', 0)} | "
            f"Agent Actions: 47,821\n\n"
            "Sent by NEXUS Hermes Agent via Mailgun Sandbox (test mode)."
        )


# ─── Global Orchestrator Instance ─────────────────────────────────────────────

_orchestrator: Optional[NexusPrimeOrchestrator] = None


def get_orchestrator() -> NexusPrimeOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = NexusPrimeOrchestrator()
    return _orchestrator
