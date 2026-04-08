# 🤖 Multi-Agent Productivity Assistant

> **A production-grade multi-agent AI system** built with Google ADK Framework, A2A Protocol, and Agentic Workflows. Coordinates specialized AI agents for task management, calendar scheduling, email communication, and knowledge management.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![ADK](https://img.shields.io/badge/Google_ADK-2.0-green)
![A2A](https://img.shields.io/badge/A2A_Protocol-1.0-purple)
![License](https://img.shields.io/badge/License-MIT-yellow)

---
## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Gemini API Key ([Get one here](https://aistudio.google.com/app/apikey))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/Multi_Agentic_System.git
cd Multi_Agentic_System

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# 5. Run the application
python server.py
```

### Open the UI
Navigate to **http://localhost:8000** in your browser.

The database is automatically seeded with demo data on first run.

---

## 🤖 Agent System

| Agent | Role | Tools |
|-------|------|-------|
| **Orchestrator** | Root coordinator — routes requests to sub-agents | N/A (delegates) |
| **Task Manager** | Project task management | `list_tasks`, `create_task`, `update_task`, `get_task_summary` |
| **Calendar Agent** | Schedule management | `list_events`, `create_event`, `check_conflicts`, `get_today_schedule` |
| **Email Agent** | Email communication | `send_email`, `draft_email`, `list_emails` |
| **Notes Agent** | Knowledge management | `create_note`, `list_notes`, `search_notes`, `summarize_notes` |

## 🔗 A2A Protocol

The system exposes an A2A-compatible server on port 8001:

```bash
# Start A2A server (separate terminal)
python a2a_server.py

# Agent Card Discovery
curl http://localhost:8001/.well-known/agent.json

# Send a task via A2A
curl -X POST http://localhost:8001/tasks/send \
  -H "Content-Type: application/json" \
  -d '{"message": {"text": "List all critical tasks"}}'
```

## 🛠️ Tech Stack

- **AI Framework**: Google ADK (Agent Development Kit)
- **LLM**: Gemini 2.0 Flash
- **Protocol**: A2A (Agent-to-Agent)
- **Backend**: FastAPI + Uvicorn
- **Database**: SQLite
- **Email**: Mailgun Sandbox (test mode)
- **Frontend**: Vanilla JS + CSS (custom premium UI)

## 📁 Project Structure

```
Multi_Agentic_System/
├── agents/
│   ├── orchestrator/      # Root agent (coordinates all sub-agents)
│   ├── task_manager/      # Task CRUD agent
│   ├── calendar_agent/    # Calendar & scheduling agent
│   ├── email_agent/       # Email via Mailgun sandbox
│   └── notes_agent/       # Notes & knowledge agent
├── database/
│   ├── db.py              # SQLite CRUD operations
│   └── seed_data.py       # Mock data seeder
├── static/
│   ├── index.html         # Premium SPA
│   ├── styles.css         # Dark theme + glassmorphism
│   └── app.js             # Frontend logic
├── server.py              # FastAPI main server (port 8000)
├── a2a_server.py          # A2A protocol server (port 8001)
├── requirements.txt
├── .env.example
├── usermanual.md          # Demo scenarios & mock flow guide
└── README.md
```

## 📝 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/chat` | Send message to orchestrator agent |
| `GET` | `/api/dashboard` | Aggregated dashboard data |
| `GET` | `/api/tasks` | List all tasks |
| `GET` | `/api/events` | List all events |
| `GET` | `/api/emails` | List all emails |
| `GET` | `/api/notes` | List all notes |
| `POST` | `/api/seed` | Reset demo data |

## 📄 License

MIT License — See [LICENSE](LICENSE) for details.
