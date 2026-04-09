"""
NEXUS FastAPI Gateway — Cloud Run Edition
Serves React SPA + REST API + SSE on port 8080
"""
import os, uuid, json, asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

STATIC_DIR = Path(__file__).parent.parent / "static"

app = FastAPI(title="NEXUS Multi-Agent API", version="1.0.0", docs_url="/api/docs", redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
async def startup():
    logger.info("🚀 NEXUS starting...")
    try:
        from database.seed_data import seed_database
        await seed_database()
    except Exception as e:
        logger.warning(f"Seed skipped: {e}")
    logger.info(f"✅ Ready — static exists: {STATIC_DIR.exists()}")


# ── Models ───────────────────────────────────────────────────────────────────
class OrchestrationRequest(BaseModel):
    user_input: str
    workflow_id: Optional[str] = None

class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "medium"
    assignee: Optional[str] = None
    project: Optional[str] = "General"
    due_date: Optional[str] = None
    tags: Optional[List[str]] = []

class EmailSendRequest(BaseModel):
    to: List[str]; subject: str; body: str; body_html: Optional[str] = None


# ── Health ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "nexus-agent", "mode": os.getenv("APP_MODE", "demo"), "timestamp": datetime.utcnow().isoformat()}


@app.get("/api/status")
async def status():
    from database.db import db_get_recent_activities
    recent = await db_get_recent_activities(limit=5)
    return {
        "system": "NEXUS v1.0", "status": "operational", "mode": os.getenv("APP_MODE", "demo"),
        "agents": {"nexus_prime": {"status":"ready","emoji":"🧠"}, "hermes": {"status":"ready","emoji":"📬"},
                   "atlas": {"status":"ready","emoji":"📋"}, "chronos": {"status":"ready","emoji":"📅"}, "oracle": {"status":"ready","emoji":"🔍"}},
        "recent_activity": recent, "timestamp": datetime.utcnow().isoformat(),
    }


# ── SSE Stream ───────────────────────────────────────────────────────────────
@app.get("/api/stream")
async def sse_stream():
    from agents.orchestrator import event_bus

    async def gen():
        q = event_bus.subscribe()
        try:
            yield f"data: {json.dumps({'type':'connected','timestamp':datetime.utcnow().isoformat()})}\n\n"
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=25.0)
                    yield f"data: {json.dumps(ev)}\n\n"
                except asyncio.TimeoutError:
                    yield f"data: {json.dumps({'type':'heartbeat','timestamp':datetime.utcnow().isoformat()})}\n\n"
        except asyncio.CancelledError:
            pass
        finally:
            event_bus.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control":"no-cache","X-Accel-Buffering":"no","Connection":"keep-alive"})


# ── Orchestration ─────────────────────────────────────────────────────────────
@app.post("/api/orchestrate")
async def orchestrate(req: OrchestrationRequest, bg: BackgroundTasks):
    wid = req.workflow_id or str(uuid.uuid4())
    from agents.orchestrator import get_orchestrator, event_bus

    async def run():
        try:
            await get_orchestrator().orchestrate(req.user_input, wid)
        except Exception as e:
            logger.error(f"Workflow err: {e}")
            await event_bus.publish({"type":"error","agent":"Nexus Prime","data":{"error":str(e),"action":"Workflow failed"},"workflow_id":wid,"timestamp":datetime.utcnow().isoformat()})

    bg.add_task(run)
    return {"workflow_id": wid, "status": "initiated", "stream_url": "/api/stream", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/orchestrate/sync")
async def orchestrate_sync(req: OrchestrationRequest):
    wid = req.workflow_id or str(uuid.uuid4())
    result = await get_orchestrator().orchestrate(req.user_input, wid)
    return {"workflow_id": wid, "result": result, "status": "complete"}


# ── Tasks ─────────────────────────────────────────────────────────────────────
@app.get("/api/tasks")
async def get_tasks(status: Optional[str] = None):
    from database.db import db_get_tasks
    tasks = await db_get_tasks(status=status)
    return {"tasks": tasks, "total": len(tasks)}

@app.post("/api/tasks")
async def create_task(req: TaskCreateRequest):
    from database.db import db_create_task
    from tools.mcp_tools import linear_create_issue
    pm = {"urgent":1,"high":2,"medium":3,"low":4}
    lr = await linear_create_issue(req.title, req.description or "", pm.get(req.priority, 3))
    td = {"id":str(uuid.uuid4()),"title":req.title,"description":req.description,"status":"todo",
          "priority":req.priority,"assignee":req.assignee,"project":req.project,"due_date":req.due_date,
          "linear_id":lr.get("issue",{}).get("id"),"tags":json.dumps(req.tags or [])}
    return {"task": await db_create_task(td), "linear": lr}


# ── Schedule ──────────────────────────────────────────────────────────────────
@app.get("/api/schedule")
async def get_schedule(period: str = "week"):
    from tools.mcp_tools import calendar_get_today, calendar_get_week
    return await (calendar_get_today() if period == "today" else calendar_get_week())


# ── Emails ────────────────────────────────────────────────────────────────────
@app.get("/api/emails")
async def get_emails():
    from database.db import db_get_emails
    emails = await db_get_emails()
    return {"emails": emails, "total": len(emails)}

@app.get("/api/emails/inbox")
async def get_inbox():
    from tools.mcp_tools import gmail_get_inbox
    return await gmail_get_inbox()

@app.post("/api/emails/send")
async def send_email(req: EmailSendRequest):
    from tools.mcp_tools import mailgun_send_email
    return await mailgun_send_email(req.to, req.subject, req.body_html or f"<p>{req.body}</p>", req.body)


# ── Notes ─────────────────────────────────────────────────────────────────────
@app.get("/api/notes")
async def get_notes(query: Optional[str] = None):
    from database.db import db_get_notes
    notes = await db_get_notes()
    if query:
        q = query.lower()
        notes = [n for n in notes if q in n["title"].lower() or q in n["content"].lower()]
    return {"notes": notes, "total": len(notes)}


# ── Activity ──────────────────────────────────────────────────────────────────
@app.get("/api/activity")
async def get_activity(limit: int = Query(default=50, le=200)):
    from database.db import db_get_recent_activities
    acts = await db_get_recent_activities(limit=limit)
    return {"activities": acts, "total": len(acts)}


# ── Linear ────────────────────────────────────────────────────────────────────
@app.get("/api/linear/issues")
async def get_linear_issues(status: Optional[str] = None):
    from tools.mcp_tools import linear_get_issues
    return await linear_get_issues(status=status)


# ── Demo Shortcuts ────────────────────────────────────────────────────────────
@app.post("/api/demo/morning-brief")
async def demo_morning_brief(bg: BackgroundTasks):
    return await orchestrate(OrchestrationRequest(user_input="Give me my morning brief"), bg)

@app.post("/api/demo/weekly-review")
async def demo_weekly_review(bg: BackgroundTasks):
    return await orchestrate(OrchestrationRequest(user_input="Run weekly review"), bg)

@app.post("/api/demo/project-kickoff")
async def demo_project_kickoff(bg: BackgroundTasks):
    return await orchestrate(OrchestrationRequest(user_input="Kick off the Alpha Platform project"), bg)


# ── Serve React SPA — MUST be last ───────────────────────────────────────────
if STATIC_DIR.exists():
    if (STATIC_DIR / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(STATIC_DIR / "assets")), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        idx = STATIC_DIR / "index.html"
        if idx.exists():
            return FileResponse(str(idx))
        return {"error": "Frontend not built"}
else:
    @app.get("/")
    async def root():
        return {"name": "NEXUS API", "docs": "/api/docs", "note": "Frontend not built — run npm run build"}
