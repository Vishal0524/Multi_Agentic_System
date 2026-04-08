"""
Calendar Agent — Manages schedules, events, and time conflicts.
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from google.adk.agents.llm_agent import Agent
from database import db
from datetime import datetime


# ─── TOOL FUNCTIONS ─────────────────────────────────────────

def list_events(date: str = "") -> dict:
    """List calendar events, optionally filtered by date.
    
    Args:
        date: Filter events by date (YYYY-MM-DD format). Leave empty for all events.
    
    Returns:
        Dictionary with list of events and count.
    """
    events = db.list_events(date=date if date else None)
    return {"status": "success", "count": len(events), "events": events}


def create_event(title: str, start_time: str, end_time: str, description: str = "",
                 location: str = "", attendees: str = "", event_type: str = "meeting") -> dict:
    """Create a new calendar event.
    
    Args:
        title: Event title (required).
        start_time: Start time in YYYY-MM-DDTHH:MM:SS format (required).
        end_time: End time in YYYY-MM-DDTHH:MM:SS format (required).
        description: Event description.
        location: Event location (physical or virtual).
        attendees: Comma-separated list of attendees.
        event_type: Type of event (meeting, deadline, reminder, focus_time, standup).
    
    Returns:
        Dictionary with the created event details.
    """
    # Check for conflicts first
    conflicts = db.check_conflicts(start_time, end_time)
    
    event = db.create_event(
        title=title, start_time=start_time, end_time=end_time,
        description=description, location=location, attendees=attendees,
        event_type=event_type
    )
    
    result = {"status": "success", "message": f"Event '{title}' created", "event": event}
    if conflicts:
        result["warning"] = f"⚠️ {len(conflicts)} conflicting event(s) detected"
        result["conflicts"] = conflicts
    return result


def check_conflicts(start_time: str, end_time: str) -> dict:
    """Check for scheduling conflicts in a given time range.
    
    Args:
        start_time: Start of the time range in YYYY-MM-DDTHH:MM:SS format (required).
        end_time: End of the time range in YYYY-MM-DDTHH:MM:SS format (required).
    
    Returns:
        Dictionary with any conflicting events found.
    """
    conflicts = db.check_conflicts(start_time, end_time)
    if conflicts:
        return {
            "status": "conflicts_found",
            "count": len(conflicts),
            "message": f"Found {len(conflicts)} conflicting event(s)",
            "conflicts": conflicts
        }
    return {"status": "clear", "message": "No conflicts found - time slot is available!"}


def get_today_schedule() -> dict:
    """Get today's complete schedule with all events.
    
    Returns:
        Dictionary with today's events organized chronologically.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    events = db.list_events(date=today)
    
    # Also check tomorrow
    from datetime import timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_events = db.list_events(date=tomorrow)
    
    return {
        "status": "success",
        "date": today,
        "today_count": len(events),
        "today_events": events,
        "tomorrow_count": len(tomorrow_events),
        "tomorrow_preview": tomorrow_events[:3]
    }


# ─── AGENT DEFINITION ──────────────────────────────────────

calendar_agent = Agent(
    model="gemini-2.0-flash",
    name="calendar_agent",
    description="Manages calendar events, schedules, and detects time conflicts.",
    instruction="""You are the Calendar Agent, a specialized AI assistant for schedule management.

Your capabilities:
- List events for any date or show all upcoming events
- Create new events with full details (time, location, attendees)
- Check for scheduling conflicts before booking
- Show today's schedule with a timeline view

When presenting schedules, format them as a clear timeline:
- 🕐 Time slots with duration
- 📍 Location
- 👥 Attendees
- 🏷️ Event type (meeting/deadline/focus_time/standup)

Always check for conflicts when creating new events.
Use 24-hour format for clarity. Be concise and action-oriented.""",
    tools=[list_events, create_event, check_conflicts, get_today_schedule],
)
