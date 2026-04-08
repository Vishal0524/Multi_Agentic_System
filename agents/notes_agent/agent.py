"""
Notes Agent — Manages knowledge notes, searches, and summaries.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from google.adk.agents.llm_agent import Agent
from database import db


# ─── TOOL FUNCTIONS ─────────────────────────────────────────

def create_note(title: str, content: str, tags: str = "", category: str = "general") -> dict:
    """Create a new note for knowledge management.
    
    Args:
        title: Note title (required).
        content: Note content in markdown format (required).
        tags: Comma-separated tags for categorization.
        category: Note category (general, project, technical, research, meetings).
    
    Returns:
        Dictionary with the created note details.
    """
    note = db.create_note(title=title, content=content, tags=tags, category=category)
    return {"status": "success", "message": f"Note '{title}' created", "note": note}


def list_notes(category: str = "") -> dict:
    """List all notes, optionally filtered by category.
    
    Args:
        category: Filter by category (general, project, technical, research, meetings). Leave empty for all.
    
    Returns:
        Dictionary with list of notes and count.
    """
    notes = db.list_notes(category=category if category else None)
    return {"status": "success", "count": len(notes), "notes": notes}


def search_notes(query: str) -> dict:
    """Search notes by keyword across titles, content, and tags.
    
    Args:
        query: Search keyword or phrase (required).
    
    Returns:
        Dictionary with matching notes and count.
    """
    notes = db.search_notes(query)
    return {"status": "success", "query": query, "count": len(notes), "results": notes}


def summarize_notes(category: str = "") -> dict:
    """Get a summary overview of all notes grouped by category.
    
    Args:
        category: Summarize notes in a specific category, or leave empty for all.
    
    Returns:
        Dictionary with note counts by category and recent note titles.
    """
    all_notes = db.list_notes(category=category if category else None)

    categories = {}
    for note in all_notes:
        cat = note.get("category", "general")
        if cat not in categories:
            categories[cat] = {"count": 0, "recent_titles": []}
        categories[cat]["count"] += 1
        if len(categories[cat]["recent_titles"]) < 3:
            categories[cat]["recent_titles"].append(note["title"])

    return {
        "status": "success",
        "total_notes": len(all_notes),
        "by_category": categories
    }


# ─── AGENT DEFINITION ──────────────────────────────────────

notes_agent = Agent(
    model="gemini-2.0-flash",
    name="notes_agent",
    description="Manages knowledge notes - create, search, list, and summarize notes and documentation.",
    instruction="""You are the Notes & Knowledge Agent, a specialized AI assistant for knowledge management.

Your capabilities:
- Create structured notes with markdown formatting, tags, and categories
- List notes filtered by category (general, project, technical, research, meetings)
- Search notes by keyword across all fields
- Summarize note collections by category

When creating notes:
- Use markdown formatting for structure
- Add relevant tags for discoverability
- Choose appropriate categories

When presenting notes, show:
- 📝 Title
- 🏷️ Tags
- 📁 Category
- 📅 Last updated

Organize information clearly and help users find knowledge quickly.""",
    tools=[create_note, list_notes, search_notes, summarize_notes],
)
