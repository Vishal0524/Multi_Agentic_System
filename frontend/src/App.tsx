import { useState, useEffect, useRef, useCallback } from 'react'
import {
  LayoutDashboard, MessageSquare, CheckSquare, Calendar, Mail, FileText,
  Zap, Bot, RefreshCw, Send, Plus, ChevronRight, Clock, User, Tag,
  AlertTriangle, CheckCircle, Loader, Wifi, WifiOff, X, ExternalLink,
  BarChart2, Activity, ArrowUpRight, Inbox, BookOpen, Settings, Play
} from 'lucide-react'
import './App.css'

// ─── Types ─────────────────────────────────────────────────────────────────────
interface Task { id: string; title: string; status: string; priority: string; assignee?: string; project?: string; due_date?: string; linear_id?: string; tags?: string[] }
interface Event { id: string; title: string; start_time: string; end_time: string; attendees?: string[]; location?: string; event_type?: string }
interface Email { id: string; subject: string; sender: string; recipients?: string[]; body_preview?: string; status: string; is_important?: boolean; created_at: string }
interface Note { id: string; title: string; content: string; tags?: string[]; category?: string; created_at: string }
interface AgentActivity { id: string; agent_name: string; action: string; status: string; duration_ms?: number; created_at: string; details?: Record<string, unknown> }
interface StreamEvent { type: string; agent?: string; data?: Record<string, unknown>; workflow_id?: string; timestamp?: string }

const API = import.meta.env.VITE_API_BASE_URL || ''

async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!res.ok) throw new Error(`API error ${res.status}`)
  return res.json()
}

// ─── Agent config ────────────────────────────────────────────────────────────
const AGENTS = [
  { name: 'Nexus Prime', emoji: '🧠', role: 'Orchestrator', color: '#3b82f6', key: 'nexus_prime' },
  { name: 'Hermes', emoji: '📬', role: 'Email Agent', color: '#10b981', key: 'hermes' },
  { name: 'Atlas', emoji: '📋', role: 'Task Agent', color: '#f59e0b', key: 'atlas' },
  { name: 'Chronos', emoji: '📅', role: 'Schedule Agent', color: '#8b5cf6', key: 'chronos' },
  { name: 'Oracle', emoji: '🔍', role: 'Research Agent', color: '#06b6d4', key: 'oracle' },
]

const AGENT_COLOR: Record<string, string> = {
  'Nexus Prime': '#3b82f6', 'Hermes': '#10b981', 'Atlas': '#f59e0b',
  'Chronos': '#8b5cf6', 'Oracle': '#06b6d4',
}

const QUICK_COMMANDS = [
  { label: 'Morning Brief', icon: '☀️', cmd: 'Give me my morning brief', color: '#3b82f6' },
  { label: 'Weekly Review', icon: '📊', cmd: 'Run weekly review', color: '#8b5cf6' },
  { label: 'Project Kickoff', icon: '🚀', cmd: 'Kick off the Alpha Platform project', color: '#10b981' },
  { label: 'Send Report', icon: '📤', cmd: 'Email team the status update', color: '#f59e0b' },
]

// ─── Helpers ─────────────────────────────────────────────────────────────────
function fmtTime(iso: string) {
  try { return new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) } catch { return iso }
}
function fmtDate(iso: string) {
  try { return new Date(iso).toLocaleDateString([], { month: 'short', day: 'numeric' }) } catch { return iso }
}
function fmtRelative(iso: string) {
  try {
    const diff = Date.now() - new Date(iso).getTime()
    if (diff < 60000) return 'just now'
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`
    return fmtDate(iso)
  } catch { return iso }
}

const STATUS_COLOR: Record<string, string> = {
  todo: '#7a95b8', in_progress: '#3b82f6', done: '#10b981', cancelled: '#ef4444'
}
const PRIORITY_COLOR: Record<string, string> = {
  urgent: '#ef4444', high: '#f59e0b', medium: '#3b82f6', low: '#7a95b8'
}

// ─── Components ───────────────────────────────────────────────────────────────

function StatusBadge({ status }: { status: string }) {
  const label = status.replace('_', ' ').toUpperCase()
  return (
    <span className="badge" style={{ background: `${STATUS_COLOR[status] || '#7a95b8'}22`, color: STATUS_COLOR[status] || '#7a95b8', border: `1px solid ${STATUS_COLOR[status] || '#7a95b8'}44` }}>
      {label}
    </span>
  )
}

function PriorityDot({ priority }: { priority: string }) {
  return <span className="priority-dot" style={{ background: PRIORITY_COLOR[priority] || '#7a95b8' }} title={priority} />
}

function AgentPill({ name }: { name: string }) {
  const color = AGENT_COLOR[name] || '#7a95b8'
  const ag = AGENTS.find(a => a.name === name)
  return (
    <span className="agent-pill" style={{ color, border: `1px solid ${color}33`, background: `${color}11` }}>
      {ag?.emoji} {name}
    </span>
  )
}

function Spinner() {
  return <div className="spinner" />
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [page, setPage] = useState<'dashboard' | 'chat' | 'tasks' | 'calendar' | 'email' | 'notes' | 'activity'>('dashboard')
  const [tasks, setTasks] = useState<Task[]>([])
  const [events, setEvents] = useState<Event[]>([])
  const [emails, setEmails] = useState<Email[]>([])
  const [notes, setNotes] = useState<Note[]>([])
  const [activity, setActivity] = useState<AgentActivity[]>([])
  const [loading, setLoading] = useState(true)
  const [connected, setConnected] = useState(false)
  const [streamEvents, setStreamEvents] = useState<StreamEvent[]>([])
  const [agentStates, setAgentStates] = useState<Record<string, 'idle' | 'running' | 'done'>>({})
  const [activeWorkflow, setActiveWorkflow] = useState<string | null>(null)
  const [chatMessages, setChatMessages] = useState<{ role: 'user' | 'agent'; content: string; agent?: string; ts: string }[]>([
    { role: 'agent', content: 'NEXUS online. I have 4 agents ready — Hermes (Email), Atlas (Tasks), Chronos (Schedule), and Oracle (Research). What would you like to accomplish?', agent: 'Nexus Prime', ts: new Date().toISOString() }
  ])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const [newTaskTitle, setNewTaskTitle] = useState('')
  const [showNewTask, setShowNewTask] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const activityEndRef = useRef<HTMLDivElement>(null)

  // ── Data Loading ──────────────────────────────────────────────────────────
  const loadAll = useCallback(async () => {
    setLoading(true)
    try {
      const [t, s, e, n, a] = await Promise.all([
        api<{ tasks: Task[] }>('/api/tasks'),
        api<{ events: Event[] }>('/api/schedule'),
        api<{ emails: Email[] }>('/api/emails'),
        api<{ notes: Note[] }>('/api/notes'),
        api<{ activities: AgentActivity[] }>('/api/activity?limit=30'),
      ])
      setTasks(t.tasks || [])
      setEvents(s.events || [])
      setEmails(e.emails || [])
      setNotes(n.notes || [])
      setActivity(a.activities || [])
    } catch (err) {
      console.error('Load error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // ── SSE Connection ────────────────────────────────────────────────────────
  useEffect(() => {
    const connect = () => {
      const es = new EventSource(`${API}/api/stream`)
      eventSourceRef.current = es
      es.onopen = () => setConnected(true)
      es.onerror = () => { setConnected(false); es.close(); setTimeout(connect, 3000) }
      es.onmessage = (ev) => {
        try {
          const event: StreamEvent = JSON.parse(ev.data)
          if (event.type === 'heartbeat' || event.type === 'connected') return
          setStreamEvents(prev => [event, ...prev].slice(0, 100))

          // Update agent states
          if (event.agent) {
            if (event.type === 'agent_start' || event.type === 'tool_call') {
              setAgentStates(prev => ({ ...prev, [event.agent!]: 'running' }))
            } else if (event.type === 'agent_complete') {
              setAgentStates(prev => ({ ...prev, [event.agent!]: 'done' }))
              setTimeout(() => setAgentStates(prev => ({ ...prev, [event.agent!]: 'idle' })), 2000)
            } else if (event.type === 'workflow_complete') {
              setAgentStates({})
              setActiveWorkflow(null)
              // Refresh data after workflow
              loadAll()
              // Add agent response to chat
              const summary = (event.data?.summary as string) || (event.data?.action as string) || 'Workflow complete.'
              setChatMessages(prev => [...prev, {
                role: 'agent', content: summary, agent: 'Nexus Prime', ts: new Date().toISOString()
              }])
              setChatLoading(false)
            }
          }
        } catch { /* skip malformed */ }
      }
    }
    connect()
    return () => eventSourceRef.current?.close()
  }, [loadAll])

  useEffect(() => { loadAll() }, [loadAll])
  useEffect(() => { chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [chatMessages])

  // ── Chat Send ─────────────────────────────────────────────────────────────
  const sendChat = async (input?: string) => {
    const text = (input || chatInput).trim()
    if (!text || chatLoading) return
    setChatInput('')
    setChatMessages(prev => [...prev, { role: 'user', content: text, ts: new Date().toISOString() }])
    setChatLoading(true)
    try {
      const res = await api<{ workflow_id: string }>('/api/orchestrate', {
        method: 'POST', body: JSON.stringify({ user_input: text })
      })
      setActiveWorkflow(res.workflow_id)
    } catch {
      setChatMessages(prev => [...prev, { role: 'agent', content: 'Connection error — is the backend running?', agent: 'System', ts: new Date().toISOString() }])
      setChatLoading(false)
    }
  }

  const createTask = async () => {
    if (!newTaskTitle.trim()) return
    try {
      await api('/api/tasks', { method: 'POST', body: JSON.stringify({ title: newTaskTitle, priority: 'medium', project: 'General' }) })
      setNewTaskTitle(''); setShowNewTask(false)
      loadAll()
    } catch { alert('Failed to create task') }
  }

  // ── Stats ─────────────────────────────────────────────────────────────────
  const urgentTasks = tasks.filter(t => t.priority === 'urgent' || t.priority === 'high')
  const inProgressTasks = tasks.filter(t => t.status === 'in_progress')
  const importantEmails = emails.filter(e => e.is_important)
  const todayEvents = events.filter(e => e.start_time?.startsWith(new Date().toISOString().split('T')[0]))

  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'chat', label: 'Agent Chat', icon: MessageSquare },
  ]
  const agentNavItems = [
    { id: 'tasks', label: 'Tasks', icon: CheckSquare, count: tasks.length },
    { id: 'calendar', label: 'Calendar', icon: Calendar, count: events.length },
    { id: 'email', label: 'Email', icon: Mail, count: emails.length },
    { id: 'notes', label: 'Notes', icon: FileText, count: notes.length },
  ]
  const systemNavItems = [
    { id: 'activity', label: 'Activity Feed', icon: Activity },
  ]

  return (
    <div className="app-shell">
      {/* ── Sidebar ─────────────────────────────────────────────────────── */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-icon">
            <Bot size={20} color="#3b82f6" />
          </div>
          <div>
            <div className="logo-name">Nexus AI</div>
            <div className="logo-sub">PRODUCTIVITY ASSISTANT</div>
          </div>
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">MAIN</div>
          {navItems.map(item => (
            <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => setPage(item.id as typeof page)}>
              <item.icon size={16} />
              <span>{item.label}</span>
            </button>
          ))}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">AGENTS</div>
          {agentNavItems.map(item => (
            <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => setPage(item.id as typeof page)}>
              <item.icon size={16} />
              <span>{item.label}</span>
              {item.count > 0 && <span className="nav-badge">{item.count}</span>}
            </button>
          ))}
        </div>

        <div className="sidebar-section">
          <div className="sidebar-section-label">SYSTEM</div>
          <button className={`nav-item ${page === 'activity' ? 'active' : ''}`} onClick={() => setPage('activity')}>
            <Zap size={16} />
            <span>Activity Feed</span>
          </button>
        </div>

        {/* Agent Status */}
        <div className="sidebar-agents">
          <div className="agents-online">
            <span className="online-dot" />
            <span>{AGENTS.length - 1} Agents Online</span>
          </div>
          {AGENTS.slice(1).map(ag => (
            <div key={ag.key} className="sidebar-agent-row">
              <span className="sidebar-agent-emoji">{ag.emoji}</span>
              <span className="sidebar-agent-name">{ag.name}</span>
              <span className={`sidebar-agent-state ${agentStates[ag.name] || 'idle'}`}>
                {agentStates[ag.name] === 'running' ? <Spinner /> : agentStates[ag.name] === 'done' ? '✓' : ''}
              </span>
            </div>
          ))}
        </div>
      </aside>

      {/* ── Main Content ─────────────────────────────────────────────────── */}
      <main className="main-content">
        {/* Header */}
        <header className="top-bar">
          <div className="page-title">
            {page === 'dashboard' && 'Dashboard'}
            {page === 'chat' && 'Agent Chat'}
            {page === 'tasks' && 'Tasks'}
            {page === 'calendar' && 'Calendar'}
            {page === 'email' && 'Email'}
            {page === 'notes' && 'Notes'}
            {page === 'activity' && 'Activity Feed'}
          </div>
          <div className="top-bar-actions">
            <div className={`connection-pill ${connected ? 'connected' : 'disconnected'}`}>
              {connected ? <Wifi size={12} /> : <WifiOff size={12} />}
              {connected ? 'Live' : 'Connecting...'}
            </div>
            <button className="btn-outline" onClick={loadAll}><RefreshCw size={13} /> Refresh</button>
            <button className="btn-primary" onClick={() => { setPage('chat'); setChatInput('Give me my morning brief') }}>
              <Zap size={13} /> Quick Brief
            </button>
          </div>
        </header>

        <div className="page-body">
          {loading && page === 'dashboard' ? (
            <div className="loading-state"><Spinner /><span>Loading NEXUS data…</span></div>
          ) : (
            <>
              {page === 'dashboard' && <DashboardPage tasks={tasks} events={events} emails={emails} notes={notes} urgentTasks={urgentTasks} inProgressTasks={inProgressTasks} importantEmails={importantEmails} todayEvents={todayEvents} onNavigate={setPage} />}
              {page === 'chat' && <ChatPage messages={chatMessages} input={chatInput} loading={chatLoading} streamEvents={streamEvents} agentStates={agentStates} activeWorkflow={activeWorkflow} onInputChange={setChatInput} onSend={sendChat} chatEndRef={chatEndRef} />}
              {page === 'tasks' && <TasksPage tasks={tasks} showNew={showNewTask} newTitle={newTaskTitle} onToggleNew={() => setShowNewTask(v => !v)} onNewTitleChange={setNewTaskTitle} onCreateTask={createTask} onRefresh={loadAll} />}
              {page === 'calendar' && <CalendarPage events={events} />}
              {page === 'email' && <EmailPage emails={emails} />}
              {page === 'notes' && <NotesPage notes={notes} />}
              {page === 'activity' && <ActivityPage activities={activity} streamEvents={streamEvents} onRefresh={loadAll} />}
            </>
          )}
        </div>
      </main>
    </div>
  )
}

// ─── Dashboard Page ───────────────────────────────────────────────────────────
function DashboardPage({ tasks, events, emails, notes, urgentTasks, inProgressTasks, importantEmails, todayEvents, onNavigate }: {
  tasks: Task[]; events: Event[]; emails: Email[]; notes: Note[];
  urgentTasks: Task[]; inProgressTasks: Task[]; importantEmails: Email[]; todayEvents: Event[];
  onNavigate: (p: 'dashboard' | 'chat' | 'tasks' | 'calendar' | 'email' | 'notes' | 'activity') => void
}) {
  return (
    <div className="dashboard">
      {/* Stat Cards */}
      <div className="stat-grid">
        <StatCard icon="📋" value={tasks.length} label="TOTAL TASKS" sub={`▲ ${inProgressTasks.length} in progress`} subColor="#3b82f6" topColor="#3b82f6" onClick={() => onNavigate('tasks')} />
        <StatCard icon="📅" value={events.length} label="EVENTS" sub={`📅 ${todayEvents.length} today`} subColor="#8b5cf6" topColor="#8b5cf6" onClick={() => onNavigate('calendar')} />
        <StatCard icon="📬" value={emails.length} label="EMAILS" sub={importantEmails.length > 0 ? `🔴 ${importantEmails.length} important` : '✅ All clear'} subColor={importantEmails.length > 0 ? '#ef4444' : '#10b981'} topColor="#10b981" onClick={() => onNavigate('email')} />
        <StatCard icon="📝" value={notes.length} label="NOTES" sub={urgentTasks.length > 0 ? `🔴 ${urgentTasks.length} critical tasks` : '✅ No blockers'} subColor={urgentTasks.length > 0 ? '#ef4444' : '#10b981'} topColor="#f59e0b" onClick={() => onNavigate('notes')} />
      </div>

      {/* Quick Workflows */}
      <div className="quick-workflows">
        {QUICK_COMMANDS.map(qc => (
          <button key={qc.cmd} className="workflow-btn" onClick={() => onNavigate('chat')} style={{ borderColor: `${qc.color}44` }}>
            <span className="workflow-icon" style={{ background: `${qc.color}22` }}>{qc.icon}</span>
            <span>{qc.label}</span>
            <Play size={12} style={{ color: qc.color, marginLeft: 'auto' }} />
          </button>
        ))}
      </div>

      {/* Main Grid */}
      <div className="dashboard-grid">
        {/* Recent Tasks */}
        <div className="panel">
          <div className="panel-header">
            <span>📋 Recent Tasks</span>
            <button className="panel-link" onClick={() => onNavigate('tasks')}>View all <ChevronRight size={12} /></button>
          </div>
          <div className="panel-body">
            {tasks.slice(0, 5).map(task => (
              <div key={task.id} className="list-row task-row">
                <PriorityDot priority={task.priority} />
                <div className="list-row-main">
                  <div className="list-row-title">{task.title}</div>
                  <div className="list-row-meta">
                    {task.assignee && <><User size={10} /> {task.assignee}</>}
                    {task.due_date && <><Clock size={10} /> {fmtDate(task.due_date)}</>}
                    {task.linear_id && <span className="linear-tag">{task.linear_id}</span>}
                  </div>
                </div>
                <StatusBadge status={task.status} />
              </div>
            ))}
          </div>
        </div>

        {/* Upcoming Events */}
        <div className="panel">
          <div className="panel-header">
            <span>📅 Upcoming Events</span>
            <button className="panel-link" onClick={() => onNavigate('calendar')}>View all <ChevronRight size={12} /></button>
          </div>
          <div className="panel-body">
            {events.slice(0, 5).map(ev => (
              <div key={ev.id} className="list-row event-row">
                <div className="event-time-col">
                  <div className="event-time">{fmtTime(ev.start_time)}</div>
                  <div className="event-dur">
                    {Math.round((new Date(ev.end_time).getTime() - new Date(ev.start_time).getTime()) / 60000)}min
                  </div>
                </div>
                <div className="list-row-main">
                  <div className="list-row-title">{ev.title}</div>
                  {ev.location && <div className="list-row-meta"><span className="location-dot">📍</span>{ev.location}</div>}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Emails */}
        <div className="panel">
          <div className="panel-header">
            <span>📬 Recent Emails</span>
            <button className="panel-link" onClick={() => onNavigate('email')}>View all <ChevronRight size={12} /></button>
          </div>
          <div className="panel-body">
            {emails.slice(0, 4).map(em => (
              <div key={em.id} className={`list-row email-row ${em.is_important ? 'important' : ''}`}>
                {em.is_important && <span className="important-dot" />}
                <div className="list-row-main">
                  <div className="list-row-title">{em.subject}</div>
                  <div className="list-row-meta">
                    <User size={10} /> {em.sender}
                    <span className={`email-status-tag ${em.status}`}>{em.status.toUpperCase()}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Notes */}
        <div className="panel">
          <div className="panel-header">
            <span>📝 Recent Notes</span>
            <button className="panel-link" onClick={() => onNavigate('notes')}>View all <ChevronRight size={12} /></button>
          </div>
          <div className="panel-body">
            {notes.slice(0, 4).map(note => (
              <div key={note.id} className="list-row note-row">
                <div className="list-row-main">
                  <div className="list-row-title">{note.title}</div>
                  {note.category && (
                    <div className="list-row-meta">
                      <span className="note-category">{note.category}</span>
                      {note.tags?.slice(0, 3).map(tag => (
                        <span key={tag} className="note-tag">#{tag}</span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, value, label, sub, subColor, topColor, onClick }: {
  icon: string; value: number; label: string; sub: string; subColor: string; topColor: string; onClick?: () => void
}) {
  return (
    <div className="stat-card" onClick={onClick} style={{ cursor: onClick ? 'pointer' : 'default' }}>
      <div className="stat-card-top" style={{ background: topColor }} />
      <div className="stat-card-body">
        <div className="stat-icon">{icon}</div>
        <div className="stat-value">{value}</div>
        <div className="stat-label">{label}</div>
        <div className="stat-sub" style={{ color: subColor }}>{sub}</div>
      </div>
    </div>
  )
}

// ─── Chat Page ────────────────────────────────────────────────────────────────
function ChatPage({ messages, input, loading, streamEvents, agentStates, activeWorkflow, onInputChange, onSend, chatEndRef }: {
  messages: { role: 'user' | 'agent'; content: string; agent?: string; ts: string }[]
  input: string; loading: boolean; streamEvents: StreamEvent[]; agentStates: Record<string, string>
  activeWorkflow: string | null; onInputChange: (v: string) => void; onSend: (v?: string) => void
  chatEndRef: React.RefObject<HTMLDivElement>
}) {
  return (
    <div className="chat-layout">
      {/* Chat main */}
      <div className="chat-main">
        <div className="chat-messages">
          {messages.map((msg, i) => (
            <div key={i} className={`chat-msg ${msg.role}`}>
              {msg.role === 'agent' && (
                <div className="chat-msg-avatar" style={{ background: `${AGENT_COLOR[msg.agent || ''] || '#3b82f6'}22`, border: `1px solid ${AGENT_COLOR[msg.agent || ''] || '#3b82f6'}44` }}>
                  {AGENTS.find(a => a.name === msg.agent)?.emoji || '🧠'}
                </div>
              )}
              <div className="chat-msg-body">
                {msg.role === 'agent' && <div className="chat-msg-agent">{msg.agent || 'Nexus Prime'}</div>}
                <div className="chat-bubble">{msg.content}</div>
                <div className="chat-ts">{fmtRelative(msg.ts)}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-msg agent">
              <div className="chat-msg-avatar" style={{ background: '#3b82f622', border: '1px solid #3b82f644' }}>🧠</div>
              <div className="chat-msg-body">
                <div className="chat-msg-agent">Nexus Prime</div>
                <div className="chat-bubble typing">
                  <span className="dot" /><span className="dot" /><span className="dot" />
                </div>
              </div>
            </div>
          )}
          <div ref={chatEndRef} />
        </div>

        {/* Quick commands */}
        <div className="quick-cmds">
          {QUICK_COMMANDS.map(qc => (
            <button key={qc.cmd} className="quick-cmd-btn" onClick={() => onSend(qc.cmd)} disabled={loading}>
              {qc.icon} {qc.label}
            </button>
          ))}
        </div>

        {/* Input */}
        <div className="chat-input-area">
          <input
            className="chat-input"
            placeholder="Ask NEXUS anything — 'morning brief', 'create task: fix login bug', 'run weekly review'…"
            value={input}
            onChange={e => onInputChange(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && onSend()}
            disabled={loading}
          />
          <button className="chat-send" onClick={() => onSend()} disabled={loading || !input.trim()}>
            {loading ? <Spinner /> : <Send size={16} />}
          </button>
        </div>
      </div>

      {/* Agent Activity Panel */}
      <div className="agent-panel">
        <div className="agent-panel-header">
          <Activity size={14} />
          <span>Agent Activity</span>
          {activeWorkflow && <span className="workflow-badge">LIVE</span>}
        </div>

        {/* Agent Status Rows */}
        <div className="agent-status-list">
          {AGENTS.map(ag => (
            <div key={ag.key} className={`agent-status-row ${agentStates[ag.name] || 'idle'}`}>
              <span className="agent-status-emoji">{ag.emoji}</span>
              <div className="agent-status-info">
                <div className="agent-status-name">{ag.name}</div>
                <div className="agent-status-role">{ag.role}</div>
              </div>
              <div className="agent-state-indicator">
                {agentStates[ag.name] === 'running' && <Spinner />}
                {agentStates[ag.name] === 'done' && <CheckCircle size={12} color="#10b981" />}
                {(!agentStates[ag.name] || agentStates[ag.name] === 'idle') && <span className="idle-dot" />}
              </div>
            </div>
          ))}
        </div>

        <div className="agent-panel-divider" />

        {/* Stream Events */}
        <div className="stream-events">
          <div className="stream-events-label">Live Events</div>
          {streamEvents.length === 0 && <div className="stream-empty">Waiting for agent activity…</div>}
          {streamEvents.slice(0, 15).map((ev, i) => (
            <div key={i} className="stream-event animate-stream">
              {ev.agent && <AgentPill name={ev.agent} />}
              <div className="stream-event-action">{(ev.data?.action as string) || ev.type}</div>
              {ev.data?.tool && <span className="tool-tag">🔧 {ev.data.tool as string}</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ─── Tasks Page ───────────────────────────────────────────────────────────────
function TasksPage({ tasks, showNew, newTitle, onToggleNew, onNewTitleChange, onCreateTask, onRefresh }: {
  tasks: Task[]; showNew: boolean; newTitle: string;
  onToggleNew: () => void; onNewTitleChange: (v: string) => void; onCreateTask: () => void; onRefresh: () => void
}) {
  const [filter, setFilter] = useState<string>('all')
  const filtered = filter === 'all' ? tasks : tasks.filter(t => t.status === filter)

  return (
    <div className="full-page">
      <div className="page-toolbar">
        <div className="filter-tabs">
          {['all', 'todo', 'in_progress', 'done'].map(s => (
            <button key={s} className={`filter-tab ${filter === s ? 'active' : ''}`} onClick={() => setFilter(s)}>
              {s === 'all' ? 'All' : s.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}
              <span className="filter-count">{s === 'all' ? tasks.length : tasks.filter(t => t.status === s).length}</span>
            </button>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="btn-outline" onClick={onRefresh}><RefreshCw size={13} /></button>
          <button className="btn-primary" onClick={onToggleNew}><Plus size={13} /> New Task</button>
        </div>
      </div>

      {showNew && (
        <div className="new-task-bar animate-fade-in">
          <input className="new-task-input" placeholder="Task title…" value={newTitle} onChange={e => onNewTitleChange(e.target.value)} onKeyDown={e => e.key === 'Enter' && onCreateTask()} autoFocus />
          <button className="btn-primary" onClick={onCreateTask}>Create → Linear</button>
          <button className="btn-ghost" onClick={onToggleNew}><X size={14} /></button>
        </div>
      )}

      <div className="task-table">
        <div className="task-table-head">
          <span>Task</span><span>Status</span><span>Priority</span><span>Assignee</span><span>Due</span><span>Linear</span>
        </div>
        {filtered.map(task => (
          <div key={task.id} className="task-table-row animate-fade-in">
            <div className="task-title-cell">
              <PriorityDot priority={task.priority} />
              <div>
                <div className="task-title">{task.title}</div>
                {task.project && <div className="task-project">{task.project}</div>}
              </div>
            </div>
            <StatusBadge status={task.status} />
            <span className="priority-label" style={{ color: PRIORITY_COLOR[task.priority] }}>{task.priority}</span>
            <span className="assignee-cell">{task.assignee ? <><User size={11} />{task.assignee}</> : '—'}</span>
            <span className="due-cell">{task.due_date ? fmtDate(task.due_date) : '—'}</span>
            <span className="linear-cell">{task.linear_id ? <span className="linear-link">{task.linear_id}</span> : '—'}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Calendar Page ────────────────────────────────────────────────────────────
function CalendarPage({ events }: { events: Event[] }) {
  return (
    <div className="full-page">
      <div className="events-list">
        {events.map(ev => (
          <div key={ev.id} className="event-card animate-fade-in">
            <div className="event-card-time">
              <div className="event-card-hour">{fmtTime(ev.start_time)}</div>
              <div className="event-card-date">{fmtDate(ev.start_time)}</div>
            </div>
            <div className="event-card-body">
              <div className="event-card-title">{ev.title}</div>
              {ev.description && <div className="event-card-desc">{ev.description.slice(0, 120)}{ev.description.length > 120 ? '…' : ''}</div>}
              <div className="event-card-meta">
                {ev.location && <span><span className="meta-icon">📍</span>{ev.location}</span>}
                {ev.meeting_link && <a href={ev.meeting_link} target="_blank" rel="noreferrer" className="meeting-link"><ExternalLink size={11} /> Join Meeting</a>}
                {ev.attendees && ev.attendees.length > 0 && (
                  <span><User size={11} /> {ev.attendees.slice(0, 2).join(', ')}{ev.attendees.length > 2 ? ` +${ev.attendees.length - 2}` : ''}</span>
                )}
              </div>
            </div>
            <div className="event-type-tag">{ev.event_type || 'meeting'}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

// ─── Email Page ───────────────────────────────────────────────────────────────
function EmailPage({ emails }: { emails: Email[] }) {
  const [selected, setSelected] = useState<Email | null>(null)
  return (
    <div className="email-layout">
      <div className="email-list">
        {emails.map(em => (
          <div key={em.id} className={`email-item ${em.is_important ? 'important' : ''} ${selected?.id === em.id ? 'selected' : ''}`} onClick={() => setSelected(em)}>
            {em.is_important && <div className="email-important-bar" />}
            <div className="email-item-body">
              <div className="email-item-header">
                <span className="email-from">{em.sender}</span>
                <span className={`email-status ${em.status}`}>{em.status.toUpperCase()}</span>
              </div>
              <div className="email-item-subject">{em.subject}</div>
              {em.body_preview && <div className="email-item-preview">{em.body_preview.slice(0, 100)}…</div>}
              <div className="email-item-time">{fmtRelative(em.created_at)}</div>
            </div>
          </div>
        ))}
      </div>
      <div className="email-detail">
        {selected ? (
          <div className="email-detail-body animate-fade-in">
            <div className="email-detail-subject">{selected.subject}</div>
            <div className="email-detail-meta">
              <span>From: <strong>{selected.sender}</strong></span>
              {selected.is_important && <span className="important-chip">⭐ Important</span>}
            </div>
            <div className="email-detail-content">{selected.body_preview || 'No preview available.'}</div>
          </div>
        ) : (
          <div className="email-empty"><Inbox size={40} opacity={0.3} /><p>Select an email to read</p></div>
        )}
      </div>
    </div>
  )
}

// ─── Notes Page ───────────────────────────────────────────────────────────────
function NotesPage({ notes }: { notes: Note[] }) {
  const [selected, setSelected] = useState<Note | null>(notes[0] || null)
  return (
    <div className="notes-layout">
      <div className="notes-list">
        {notes.map(note => (
          <div key={note.id} className={`note-item ${selected?.id === note.id ? 'selected' : ''}`} onClick={() => setSelected(note)}>
            <div className="note-item-title">{note.title}</div>
            {note.category && <span className="note-category-tag">{note.category}</span>}
            <div className="note-item-tags">{note.tags?.slice(0, 3).map(t => <span key={t} className="note-tag">#{t}</span>)}</div>
            <div className="note-item-date">{fmtRelative(note.created_at)}</div>
          </div>
        ))}
      </div>
      <div className="note-detail">
        {selected ? (
          <div className="note-detail-body animate-fade-in">
            <div className="note-detail-title">{selected.title}</div>
            <div className="note-detail-meta">
              {selected.category && <span className="note-category-tag">{selected.category}</span>}
              {selected.tags?.map(t => <span key={t} className="note-tag">#{t}</span>)}
            </div>
            <pre className="note-detail-content">{selected.content}</pre>
          </div>
        ) : <div className="email-empty"><BookOpen size={40} opacity={0.3} /><p>Select a note</p></div>}
      </div>
    </div>
  )
}

// ─── Activity Page ────────────────────────────────────────────────────────────
function ActivityPage({ activities, streamEvents, onRefresh }: { activities: AgentActivity[]; streamEvents: StreamEvent[]; onRefresh: () => void }) {
  return (
    <div className="full-page">
      <div className="page-toolbar">
        <span style={{ color: 'var(--text-secondary)', fontSize: 13 }}>{activities.length} logged actions</span>
        <button className="btn-outline" onClick={onRefresh}><RefreshCw size={13} /> Refresh</button>
      </div>

      {streamEvents.length > 0 && (
        <div className="live-events-section">
          <div className="live-events-header"><span className="live-dot" />Live Stream</div>
          {streamEvents.slice(0, 8).map((ev, i) => (
            <div key={i} className="activity-row live animate-stream">
              <span className="activity-time">{fmtRelative(ev.timestamp || '')}</span>
              {ev.agent && <AgentPill name={ev.agent} />}
              <span className="activity-action">{(ev.data?.action as string) || ev.type}</span>
              <span className={`activity-status ${ev.type === 'agent_complete' ? 'success' : 'running'}`}>
                {ev.type === 'agent_complete' ? '✓' : ev.type === 'error' ? '✗' : '●'}
              </span>
            </div>
          ))}
        </div>
      )}

      <div className="activity-list">
        {activities.map(act => (
          <div key={act.id} className="activity-row animate-fade-in">
            <span className="activity-time">{fmtRelative(act.created_at)}</span>
            <AgentPill name={act.agent_name} />
            <span className="activity-action">{act.action}</span>
            {act.duration_ms && <span className="activity-dur">{act.duration_ms}ms</span>}
            <span className={`activity-status ${act.status}`}>{act.status === 'success' ? '✓' : act.status === 'error' ? '✗' : '●'}</span>
          </div>
        ))}
        {activities.length === 0 && (
          <div className="activity-empty">
            <Activity size={40} opacity={0.3} />
            <p>No activity yet — run a workflow to see agent actions here.</p>
          </div>
        )}
      </div>
    </div>
  )
}
