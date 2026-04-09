"""
NEXUS Database Layer
SQLite with SQLAlchemy async ORM
"""
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Boolean, Integer, JSON, select, update
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nexus.db").replace(
    "sqlite:///", "sqlite+aiosqlite:///"
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ─── Models ───────────────────────────────────────────────────────────────────

class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="todo")  # todo|in_progress|done|cancelled
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # low|medium|high|urgent
    assignee: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    project: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    due_date: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    linear_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    created_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())


class ScheduleEvent(Base):
    __tablename__ = "schedule_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_time: Mapped[str] = mapped_column(String(50))
    end_time: Mapped[str] = mapped_column(String(50))
    attendees: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    location: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    meeting_link: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    event_type: Mapped[str] = mapped_column(String(50), default="meeting")
    created_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())


class Note(Base):
    __tablename__ = "notes"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    title: Mapped[str] = mapped_column(String(500))
    content: Mapped[str] = mapped_column(Text)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())
    updated_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())


class EmailRecord(Base):
    __tablename__ = "email_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    subject: Mapped[str] = mapped_column(String(500))
    sender: Mapped[str] = mapped_column(String(200))
    recipients: Mapped[str] = mapped_column(Text)  # JSON array
    body_preview: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="sent")  # sent|draft|received
    mailgun_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    is_important: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())


class AgentActivity(Base):
    __tablename__ = "agent_activities"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    workflow_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(100))
    action: Mapped[str] = mapped_column(String(200))
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    status: Mapped[str] = mapped_column(String(50), default="running")  # running|success|error
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    trigger: Mapped[str] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), default="running")
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agents_involved: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    started_at: Mapped[str] = mapped_column(String(50), default=lambda: datetime.utcnow().isoformat())
    completed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


# ─── Database helpers ──────────────────────────────────────────────────────────

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


# ─── CRUD helpers ──────────────────────────────────────────────────────────────

async def db_get_tasks(status: Optional[str] = None) -> List[Dict]:
    async with AsyncSessionLocal() as session:
        stmt = select(Task)
        if status:
            stmt = stmt.where(Task.status == status)
        result = await session.execute(stmt)
        tasks = result.scalars().all()
        return [_task_to_dict(t) for t in tasks]


async def db_create_task(data: Dict) -> Dict:
    async with AsyncSessionLocal() as session:
        task = Task(**data)
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return _task_to_dict(task)


async def db_update_task(task_id: str, data: Dict) -> Optional[Dict]:
    async with AsyncSessionLocal() as session:
        data["updated_at"] = datetime.utcnow().isoformat()
        stmt = update(Task).where(Task.id == task_id).values(**data)
        await session.execute(stmt)
        await session.commit()
        result = await session.execute(select(Task).where(Task.id == task_id))
        task = result.scalar_one_or_none()
        return _task_to_dict(task) if task else None


async def db_get_events() -> List[Dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ScheduleEvent).order_by(ScheduleEvent.start_time))
        events = result.scalars().all()
        return [_event_to_dict(e) for e in events]


async def db_get_notes() -> List[Dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Note).order_by(Note.created_at.desc()))
        notes = result.scalars().all()
        return [_note_to_dict(n) for n in notes]


async def db_log_activity(data: Dict) -> Dict:
    async with AsyncSessionLocal() as session:
        activity = AgentActivity(**data)
        session.add(activity)
        await session.commit()
        return data


async def db_get_recent_activities(limit: int = 50) -> List[Dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentActivity).order_by(AgentActivity.created_at.desc()).limit(limit)
        )
        activities = result.scalars().all()
        return [_activity_to_dict(a) for a in activities]


async def db_log_email(data: Dict) -> Dict:
    async with AsyncSessionLocal() as session:
        email = EmailRecord(**data)
        session.add(email)
        await session.commit()
        return data


async def db_get_emails() -> List[Dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EmailRecord).order_by(EmailRecord.created_at.desc()).limit(20)
        )
        emails = result.scalars().all()
        return [_email_to_dict(e) for e in emails]


# ─── Serializers ──────────────────────────────────────────────────────────────

def _task_to_dict(t: Task) -> Dict:
    return {
        "id": t.id, "title": t.title, "description": t.description,
        "status": t.status, "priority": t.priority, "assignee": t.assignee,
        "project": t.project, "due_date": t.due_date, "linear_id": t.linear_id,
        "tags": json.loads(t.tags) if t.tags else [],
        "created_at": t.created_at, "updated_at": t.updated_at,
    }


def _event_to_dict(e: ScheduleEvent) -> Dict:
    return {
        "id": e.id, "title": e.title, "description": e.description,
        "start_time": e.start_time, "end_time": e.end_time,
        "attendees": json.loads(e.attendees) if e.attendees else [],
        "location": e.location, "meeting_link": e.meeting_link,
        "event_type": e.event_type, "created_at": e.created_at,
    }


def _note_to_dict(n: Note) -> Dict:
    return {
        "id": n.id, "title": n.title, "content": n.content,
        "tags": json.loads(n.tags) if n.tags else [],
        "category": n.category, "created_at": n.created_at, "updated_at": n.updated_at,
    }


def _activity_to_dict(a: AgentActivity) -> Dict:
    return {
        "id": a.id, "workflow_id": a.workflow_id, "agent_name": a.agent_name,
        "action": a.action, "status": a.status, "duration_ms": a.duration_ms,
        "details": json.loads(a.details) if a.details else {},
        "created_at": a.created_at,
    }


def _email_to_dict(e: EmailRecord) -> Dict:
    return {
        "id": e.id, "subject": e.subject, "sender": e.sender,
        "recipients": json.loads(e.recipients) if e.recipients else [],
        "body_preview": e.body_preview, "status": e.status,
        "mailgun_id": e.mailgun_id, "is_important": e.is_important,
        "created_at": e.created_at,
    }
