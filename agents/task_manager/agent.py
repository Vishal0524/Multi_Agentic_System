"""
Task Manager Agent — Manages project tasks, priorities, and assignments.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from google.adk.agents.llm_agent import Agent
from database import db


# ─── TOOL FUNCTIONS ─────────────────────────────────────────

def list_tasks(status: str = "", project: str = "") -> dict:
    """List all tasks, optionally filtered by status or project.
    
    Args:
        status: Filter by status (todo, in_progress, done, blocked). Leave empty for all.
        project: Filter by project name. Leave empty for all.
    
    Returns:
        Dictionary with list of tasks and count.
    """
    tasks = db.list_tasks(
        status=status if status else None,
        project=project if project else None
    )
    return {"status": "success", "count": len(tasks), "tasks": tasks}


def create_task(title: str, description: str = "", priority: str = "medium",
                assignee: str = "", project: str = "", due_date: str = "") -> dict:
    """Create a new task.
    
    Args:
        title: Task title (required).
        description: Detailed task description.
        priority: Priority level (low, medium, high, critical).
        assignee: Person responsible for the task.
        project: Project the task belongs to.
        due_date: Due date in YYYY-MM-DD format.
    
    Returns:
        Dictionary with the created task details.
    """
    task = db.create_task(
        title=title, description=description, priority=priority,
        assignee=assignee, project=project, due_date=due_date
    )
    return {"status": "success", "message": f"Task '{title}' created successfully", "task": task}


def update_task(task_id: int, status: str = "", priority: str = "",
                assignee: str = "", title: str = "", description: str = "") -> dict:
    """Update an existing task's status, priority, assignee, or other fields.
    
    Args:
        task_id: The ID of the task to update (required).
        status: New status (todo, in_progress, done, blocked).
        priority: New priority (low, medium, high, critical).
        assignee: New assignee name.
        title: New title. 
        description: New description.
    
    Returns:
        Dictionary with the updated task details.
    """
    kwargs = {}
    if status:
        kwargs["status"] = status
    if priority:
        kwargs["priority"] = priority
    if assignee:
        kwargs["assignee"] = assignee
    if title:
        kwargs["title"] = title
    if description:
        kwargs["description"] = description

    task = db.update_task(task_id, **kwargs)
    if task:
        return {"status": "success", "message": f"Task #{task_id} updated", "task": task}
    return {"status": "error", "message": f"Task #{task_id} not found"}


def get_task_summary() -> dict:
    """Get a high-level summary of all tasks across projects.
    
    Returns:
        Dictionary with task counts by status and priority.
    """
    summary = db.get_task_summary()
    return {"status": "success", "summary": summary}


# ─── AGENT DEFINITION ──────────────────────────────────────

task_agent = Agent(
    model="gemini-2.0-flash",
    name="task_manager",
    description="Manages project tasks - create, update, list, and summarize tasks across projects.",
    instruction="""You are the Task Manager Agent, a specialized AI assistant for project task management.

Your capabilities:
- List tasks with optional filters (by status: todo/in_progress/done/blocked, or by project)
- Create new tasks with titles, descriptions, priorities, assignees, and due dates
- Update existing tasks (change status, priority, assignee, etc.)
- Provide task summaries and project overviews

When presenting tasks, format them clearly with:
- 📋 Task title
- 🔴/🟡/🟢 Priority indicators (critical/high → 🔴, medium → 🟡, low → 🟢)
- 📊 Status badges
- 👤 Assignee
- 📅 Due date

Always be proactive - if a user asks about tasks, also mention any overdue or critical items.
Respond in a concise but informative manner suitable for busy professionals.""",
    tools=[list_tasks, create_task, update_task, get_task_summary],
)
