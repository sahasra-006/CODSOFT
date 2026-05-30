/* ── StudyMate AI — app.js ─────────────────────────────────────────────────── */
'use strict';

const API = '';  // same origin

// ── State ──────────────────────────────────────────────────────────────────────
const state = {
  sessionId: null,
  sessions: [],
  messages: [],
  hasPdf: false,
  isTyping: false,
  theme: localStorage.getItem('sm_theme') || 'light',
};

// ── DOM Refs ───────────────────────────────────────────────────────────────────
const $ = (sel) => document.querySelector(sel);
const $$ = (sel) => document.querySelectorAll(sel);

const els = {
  app:              () => $('#app'),
  sidebar:          () => $('#sidebar'),
  sidebarOverlay:   () => $('#sidebar-overlay'),
  sessionsList:     () => $('#sessions-list'),
  pdfsList:         () => $('#pdfs-list'),
  pdfsSection:      () => $('#pdfs-section'),
  newChatBtn:       () => $('#new-chat-btn'),
  mobileMenuBtn:    () => $('#mobile-menu-btn'),
  chatArea:         () => $('#chat-area'),
  chatInner:        () => $('#chat-inner'),
  welcomeScreen:    () => $('#welcome-screen'),
  typingIndicator:  () => $('#typing-indicator'),
  typingAvatar:     () => $('#typing-avatar'),
  inputArea:        () => $('#input-area'),
  messageInput:     () => $('#message-input'),
  sendBtn:          () => $('#send-btn'),
  uploadPdfBtn:     () => $('#upload-pdf-btn'),
  themeToggle:      () => $('#theme-toggle'),
  sessionTitleEl:   () => $('#session-title-display'),
  pdfContextBar:    () => $('#pdf-context-bar'),
  pdfContextText:   () => $('#pdf-context-text'),

  // Modal
  pdfModalOverlay:  () => $('#pdf-modal-overlay'),
  pdfModal:         () => $('#pdf-modal'),
  dropZone:         () => $('#drop-zone'),
  pdfFileInput:     () => $('#pdf-file-input'),
  modalClose:       () => $('#modal-close'),
  uploadProgress:   () => $('#upload-progress'),
  progressFill:     () => $('#progress-fill'),
  progressText:     () => $('#progress-text'),

  toastContainer:   () => $('#toast-container'),
};

// ── Init ───────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  applyTheme(state.theme);
  bindEvents();
  await loadSessions();
  await createOrRestoreSession();
});

// ── Session Management ─────────────────────────────────────────────────────────
async function loadSessions() {
  try {
    const res = await fetch(`${API}/api/sessions/`);
    const data = await res.json();
    state.sessions = data.sessions || [];
    renderSessionsList();
  } catch (e) {
    console.error('loadSessions error:', e);
  }
}

async function createOrRestoreSession() {
  // Try to restore last session
  const lastId = localStorage.getItem('sm_session_id');
  if (lastId && state.sessions.find(s => s.session_id === lastId)) {
    await loadSession(lastId);
  } else {
    await startNewSession();
  }
}

async function startNewSession() {
  try {
    const res = await fetch(`${API}/api/sessions/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New Chat' }),
    });
    const data = await res.json();
    state.sessionId = data.session_id;
    localStorage.setItem('sm_session_id', state.sessionId);
    state.messages = [];
    state.hasPdf = false;
    updatePdfContextBar([]);
    showWelcomeScreen();
    await loadSessions();
    setActiveSession(state.sessionId);
  } catch (e) {
    toast('Failed to create session', 'error');
  }
}

async function loadSession(sessionId) {
  state.sessionId = sessionId;
  localStorage.setItem('sm_session_id', sessionId);
  setActiveSession(sessionId);

  try {
    // Load messages
    const msgRes = await fetch(`${API}/api/chat/history/${sessionId}`);
    const msgData = await msgRes.json();
    state.messages = msgData.messages || [];

    // Load docs
    const docRes = await fetch(`${API}/api/pdf/documents/${sessionId}`);
    const docData = await docRes.json();
    const docs = docData.documents || [];
    state.hasPdf = docs.length > 0;
    updatePdfContextBar(docs);
    renderDocumentsList(docs);

    // Render UI
    const session = state.sessions.find(s => s.session_id === sessionId);
    const title = session ? session.title : 'Chat';
    els.sessionTitleEl().textContent = title;

    renderMessages();

    if (state.messages.length === 0) {
      showWelcomeScreen();
    } else {
      hideWelcomeScreen();
    }

    closeMobileSidebar();
  } catch (e) {
    toast('Failed to load session', 'error');
  }
}

async function deleteSession(sessionId, e) {
  e.stopPropagation();
  if (!confirm('Delete this chat? This cannot be undone.')) return;

  try {
    await fetch(`${API}/api/sessions/${sessionId}`, { method: 'DELETE' });
    if (state.sessionId === sessionId) {
      await startNewSession();
    }
    await loadSessions();
    toast('Chat deleted', 'info');
  } catch (e) {
    toast('Failed to delete chat', 'error');
  }
}

// ── Messaging ──────────────────────────────────────────────────────────────────
async function sendMessage(text) {
  text = text.trim();
  if (!text || state.isTyping) return;

  hideWelcomeScreen();
  state.isTyping = true;
  els.sendBtn().disabled = true;
  els.messageInput().value = '';
  els.messageInput().style.height = 'auto';

  // Optimistic user message
  const userMsg = {
    id: Date.now(),
    role: 'user',
    content: text,
    response_type: 'user',
    created_at: new Date().toISOString(),
  };
  state.messages.push(userMsg);
  appendMessage(userMsg);
  showTypingIndicator();
  scrollToBottom();

  try {
    const res = await fetch(`${API}/api/chat/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: state.sessionId, message: text }),
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Server error');
    }

    const data = await res.json();
    const assistantMsg = {
      id: Date.now() + 1,
      role: 'assistant',
      content: data.response,
      response_type: data.response_type,
      sources: data.sources || [],
      created_at: new Date().toISOString(),
    };
    state.messages.push(assistantMsg);
    hideTypingIndicator();
    appendMessage(assistantMsg);
    scrollToBottom();

    // Update session list (title may have changed)
    await loadSessions();
    setActiveSession(state.sessionId);

  } catch (e) {
    hideTypingIndicator();
    const errMsg = {
      id: Date.now() + 2,
      role: 'assistant',
      content: `⚠️ **Error:** ${e.message || 'Could not reach the server. Please try again.'}`,
      response_type: 'error',
      created_at: new Date().toISOString(),
    };
    appendMessage(errMsg);
    scrollToBottom();
    toast(e.message || 'Request failed', 'error');
  } finally {
    state.isTyping = false;
    els.sendBtn().disabled = false;
    els.messageInput().focus();
  }
}

// ── PDF Upload ─────────────────────────────────────────────────────────────────
async function uploadPdf(file) {
  if (!file || !file.name.toLowerCase().endsWith('.pdf')) {
    toast('Please select a PDF file', 'error');
    return;
  }

  if (file.size > 20 * 1024 * 1024) {
    toast('File too large. Max 20 MB.', 'error');
    return;
  }

  showUploadProgress();

  const formData = new FormData();
  formData.append('session_id', state.sessionId);
  formData.append('file', file);

  // Fake progress animation
  let progress = 0;
  const progressInterval = setInterval(() => {
    progress = Math.min(progress + Math.random() * 15, 85);
    setProgress(progress, 'Uploading & processing…');
  }, 400);

  try {
    const res = await fetch(`${API}/api/pdf/upload`, {
      method: 'POST',
      body: formData,
    });

    clearInterval(progressInterval);

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    setProgress(100, 'Complete!');
    const data = await res.json();

    // Show success message in chat
    hideWelcomeScreen();
    const sysMsg = {
      id: Date.now(),
      role: 'assistant',
      content: data.message,
      response_type: 'pdf',
      created_at: new Date().toISOString(),
    };
    state.messages.push(sysMsg);
    appendMessage(sysMsg);
    scrollToBottom();

    // Refresh docs
    const docRes = await fetch(`${API}/api/pdf/documents/${state.sessionId}`);
    const docData = await docRes.json();
    const docs = docData.documents || [];
    state.hasPdf = true;
    updatePdfContextBar(docs);
    renderDocumentsList(docs);

    setTimeout(() => {
      closePdfModal();
      toast(`📄 "${file.name}" ready for Q&A!`, 'success');
    }, 600);

  } catch (e) {
    clearInterval(progressInterval);
    hideUploadProgress();
    closePdfModal();
    toast(e.message || 'Upload failed', 'error');
  }
}

// ── Render Functions ───────────────────────────────────────────────────────────
function renderMessages() {
  els.chatInner().innerHTML = '';
  for (const msg of state.messages) {
    appendMessage(msg, false);
  }
  scrollToBottom();
}

function appendMessage(msg, animate = true) {
  const inner = els.chatInner();

  const group = document.createElement('div');
  group.className = `message-group${animate ? '' : ''}`;
  if (animate) group.style.animation = 'fadeUp 0.3s ease both';

  const row = document.createElement('div');
  row.className = `message-row ${msg.role}`;

  if (msg.role === 'assistant') {
    const avatar = document.createElement('div');
    avatar.className = 'avatar assistant';
    avatar.textContent = '🎓';
    row.appendChild(avatar);
  }

  const bubbleWrap = document.createElement('div');

  // Badge for assistant
  if (msg.role === 'assistant' && msg.response_type && msg.response_type !== 'error') {
    const badge = document.createElement('div');
    const badgeMap = {
      rule: { cls: 'badge-rule', icon: '⚡', label: 'Rule Engine' },
      ai:   { cls: 'badge-ai',   icon: '🤖', label: 'AI Response' },
      pdf:  { cls: 'badge-pdf',  icon: '📄', label: 'PDF Source' },
    };
    const b = badgeMap[msg.response_type];
    if (b) {
      badge.className = `response-badge ${b.cls}`;
      badge.innerHTML = `${b.icon} ${b.label}`;
      bubbleWrap.appendChild(badge);
    }
  }

  const bubble = document.createElement('div');
  bubble.className = `bubble ${msg.role}`;
  bubble.innerHTML = renderMarkdown(msg.content);

  // Sources
  if (msg.sources && msg.sources.length > 0) {
    const sourcesBlock = document.createElement('div');
    sourcesBlock.className = 'sources-block';
    sourcesBlock.innerHTML = `<div class="sources-title">📎 Source Excerpts</div>` +
      msg.sources.map(s => `<div class="source-item">${escapeHtml(s)}</div>`).join('');
    bubble.appendChild(sourcesBlock);
  }

  bubbleWrap.appendChild(bubble);
  row.appendChild(bubbleWrap);

  if (msg.role === 'user') {
    const avatar = document.createElement('div');
    avatar.className = 'avatar user';
    avatar.textContent = '👤';
    row.appendChild(avatar);
  }

  group.appendChild(row);

  // Timestamp
  const time = document.createElement('div');
  time.className = 'message-time';
  time.textContent = formatTime(msg.created_at);
  group.appendChild(time);

  inner.appendChild(group);
}

function renderSessionsList() {
  const list = els.sessionsList();
  list.innerHTML = '';

  if (!state.sessions.length) {
    list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">💬</div>No chats yet</div>';
    return;
  }

  for (const s of state.sessions) {
    const item = document.createElement('div');
    item.className = `session-item${s.session_id === state.sessionId ? ' active' : ''}`;
    item.dataset.id = s.session_id;

    const icon = s.document_count > 0 ? '📄' : '💬';
    const timeAgo = getRelativeTime(s.updated_at);

    item.innerHTML = `
      <div class="session-item-icon">${icon}</div>
      <div class="session-item-text">
        <div class="session-item-title">${escapeHtml(s.title || 'New Chat')}</div>
        <div class="session-item-meta">${timeAgo}</div>
      </div>
      <button class="session-item-delete" title="Delete chat">✕</button>
    `;

    item.querySelector('.session-item-delete').addEventListener('click', (e) => deleteSession(s.session_id, e));
    item.addEventListener('click', () => loadSession(s.session_id));
    list.appendChild(item);
  }
}

function renderDocumentsList(docs) {
  const section = els.pdfsSection();
  const list = els.pdfsList();
  list.innerHTML = '';

  if (!docs || docs.length === 0) {
    section.style.display = 'none';
    return;
  }

  section.style.display = 'block';
  for (const doc of docs) {
    const item = document.createElement('div');
    item.className = 'pdf-item';
    item.innerHTML = `
      <div class="pdf-item-icon">📄</div>
      <div class="pdf-item-name" title="${escapeHtml(doc.filename)}">${escapeHtml(doc.filename)}</div>
    `;
    list.appendChild(item);
  }
}

function setActiveSession(sessionId) {
  $$('.session-item').forEach(el => {
    el.classList.toggle('active', el.dataset.id === sessionId);
  });

  const session = state.sessions.find(s => s.session_id === sessionId);
  if (session) {
    els.sessionTitleEl().textContent = session.title !== 'New Chat' ? session.title : '';
  }
}

function showWelcomeScreen() {
  els.welcomeScreen() && (els.welcomeScreen().style.display = 'flex');
  els.chatInner().style.display = 'none';
}

function hideWelcomeScreen() {
  els.welcomeScreen() && (els.welcomeScreen().style.display = 'none');
  els.chatInner().style.display = 'flex';
}

function showTypingIndicator() {
  els.typingIndicator().classList.add('visible');
}

function hideTypingIndicator() {
  els.typingIndicator().classList.remove('visible');
}

function updatePdfContextBar(docs) {
  const bar = els.pdfContextBar();
  if (docs && docs.length > 0) {
    bar.classList.add('active');
    const names = docs.map(d => d.filename).join(', ');
    els.pdfContextText().textContent = `PDF active: ${names}`;
  } else {
    bar.classList.remove('active');
  }
}

function scrollToBottom() {
  const area = els.chatArea();
  requestAnimationFrame(() => {
    area.scrollTop = area.scrollHeight;
  });
}

// ── PDF Modal ──────────────────────────────────────────────────────────────────
function openPdfModal() {
  els.pdfModalOverlay().classList.add('open');
  hideUploadProgress();
  els.pdfFileInput().value = '';
}

function closePdfModal() {
  els.pdfModalOverlay().classList.remove('open');
}

function showUploadProgress() {
  els.uploadProgress().style.display = 'block';
  setProgress(0, 'Starting upload…');
}

function hideUploadProgress() {
  els.uploadProgress().style.display = 'none';
}

function setProgress(pct, text) {
  els.progressFill().style.width = `${pct}%`;
  els.progressText().textContent = text;
}

// ── Theme ──────────────────────────────────────────────────────────────────────
function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  state.theme = theme;
  localStorage.setItem('sm_theme', theme);
  const btn = els.themeToggle();
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
  applyTheme(state.theme === 'dark' ? 'light' : 'dark');
}

// ── Toast ──────────────────────────────────────────────────────────────────────
function toast(message, type = 'info', duration = 3500) {
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const t = document.createElement('div');
  t.className = `toast ${type}`;
  t.innerHTML = `<span>${icons[type] || ''}</span><span>${escapeHtml(message)}</span>`;
  els.toastContainer().appendChild(t);
  setTimeout(() => {
    t.classList.add('hiding');
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ── Mobile Sidebar ─────────────────────────────────────────────────────────────
function openMobileSidebar() {
  els.sidebar().classList.add('mobile-open');
  els.sidebarOverlay().classList.add('visible');
}

function closeMobileSidebar() {
  els.sidebar().classList.remove('mobile-open');
  els.sidebarOverlay()?.classList.remove('visible');
}

// ── Markdown Renderer ──────────────────────────────────────────────────────────
function renderMarkdown(text) {
  if (!text) return '';
  let html = escapeHtml(text);

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  // Italic
  html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
  // Inline code
  html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  html = html.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Bullet lists
  html = html.replace(/^[-•] (.+)$/gm, '<li>$1</li>');
  html = html.replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>');
  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');
  // Paragraphs (double newline)
  html = html.replace(/\n\n/g, '</p><p>');
  // Single newlines
  html = html.replace(/\n/g, '<br>');
  // Wrap in paragraph
  if (!html.startsWith('<')) html = `<p>${html}</p>`;

  return html;
}

function escapeHtml(text) {
  const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
  return String(text).replace(/[&<>"']/g, c => map[c]);
}

function formatTime(iso) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  } catch { return ''; }
}

function getRelativeTime(iso) {
  try {
    const diff = Date.now() - new Date(iso).getTime();
    const mins = Math.floor(diff / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins}m ago`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h ago`;
    const days = Math.floor(hrs / 24);
    return `${days}d ago`;
  } catch { return ''; }
}

// ── Events ─────────────────────────────────────────────────────────────────────
function bindEvents() {
  // New chat
  els.newChatBtn().addEventListener('click', startNewSession);

  // Theme
  els.themeToggle().addEventListener('click', toggleTheme);

  // Mobile menu
  els.mobileMenuBtn()?.addEventListener('click', openMobileSidebar);
  els.sidebarOverlay()?.addEventListener('click', closeMobileSidebar);

  // Upload PDF button
  els.uploadPdfBtn().addEventListener('click', openPdfModal);

  // Modal close
  els.modalClose().addEventListener('click', closePdfModal);
  els.pdfModalOverlay().addEventListener('click', (e) => {
    if (e.target === els.pdfModalOverlay()) closePdfModal();
  });

  // Drop zone click
  els.dropZone().addEventListener('click', () => els.pdfFileInput().click());

  // File input change
  els.pdfFileInput().addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) uploadPdf(file);
  });

  // Drag and drop
  els.dropZone().addEventListener('dragover', (e) => {
    e.preventDefault();
    els.dropZone().classList.add('drag-over');
  });
  els.dropZone().addEventListener('dragleave', () => {
    els.dropZone().classList.remove('drag-over');
  });
  els.dropZone().addEventListener('drop', (e) => {
    e.preventDefault();
    els.dropZone().classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file) uploadPdf(file);
  });

  // Send message
  els.sendBtn().addEventListener('click', () => {
    const text = els.messageInput().value;
    sendMessage(text);
  });

  // Enter to send
  els.messageInput().addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(els.messageInput().value);
    }
  });

  // Auto-resize textarea
  els.messageInput().addEventListener('input', () => {
    const el = els.messageInput();
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
    els.sendBtn().disabled = !el.value.trim();
  });

  // Welcome chip clicks
  document.addEventListener('click', (e) => {
    if (e.target.classList.contains('welcome-chip')) {
      const text = e.target.dataset.msg || e.target.textContent.replace(/^[^ ]+ /, '');
      els.messageInput().value = text;
      sendMessage(text);
    }
  });

  // Keyboard shortcut: Ctrl/Cmd + K = new chat
  document.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
      e.preventDefault();
      startNewSession();
    }
  });
}
