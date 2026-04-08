/**
 * Nexus AI — Multi-Agent Productivity Assistant
 * Frontend application logic
 */

// ─── STATE ─────────────────────────────────────────────────
let currentView = 'dashboard';
let sessionId = 'session_' + Date.now();
let isProcessing = false;
let chatHistory = [];

// ─── INITIALIZATION ────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    // Setup navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', () => handleNavClick(item));
    });

    // Auto-resize textarea
    const input = document.getElementById('chat-input');
    input.addEventListener('input', () => {
        input.style.height = 'auto';
        input.style.height = Math.min(input.scrollHeight, 120) + 'px';
    });

    // Load dashboard data
    await loadDashboard();

    // Hide loading overlay
    setTimeout(() => {
        document.getElementById('loadingOverlay').classList.add('hidden');
    }, 800);
});

// ─── NAVIGATION ────────────────────────────────────────────
function handleNavClick(item) {
    const view = item.dataset.view;
    const prompt = item.dataset.prompt;

    // Update active state
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    item.classList.add('active');

    // Switch view
    switchView(view);

    // If nav item has a prompt, send it
    if (prompt && view === 'chat') {
        setTimeout(() => sendQuickAction(prompt), 300);
    }
}

function switchView(view) {
    currentView = view;
    document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
    document.getElementById('view-' + view).classList.add('active');

    const titles = { dashboard: 'Dashboard', chat: 'Agent Chat' };
    document.getElementById('view-title').textContent = titles[view] || 'Dashboard';

    // Show agent panel in chat view
    const agentPanel = document.getElementById('agent-panel');
    if (view === 'chat') {
        agentPanel.classList.add('visible');
    }
}

// ─── DASHBOARD ─────────────────────────────────────────────
async function loadDashboard() {
    try {
        const response = await fetch('/api/dashboard');
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function renderDashboard(data) {
    const stats = data.stats;

    // Update sidebar badges
    document.getElementById('task-count').textContent = stats.total_tasks;
    document.getElementById('event-count').textContent = stats.total_events;
    document.getElementById('email-count').textContent = stats.total_emails;
    document.getElementById('note-count').textContent = stats.total_notes;

    // Stats grid
    document.getElementById('stats-grid').innerHTML = `
        <div class="stat-card">
            <div class="stat-icon">📋</div>
            <div class="stat-value">${stats.total_tasks}</div>
            <div class="stat-label">Total Tasks</div>
            <div class="stat-change">▲ ${stats.tasks_in_progress} in progress</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📅</div>
            <div class="stat-value">${stats.total_events}</div>
            <div class="stat-label">Events</div>
            <div class="stat-change">📆 ${data.today_events.length} today</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📧</div>
            <div class="stat-value">${stats.total_emails}</div>
            <div class="stat-label">Emails</div>
            <div class="stat-change">✉️ Communications</div>
        </div>
        <div class="stat-card">
            <div class="stat-icon">📝</div>
            <div class="stat-value">${stats.total_notes}</div>
            <div class="stat-label">Notes</div>
            <div class="stat-change">🔴 ${stats.critical_tasks} critical tasks</div>
        </div>
    `;

    // Dashboard panels
    document.getElementById('dashboard-panels').innerHTML = `
        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">📋 Recent Tasks</div>
            </div>
            <div class="panel-content">
                ${data.recent_tasks.map(task => `
                    <div class="task-item">
                        <div class="task-priority ${task.priority}"></div>
                        <div class="task-info">
                            <h4>${escapeHtml(task.title)}</h4>
                            <div class="task-meta">
                                <span class="status-badge ${task.status}">${formatStatus(task.status)}</span>
                                <span>👤 ${escapeHtml(task.assignee || 'Unassigned')}</span>
                                ${task.due_date ? `<span>📅 ${task.due_date}</span>` : ''}
                            </div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">📅 Upcoming Events</div>
            </div>
            <div class="panel-content">
                ${data.upcoming_events.map(event => `
                    <div class="event-item">
                        <div class="event-time">
                            <div class="time">${formatTime(event.start_time)}</div>
                            <div class="duration">${formatDuration(event.start_time, event.end_time)}</div>
                        </div>
                        <div class="event-info">
                            <h4>${escapeHtml(event.title)}</h4>
                            <div class="event-meta">📍 ${escapeHtml(event.location || 'TBD')}</div>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">📧 Recent Emails</div>
            </div>
            <div class="panel-content">
                ${data.recent_emails.map(email => `
                    <div class="email-item">
                        <h4>${escapeHtml(email.subject)}</h4>
                        <div class="email-meta">
                            <span>👤 ${escapeHtml(email.sender)}</span>
                            <span class="status-badge ${email.status}">${email.status}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>

        <div class="panel">
            <div class="panel-header">
                <div class="panel-title">📝 Recent Notes</div>
            </div>
            <div class="panel-content">
                ${data.recent_notes.map(note => `
                    <div class="email-item">
                        <h4>${escapeHtml(note.title)}</h4>
                        <div class="email-meta">
                            <span>📁 ${note.category}</span>
                            <span>🏷️ ${escapeHtml(note.tags || '')}</span>
                        </div>
                    </div>
                `).join('')}
            </div>
        </div>
    `;
}

// ─── CHAT ──────────────────────────────────────────────────
function handleChatKeydown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (!message || isProcessing) return;

    // Hide welcome screen
    const welcome = document.getElementById('chat-welcome');
    if (welcome) welcome.style.display = 'none';

    // Add user message
    addMessage('user', message);
    input.value = '';
    input.style.height = 'auto';

    // Show typing indicator
    isProcessing = true;
    document.getElementById('send-btn').disabled = true;
    const typingId = showTyping();

    // Activate orchestrator agent card
    setAgentActive('orchestrator', 'Processing...');

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, session_id: sessionId })
        });

        const data = await response.json();

        // Remove typing indicator
        removeTyping(typingId);

        if (data.error) {
            addMessage('assistant', '❌ Error: ' + data.error);
        } else {
            // Show agent activity
            if (data.agent_actions && data.agent_actions.length > 0) {
                data.agent_actions.forEach(action => {
                    setAgentActive(action.agent, 'Completed');
                });
            }
            addMessage('assistant', data.response, data.agent_actions);
        }

        // Refresh dashboard data in background
        loadDashboard();

    } catch (error) {
        removeTyping(typingId);
        addMessage('assistant', '❌ Connection error. Please ensure the server is running.');
    }

    isProcessing = false;
    document.getElementById('send-btn').disabled = false;
    resetAgentCards();
}

function sendQuickAction(prompt) {
    switchView('chat');
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    document.getElementById('nav-chat').classList.add('active');

    const input = document.getElementById('chat-input');
    input.value = prompt;
    sendMessage();
}

function addMessage(role, content, agentActions) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const avatar = role === 'assistant' ? '🤖' : '👤';
    const formattedContent = role === 'assistant' ? formatMarkdown(content) : escapeHtml(content);

    let activityHtml = '';
    if (agentActions && agentActions.length > 0) {
        const uniqueAgents = [...new Set(agentActions.map(a => a.agent))];
        const agentNames = {
            'task_manager': '📋 Task Manager',
            'calendar_agent': '📅 Calendar',
            'email_agent': '📧 Email',
            'notes_agent': '📝 Notes'
        };
        const agentLabels = uniqueAgents.map(a => agentNames[a] || a).join(', ');
        activityHtml = `<div class="agent-activity">⚡ Agents used: ${agentLabels}</div>`;
    }

    messageEl.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div>
            <div class="message-bubble">${formattedContent}</div>
            ${activityHtml}
        </div>
    `;

    messagesContainer.appendChild(messageEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;

    chatHistory.push({ role, content });
}

function showTyping() {
    const messagesContainer = document.getElementById('chat-messages');
    const typingEl = document.createElement('div');
    typingEl.className = 'message assistant';
    typingEl.id = 'typing-indicator';
    typingEl.innerHTML = `
        <div class="message-avatar">🤖</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="dot"></div>
                <div class="dot"></div>
                <div class="dot"></div>
            </div>
        </div>
    `;
    messagesContainer.appendChild(typingEl);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
    return 'typing-indicator';
}

function removeTyping(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// ─── AGENT PANEL ───────────────────────────────────────────
function toggleAgentPanel() {
    const panel = document.getElementById('agent-panel');
    panel.classList.toggle('visible');
}

function setAgentActive(agentName, status) {
    const card = document.getElementById('agent-card-' + agentName);
    if (card) {
        card.classList.add('active');
        const statusEl = card.querySelector('.agent-card-status');
        if (statusEl) {
            statusEl.textContent = status;
            statusEl.classList.add('processing');
        }
    }
}

function resetAgentCards() {
    setTimeout(() => {
        document.querySelectorAll('.agent-card').forEach(card => {
            card.classList.remove('active');
            const statusEl = card.querySelector('.agent-card-status');
            if (statusEl) {
                statusEl.textContent = 'Ready';
                statusEl.classList.remove('processing');
            }
        });
    }, 3000);
}

// ─── DATABASE RESET ────────────────────────────────────────
async function reseedDatabase() {
    try {
        const response = await fetch('/api/seed', { method: 'POST' });
        const data = await response.json();
        if (data.status === 'success') {
            // Reset session for fresh context
            sessionId = 'session_' + Date.now();
            // Reload dashboard
            await loadDashboard();
            // Clear chat
            const messagesContainer = document.getElementById('chat-messages');
            messagesContainer.innerHTML = `
                <div class="chat-welcome" id="chat-welcome">
                    <h2>👋 Hello! I'm Nexus AI</h2>
                    <p>Your multi-agent productivity assistant. Demo data has been reset!</p>
                    <div class="quick-actions">
                        <button class="quick-action" onclick="sendQuickAction('Give me a comprehensive daily briefing with tasks, calendar, and emails')">
                            <div class="qa-icon">⚡</div>
                            <div class="qa-text">Daily Briefing</div>
                            <div class="qa-sub">Tasks, calendar & email summary</div>
                        </button>
                        <button class="quick-action" onclick="sendQuickAction('Create a new task: Prepare investor pitch deck with critical priority, assigned to Sarah, due April 15')">
                            <div class="qa-icon">📋</div>
                            <div class="qa-text">Create Task</div>
                            <div class="qa-sub">Add a new project task</div>
                        </button>
                        <button class="quick-action" onclick="sendQuickAction('Schedule a team strategy meeting for tomorrow at 2 PM to 3 PM in Conference Room B with Sarah Chen and Mike Rivera')">
                            <div class="qa-icon">📅</div>
                            <div class="qa-text">Schedule Meeting</div>
                            <div class="qa-sub">Book a new calendar event</div>
                        </button>
                        <button class="quick-action" onclick="sendQuickAction('Draft a professional email to the engineering team about the upcoming Q2 product launch preparations and timeline')">
                            <div class="qa-icon">📧</div>
                            <div class="qa-text">Draft Email</div>
                            <div class="qa-sub">Compose and send emails</div>
                        </button>
                    </div>
                </div>
            `;
            chatHistory = [];
        }
    } catch (error) {
        console.error('Reseed error:', error);
    }
}

// ─── FORMATTING UTILITIES ──────────────────────────────────
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

function formatStatus(status) {
    const map = {
        'todo': 'To Do',
        'in_progress': 'In Progress',
        'done': 'Done',
        'blocked': 'Blocked'
    };
    return map[status] || status;
}

function formatTime(datetime) {
    if (!datetime) return '';
    try {
        const date = new Date(datetime);
        return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    } catch {
        return datetime.split('T')[1]?.substring(0, 5) || '';
    }
}

function formatDuration(start, end) {
    try {
        const s = new Date(start);
        const e = new Date(end);
        const mins = Math.round((e - s) / 60000);
        if (mins < 60) return mins + 'min';
        const hrs = Math.floor(mins / 60);
        const remMins = mins % 60;
        return remMins ? `${hrs}h ${remMins}m` : `${hrs}h`;
    } catch {
        return '';
    }
}

function formatMarkdown(text) {
    if (!text) return '';

    // Escape HTML first
    let html = escapeHtml(text);

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Code blocks
    html = html.replace(/```(\w*)\n?([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

    // Headers
    html = html.replace(/^### (.*$)/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.*$)/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.*$)/gm, '<h2>$1</h2>');

    // Unordered lists
    html = html.replace(/^[-•] (.*$)/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    // Numbered lists
    html = html.replace(/^\d+\. (.*$)/gm, '<li>$1</li>');

    // Line breaks to paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = html.replace(/\n/g, '<br>');

    // Wrap in paragraph
    if (!html.startsWith('<')) {
        html = '<p>' + html + '</p>';
    }

    return html;
}
