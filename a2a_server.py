"""
A2A Protocol Server — Exposes the orchestrator agent as an A2A-compatible server.
Demonstrates Agent-to-Agent communication protocol.
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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ─── A2A Agent Card ────────────────────────────────────────

AGENT_CARD = {
    "name": "Productivity Orchestrator",
    "description": "Multi-agent productivity assistant that coordinates task management, calendar scheduling, email communication, and knowledge notes.",
    "version": "1.0.0",
    "protocol": "a2a",
    "capabilities": [
        {
            "name": "task_management",
            "description": "Create, update, list, and summarize project tasks"
        },
        {
            "name": "calendar_management",
            "description": "Schedule events, check conflicts, view daily schedules"
        },
        {
            "name": "email_management",
            "description": "Send emails via Mailgun sandbox, draft, and list emails"
        },
        {
            "name": "knowledge_management",
            "description": "Create, search, and organize notes and documentation"
        }
    ],
    "endpoints": {
        "base_url": "http://localhost:8001",
        "agent_card": "/.well-known/agent.json",
        "tasks_send": "/tasks/send",
        "tasks_get": "/tasks/{task_id}"
    },
    "authentication": {
        "type": "none",
        "note": "Demo mode - no authentication required"
    }
}


async def handle_a2a_request(request_data: dict) -> dict:
    """Handle an incoming A2A protocol request."""
    from google.adk.runners import InMemoryRunner
    from google.genai import types
    from agents.orchestrator.agent import root_agent
    from database.db import init_database

    init_database()

    runner = InMemoryRunner(agent=root_agent, app_name="productivity_assistant")

    message = request_data.get("message", {}).get("text", "")
    task_id = request_data.get("task_id", f"a2a_{datetime.now().strftime('%Y%m%d%H%M%S')}")

    content = types.Content(
        role="user",
        parts=[types.Part.from_text(text=message)]
    )

    response_text = ""
    async for event in runner.run_async(
        user_id="a2a_remote_agent",
        session_id=f"a2a_session_{task_id}",
        new_message=content,
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    response_text += part.text

    return {
        "task_id": task_id,
        "status": "completed",
        "response": {
            "text": response_text
        },
        "agent": AGENT_CARD["name"],
        "timestamp": datetime.now().isoformat()
    }


def create_a2a_app():
    """Create a FastAPI app that serves the A2A protocol endpoints."""
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

    app = FastAPI(title="Productivity Assistant - A2A Server", version="1.0.0")

    @app.get("/.well-known/agent.json")
    async def agent_card():
        """Serve the A2A Agent Card for discovery."""
        return JSONResponse(content=AGENT_CARD)

    @app.post("/tasks/send")
    async def send_task(request: Request):
        """Handle A2A task send requests."""
        data = await request.json()
        result = await handle_a2a_request(data)
        return JSONResponse(content=result)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "protocol": "a2a", "agent": AGENT_CARD["name"]}

    return app


if __name__ == "__main__":
    import uvicorn
    app = create_a2a_app()
    print("🌐 A2A Protocol Server starting...")
    print(f"📋 Agent Card: http://localhost:8001/.well-known/agent.json")
    print(f"📨 Task Endpoint: http://localhost:8001/tasks/send")
    uvicorn.run(app, host="0.0.0.0", port=8001)
