"""
Database module for Multi-Agent Productivity Assistant.
Provides SQLite-backed storage for tasks, events, emails, and notes.
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "productivity.db")


def get_connection() -> sqlite3.Connection:
    """Get a database connection with row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_database():
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'todo' CHECK(status IN ('todo','in_progress','done','blocked')),
            priority TEXT DEFAULT 'medium' CHECK(priority IN ('low','medium','high','critical')),
            assignee TEXT,
            project TEXT,
            due_date TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            start_time TEXT NOT NULL,
            end_time TEXT NOT NULL,
            location TEXT,
            attendees TEXT,
            event_type TEXT DEFAULT 'meeting' CHECK(event_type IN ('meeting','deadline','reminder','focus_time','standup')),
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS emails (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            sender TEXT NOT NULL,
            recipients TEXT NOT NULL,
            body TEXT,
            status TEXT DEFAULT 'draft' CHECK(status IN ('draft','sent','received','failed')),
            thread_id TEXT,
            sent_at TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            tags TEXT,
            category TEXT DEFAULT 'general',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()


# ─── TASK CRUD ─────────────────────────────────────────────

def create_task(title: str, description: str = "", status: str = "todo",
                priority: str = "medium", assignee: str = "", project: str = "",
                due_date: str = "") -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (title, description, status, priority, assignee, project, due_date) VALUES (?,?,?,?,?,?,?)",
        (title, description, status, priority, assignee, project, due_date)
    )
    conn.commit()
    task_id = cursor.lastrowid
    task = dict(conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone())
    conn.close()
    return task


def list_tasks(status: Optional[str] = None, project: Optional[str] = None) -> list:
    conn = get_connection()
    query = "SELECT * FROM tasks WHERE 1=1"
    params = []
    if status:
        query += " AND status=?"
        params.append(status)
    if project:
        query += " AND project=?"
        params.append(project)
    query += " ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_task(task_id: int, **kwargs) -> dict:
    conn = get_connection()
    allowed = ["title", "description", "status", "priority", "assignee", "project", "due_date"]
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if updates:
        set_clause = ", ".join(f"{k}=?" for k in updates)
        values = list(updates.values()) + [task_id]
        conn.execute(f"UPDATE tasks SET {set_clause}, updated_at=datetime('now') WHERE id=?", values)
        conn.commit()
    task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.close()
    return dict(task) if task else {}


def get_task_summary() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    by_status = {}
    for row in conn.execute("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status").fetchall():
        by_status[row["status"]] = row["cnt"]
    by_priority = {}
    for row in conn.execute("SELECT priority, COUNT(*) as cnt FROM tasks GROUP BY priority").fetchall():
        by_priority[row["priority"]] = row["cnt"]
    conn.close()
    return {"total": total, "by_status": by_status, "by_priority": by_priority}


# ─── EVENT CRUD ────────────────────────────────────────────

def create_event(title: str, start_time: str, end_time: str, description: str = "",
                 location: str = "", attendees: str = "", event_type: str = "meeting") -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO events (title, start_time, end_time, description, location, attendees, event_type) VALUES (?,?,?,?,?,?,?)",
        (title, start_time, end_time, description, location, attendees, event_type)
    )
    conn.commit()
    event_id = cursor.lastrowid
    event = dict(conn.execute("SELECT * FROM events WHERE id=?", (event_id,)).fetchone())
    conn.close()
    return event


def list_events(date: Optional[str] = None) -> list:
    conn = get_connection()
    if date:
        rows = conn.execute(
            "SELECT * FROM events WHERE DATE(start_time) = DATE(?) ORDER BY start_time",
            (date,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM events ORDER BY start_time").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def check_conflicts(start_time: str, end_time: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM events WHERE start_time < ? AND end_time > ? ORDER BY start_time",
        (end_time, start_time)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─── EMAIL CRUD ────────────────────────────────────────────

def create_email(subject: str, sender: str, recipients: str, body: str = "",
                 status: str = "draft", thread_id: str = "") -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    sent_at = datetime.now().isoformat() if status == "sent" else None
    cursor.execute(
        "INSERT INTO emails (subject, sender, recipients, body, status, thread_id, sent_at) VALUES (?,?,?,?,?,?,?)",
        (subject, sender, recipients, body, status, thread_id, sent_at)
    )
    conn.commit()
    email_id = cursor.lastrowid
    email = dict(conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone())
    conn.close()
    return email


def list_emails(status: Optional[str] = None) -> list:
    conn = get_connection()
    if status:
        rows = conn.execute("SELECT * FROM emails WHERE status=? ORDER BY created_at DESC", (status,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM emails ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_email_status(email_id: int, status: str) -> dict:
    conn = get_connection()
    conn.execute("UPDATE emails SET status=?, sent_at=datetime('now') WHERE id=?", (status, email_id))
    conn.commit()
    email = conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
    conn.close()
    return dict(email) if email else {}


# ─── NOTES CRUD ────────────────────────────────────────────

def create_note(title: str, content: str, tags: str = "", category: str = "general") -> dict:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notes (title, content, tags, category) VALUES (?,?,?,?)",
        (title, content, tags, category)
    )
    conn.commit()
    note_id = cursor.lastrowid
    note = dict(conn.execute("SELECT * FROM notes WHERE id=?", (note_id,)).fetchone())
    conn.close()
    return note


def list_notes(category: Optional[str] = None) -> list:
    conn = get_connection()
    if category:
        rows = conn.execute("SELECT * FROM notes WHERE category=? ORDER BY updated_at DESC", (category,)).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def search_notes(query: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM notes WHERE title LIKE ? OR content LIKE ? OR tags LIKE ? ORDER BY updated_at DESC",
        (f"%{query}%", f"%{query}%", f"%{query}%")
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
