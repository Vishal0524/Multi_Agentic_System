# 🧠 NEXUS — Multi-Agent Productivity Assistant

> A production-grade, investor-ready demo of coordinated AI agents managing tasks, schedules, communication, and information using Google ADK, A2A Protocol, and real MCP tool integrations.

---

## 🎯 What NEXUS Does

NEXUS is a **multi-agent AI system** where a **Primary Orchestrator Agent** coordinates specialized sub-agents to complete real-world productivity workflows:

| Agent | Role | Tools |
|---|---|---|
| 🧠 **Nexus Prime** | Orchestrator — plans, delegates, synthesizes | All |
| 📬 **Hermes** | Email Intelligence Agent | Gmail MCP + Mailgun MCP |
| 📋 **Atlas** | Task & Project Agent | Linear MCP + SQLite DB |
| 📅 **Chronos** | Schedule & Time Agent | Calendar Tool + DB |
| 🔍 **Oracle** | Research & Notes Agent | Web Search + Notes DB |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  NEXUS UI (React)                    │
│          Real-time Agent Activity Feed               │
└────────────────────┬────────────────────────────────┘
                     │ REST + SSE
┌────────────────────▼────────────────────────────────┐
│              FastAPI Gateway (api/main.py)           │
│         A2A Protocol Handler + SSE Streamer          │
└────────────────────┬────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────┐
│           Nexus Prime (Orchestrator Agent)           │
│    Google ADK AgentSession + Tool Registry          │
└──┬──────────┬───────────┬──────────┬───────────────┘
   │          │           │          │
┌──▼──┐  ┌───▼──┐  ┌─────▼─┐  ┌────▼───┐
│Hermes│  │Atlas │  │Chronos│  │Oracle  │
│Email │  │Tasks │  │Sched. │  │Research│
└──────┘  └──────┘  └───────┘  └────────┘
   │          │           │          │
┌──▼──┐  ┌───▼──┐  ┌─────▼─┐  ┌────▼───┐
│Gmail │  │Linear│  │Cal MCP│  │Search  │
│MCP   │  │MCP   │  │SQLite │  │SQLite  │
│Mailg.│  │SQLite│  │       │  │        │
└──────┘  └──────┘  └───────┘  └────────┘
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- API Keys (see `.env.example`)

### 1. Clone & Install

```bash
mkdir nexus-agent
git clone https://github.com/Vishal0524/Multi_Agentic_System.git
cd nexus-agent

# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd ../frontend
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
# Fill in your API keys (see docs/SETUP.md)
```

### 3. Run Demo Mode (No real API keys needed!)

```bash
# Terminal 1 — Backend
cd backend
python -m uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend
cd frontend
npm run dev
```

Visit **http://localhost:5173** — NEXUS loads agent workflows.

---

## 🔑 API Keys Required (for live mode)

| Key | Where to get |
|---|---|
| `GOOGLE_API_KEY` | [Google AI Studio](https://aistudio.google.com) |
| `COMPOSIO_API_KEY` | [Composio Dashboard](https://composio.dev) |
| `MAILGUN_API_KEY` | [Mailgun Console](https://mailgun.com) |
| `MAILGUN_DOMAIN` | Your Mailgun sandbox domain |
| `LINEAR_API_KEY` | [Linear Settings → API](https://linear.app) |

---

## 📁 Project Structure

```
nexus-agent/
├── backend/
│   ├── agents/          # ADK Agent definitions
│   │   ├── orchestrator.py   # Nexus Prime
│   │   ├── hermes.py         # Email agent
│   │   ├── atlas.py          # Task agent
│   │   ├── chronos.py        # Schedule agent
│   │   └── oracle.py         # Research agent
│   ├── tools/           # MCP Tool wrappers
│   │   ├── gmail_tool.py
│   │   ├── mailgun_tool.py
│   │   ├── linear_tool.py
│   │   └── calendar_tool.py
│   ├── database/        # SQLite + schema
│   │   ├── db.py
│   │   ├── schema.sql
│   │   └── seed_data.py    
│   ├── workflows/       # Multi-step workflow definitions
│   │   ├── morning_brief.py
│   │   ├── project_kickoff.py
│   │   └── weekly_review.py
│   ├── api/
│   │   └── main.py      # FastAPI app + SSE streaming
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/  # React UI components
│   │   ├── pages/       # App pages
│   │   └── hooks/       # Custom hooks
│   └── package.json
├── docs/
│   ├── SETUP.md
│   └── USERMANUAL.md
└── .env.example
```

---

## 🎬 Workflows

| Workflow | Trigger Phrase | Agents Involved |
|---|---|---|
| **Morning Brief** | "Give me my morning brief" | All 4 agents |
| **Project Kickoff** | "Kick off the Alpha project" | Atlas + Hermes + Chronos |
| **Weekly Review** | "Run weekly review" | All agents + Mailgun report |
| **Quick Task** | "Add task: ..." | Atlas → Linear |
| **Send Report** | "Email team the status" | Hermes → Mailgun |

---

## 📜 License

MIT — Built for demonstration and educational purposes.
