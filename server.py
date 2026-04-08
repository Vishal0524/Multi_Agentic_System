"""
FastAPI Server — Main entry point for the Multi-Agent Productivity Assistant.
Serves the REST API and the premium web UI.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from database.db import init_database
from database.seed_data import seed_database
import database.db as db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(message)s")
logger = logging.getLogger("server")

# ─── FASTAPI APP ────────────────────────────────────────────

app = FastAPI(
    title="Multi-Agent Productivity Assistant",
    description="AI-powered multi-agent system for task, calendar, email, and knowledge management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── STARTUP ───────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    """Initialize database and seed data on startup."""
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "productivity.db")
    if not os.path.exists(db_path):
        logger.info("🌱 First run — seeding database with demo data...")
        seed_database()
    else:
        init_database()
    logger.info("✅ Database ready")
    logger.info("🚀 Multi-Agent Productivity Assistant is online!")


# ─── CHAT ENDPOINT ─────────────────────────────────────────

@app.post("/api/chat")
async def chat(request: Request):
    """Send a message to the orchestrator agent and get a response."""
    try:
        data = await request.json()
        message = data.get("message", "")
        session_id = data.get("session_id", "default_session")

        if not message:
            return JSONResponse({"error": "Message is required"}, status_code=400)

        from google.adk.runners import InMemoryRunner
        from google.genai import types
        from agents.orchestrator.agent import root_agent

        runner = InMemoryRunner(agent=root_agent, app_name="productivity_assistant")

        content = types.Content(
            role="user",
            parts=[types.Part.from_text(text=message)]
        )

        response_text = ""
        agent_actions = []

        async for event in runner.run_async(
            user_id="web_user",
            session_id=session_id,
            new_message=content,
        ):
            # Track which agents are being invoked
            if hasattr(event, 'author') and event.author:
                if event.author not in ["user", "orchestrator"]:
                    agent_actions.append({
                        "agent": event.author,
                        "timestamp": datetime.now().isoformat()
                    })

            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        response_text += part.text

        return JSONResponse({
            "response": response_text,
            "agent_actions": agent_actions,
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── DASHBOARD ENDPOINT ───────────────────────────────────

@app.get("/api/dashboard")
async def dashboard():
    """Get aggregated dashboard data from all sources."""
    try:
        tasks = db.list_tasks()
        events = db.list_events()
        emails = db.list_emails()
        notes = db.list_notes()
        task_summary = db.get_task_summary()

        # Today's events
        today = datetime.now().strftime("%Y-%m-%d")
        today_events = db.list_events(date=today)

        return JSONResponse({
            "task_summary": task_summary,
            "recent_tasks": tasks[:5],
            "today_events": today_events,
            "upcoming_events": events[:5],
            "recent_emails": emails[:5],
            "recent_notes": notes[:3],
            "stats": {
                "total_tasks": len(tasks),
                "total_events": len(events),
                "total_emails": len(emails),
                "total_notes": len(notes),
                "tasks_in_progress": sum(1 for t in tasks if t["status"] == "in_progress"),
                "critical_tasks": sum(1 for t in tasks if t["priority"] == "critical"),
            }
        })
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


# ─── DATA ENDPOINTS ───────────────────────────────────────

@app.get("/api/tasks")
async def get_tasks(status: str = None, project: str = None):
    tasks = db.list_tasks(status=status, project=project)
    return JSONResponse({"tasks": tasks, "count": len(tasks)})


@app.get("/api/events")
async def get_events(date: str = None):
    events = db.list_events(date=date)
    return JSONResponse({"events": events, "count": len(events)})


@app.get("/api/emails")
async def get_emails(status: str = None):
    emails = db.list_emails(status=status)
    return JSONResponse({"emails": emails, "count": len(emails)})


@app.get("/api/notes")
async def get_notes(category: str = None):
    notes = db.list_notes(category=category)
    return JSONResponse({"notes": notes, "count": len(notes)})


@app.post("/api/seed")
async def reseed():
    """Re-seed the database with demo data."""
    seed_database()
    return JSONResponse({"status": "success", "message": "Database re-seeded with demo data"})


# ─── STATIC FILES & INDEX ─────────────────────────────────

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    """Serve the main UI."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>Multi-Agent Productivity Assistant</h1><p>Static files not found.</p>")


# ─── RUN ───────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    print("\n" + "="*60)
    print("  🤖 Multi-Agent Productivity Assistant")
    print("  ════════════════════════════════════")
    print(f"  🌐 Web UI:      http://localhost:8000")
    print(f"  📡 API:         http://localhost:8000/api")
    print(f"  📋 Dashboard:   http://localhost:8000/api/dashboard")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
