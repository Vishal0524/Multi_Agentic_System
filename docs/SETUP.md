# NEXUS Setup Guide

## Quick Start (Demo Mode — No API Keys Needed)

```bash
git clone https://github.com/YOUR_USERNAME/nexus-agent.git
cd nexus-agent
cp .env.example .env

# Terminal 1 — Backend
cd backend
pip install -r requirements.txt
uvicorn api.main:app --reload --port 8000

# Terminal 2 — Frontend  
cd frontend
npm install
npm run dev
```
Open **http://localhost:5173** — fully functional with mock data.

---

## Cloud Run Deployment (One Command)

```bash
# Set your real API keys (optional — demo works without them)
export GOOGLE_API_KEY=your_key_here
export MAILGUN_API_KEY=your_key_here
export MAILGUN_DOMAIN=sandboxXXX.mailgun.org
export LINEAR_API_KEY=your_key_here

bash deploy.sh
```

Your existing Cloud Run URL (`logistics-agent`) will serve NEXUS.

---

## API Key Setup (For Live Mode)

### Google API Key (Gemini)
1. Visit https://aistudio.google.com/app/apikey
2. Create key → copy to `GOOGLE_API_KEY`

### Mailgun (Sandbox — Free)
1. Sign up at https://mailgun.com (free tier)
2. Your sandbox domain is shown immediately: `sandboxXXXX.mailgun.org`
3. Get API key from Settings → API Keys
4. Sandbox mode: emails go to Mailgun logs, not real inboxes ✅

### Linear
1. Go to https://linear.app → Settings → API
2. Create Personal API Key → copy to `LINEAR_API_KEY`
3. Find Team ID: Settings → Workspace → copy team identifier

### Composio (Gmail)
1. Sign up at https://composio.dev
2. Dashboard → Connect Gmail → follow OAuth flow
3. Copy API key to `COMPOSIO_API_KEY`

---

## Architecture Notes

- **Port 8080**: Cloud Run default — Dockerfile exposes 8080
- **SQLite**: Ephemeral in Cloud Run (resets on cold start) — upgrade to Cloud SQL for persistence
- **Demo mode**: Default — no API keys required, rich mock data loaded automatically
- **SSE**: Works on Cloud Run with `--timeout=300` flag
