/* ============================================
   StudyBot Frontend — script.js
   ============================================ */

const API = '/api';

// State
let currentSessionId = null;
let isLoading = false;
let activePDFId = null;
let activePDFName = null;

// DOM refs
const sessionsList = document.getElementById('sessionsList');
const messagesContainer = document.getElementById('messagesContainer');
const welcomeScreen = document.getElementById('welcomeScreen');
const messageInput = document.getElementById('messageInput');
const btnSend = document.getElementById('btnSend');
const sessionTitle = document.getElementById('sessionTitle');
const activePdfBadge = document.getElementById('activePdfBadge');
const pdfList = document.getElementById('pdfList');
const pdfHint = document.getElementById('pdfHint');
const renameModal = document.getElementById('renameModal');
const renameInput = document.getElementById('renameInput');
const btnRenameSession = document.getElementById('btnRenameSession');

// ============ INIT ============
document.addEventListener('DOMContentLoaded', () => {
  marked.setOptions({
    breaks: true,
    gfm: true,
  });

  loadSessions();
  loadPDFs();
  bindEvents();
});

function bindEvents() {
  document.getElementById('btnNewSession').addEventListener('click', createSession);
  document.getElementById('btnStart').addEventListener('click', createSession);

  btnSend.addEventListener('click', sendMessage);
  messageInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Auto-resize textarea
  messageInput.addEventListener('input', () => {
    messageInput.style.height = 'auto';
    messageInput.style.height = Math.min(messageInput.scrollHeight, 140) + 'px';
  });

  // PDF upload
  document.getElementById('btnUploadPDF').addEventListener('click', () => {
    document.getElementById('pdfFileInput').click();
  });
  document.getElementById('pdfFileInput').addEventListener('change', handlePDFUpload);

  // Rename modal
  btnRenameSession.addEventListener('click', openRenameModal);
  document.getElementById('btnRenameConfirm').addEventListener('click', confirmRename);
  document.getElementById('btnRenameCancel').addEventListener('click', () => {
    renameModal.style.display = 'none';
  });
  renameInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') confirmRename();
    if (e.key === 'Escape') renameModal.style.display = 'none';
  });

  // Sidebar toggle
  document.getElementById('sidebarToggle').addEventListener('click', toggleSidebar);
  document.getElementById('mobileMenuBtn').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('collapsed');
  });
}

// ============ SESSIONS ============
async function loadSessions() {
  try {
    const res = await fetch(`${API}/sessions`);
    const sessions = await res.json();
    renderSessions(sessions);

    if (sessions.length > 0 && !currentSessionId) {
      // Auto-load most recent session
      selectSession(sessions[0].id, sessions[0].title);
    }
  } catch (e) {
    sessionsList.innerHTML = '<div class="loading-sessions">Failed to load sessions</div>';
  }
}

function renderSessions(sessions) {
  if (!sessions.length) {
    sessionsList.innerHTML = '<div class="loading-sessions">No sessions yet</div>';
    return;
  }

  sessionsList.innerHTML = sessions.map(s => `
    <div class="session-item ${s.id === currentSessionId ? 'active' : ''}"
         data-id="${s.id}" data-title="${escapeHtml(s.title)}"
         onclick="selectSession(${s.id}, '${escapeHtml(s.title)}')">
      <div class="session-dot"></div>
      <span class="session-name">${escapeHtml(s.title)}</span>
      <button class="session-delete" onclick="event.stopPropagation(); deleteSession(${s.id})" title="Delete session">✕</button>
    </div>
  `).join('');
}

async function createSession() {
  try {
    const res = await fetch(`${API}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: 'New Chat' })
    });
    const session = await res.json();
    selectSession(session.id, session.title);
    loadSessions();

    // Focus input
    setTimeout(() => messageInput.focus(), 100);
  } catch (e) {
    showToast('Failed to create session', 'error');
  }
}

async function selectSession(id, title) {
  currentSessionId = id;
  sessionTitle.textContent = title;
  btnRenameSession.style.display = 'flex';
  welcomeScreen.style.display = 'none';
  messagesContainer.style.display = 'flex';

  // Enable input
  messageInput.disabled = false;
  btnSend.disabled = false;
  messageInput.focus();

  // Update sidebar active state
  document.querySelectorAll('.session-item').forEach(el => {
    el.classList.toggle('active', parseInt(el.dataset.id) === id);
  });

  // Load messages
  await loadMessages(id);
}

async function deleteSession(id) {
  if (!confirm('Delete this session and all its messages?')) return;
  try {
    await fetch(`${API}/sessions/${id}`, { method: 'DELETE' });
    if (currentSessionId === id) {
      currentSessionId = null;
      sessionTitle.textContent = 'Select a session';
      btnRenameSession.style.display = 'none';
      messagesContainer.innerHTML = '';
      welcomeScreen.style.display = 'flex';
      messageInput.disabled = true;
      btnSend.disabled = true;
    }
    loadSessions();
    showToast('Session deleted', 'success');
  } catch (e) {
    showToast('Failed to delete session', 'error');
  }
}

function openRenameModal() {
  if (!currentSessionId) return;
  renameInput.value = sessionTitle.textContent;
  renameModal.style.display = 'flex';
  renameInput.focus();
  renameInput.select();
}

async function confirmRename() {
  const newTitle = renameInput.value.trim();
  if (!newTitle || !currentSessionId) return;

  try {
    const res = await fetch(`${API}/sessions/${currentSessionId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ title: newTitle })
    });
    const session = await res.json();
    sessionTitle.textContent = session.title;
    renameModal.style.display = 'none';
    loadSessions();
    showToast('Session renamed', 'success');
  } catch (e) {
    showToast('Failed to rename session', 'error');
  }
}

// ============ MESSAGES ============
async function loadMessages(sessionId) {
  messagesContainer.innerHTML = '';
  try {
    const res = await fetch(`${API}/messages/${sessionId}`);
    const messages = await res.json();

    if (!messages.length) {
      messagesContainer.innerHTML = `
        <div style="text-align:center; color: var(--text-muted); font-size:0.85rem; padding: 40px 20px;">
          Start the conversation by asking a question below ↓
        </div>
      `;
      return;
    }

    messages.forEach(msg => {
      if (msg.role === 'user') {
        appendUserMessage(msg.content);
      } else {
        appendAssistantMessage(msg.content, msg.response_type, false);
      }
    });

    scrollToBottom();
  } catch (e) {
    messagesContainer.innerHTML = '<div style="color:var(--red);padding:20px;">Failed to load messages.</div>';
  }
}

function appendUserMessage(content) {
  const div = document.createElement('div');
  div.className = 'message-row user';
  div.innerHTML = `<div class="bubble user">${escapeHtml(content)}</div>`;
  messagesContainer.appendChild(div);
}

function appendAssistantMessage(content, type, animate = false) {
  const badgeClass = type === 'rule' ? 'badge-rule' : type === 'pdf' ? 'badge-pdf' : 'badge-ai';
  const badgeLabel = type === 'rule' ? 'RULE' : type === 'pdf' ? 'PDF' : 'AI';

  const row = document.createElement('div');
  row.className = 'message-row assistant';

  const avatar = document.createElement('div');
  avatar.className = 'avatar bot';
  avatar.textContent = '⬡';

  const bubble = document.createElement('div');
  bubble.className = 'bubble assistant';
  bubble.innerHTML = `<span class="response-badge ${badgeClass}">${badgeLabel}</span><div class="bubble-content"></div>`;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);

  const contentEl = bubble.querySelector('.bubble-content');

  if (animate) {
    typewriterEffect(contentEl, content);
  } else {
    contentEl.innerHTML = marked.parse(content);
  }

  scrollToBottom();
  return contentEl;
}

function showTypingIndicator() {
  const row = document.createElement('div');
  row.className = 'message-row assistant';
  row.id = 'typingIndicator';

  const avatar = document.createElement('div');
  avatar.className = 'avatar bot';
  avatar.textContent = '⬡';

  const bubble = document.createElement('div');
  bubble.className = 'bubble assistant';
  bubble.innerHTML = `
    <div class="typing-indicator">
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
      <div class="typing-dot"></div>
    </div>
  `;

  row.appendChild(avatar);
  row.appendChild(bubble);
  messagesContainer.appendChild(row);
  scrollToBottom();
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typingIndicator');
  if (indicator) indicator.remove();
}

function typewriterEffect(el, content) {
  const rendered = marked.parse(content);
  const tempDiv = document.createElement('div');
  tempDiv.innerHTML = rendered;
  const fullText = tempDiv.innerText;

  let i = 0;
  const words = fullText.split(' ');
  let displayed = '';

  const interval = setInterval(() => {
    if (i >= words.length) {
      el.innerHTML = rendered; // Show final formatted version
      clearInterval(interval);
      return;
    }

    const chunkSize = Math.floor(Math.random() * 3) + 1;
    const chunk = words.slice(i, i + chunkSize).join(' ');
    displayed += (i > 0 ? ' ' : '') + chunk;
    el.textContent = displayed + '▌';
    i += chunkSize;
    scrollToBottom();
  }, 30);
}

// ============ SEND MESSAGE ============
async function sendMessage() {
  if (isLoading || !currentSessionId) return;

  const text = messageInput.value.trim();
  if (!text) return;

  messageInput.value = '';
  messageInput.style.height = 'auto';
  isLoading = true;
  btnSend.disabled = true;

  appendUserMessage(text);
  showTypingIndicator();
  scrollToBottom();

  try {
    const res = await fetch(`${API}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: currentSessionId,
        message: text
      })
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Request failed');
    }

    const data = await res.json();
    removeTypingIndicator();
    appendAssistantMessage(data.response, data.type, true);

  } catch (e) {
    removeTypingIndicator();
    appendAssistantMessage(`⚠️ Error: ${e.message}`, 'ai', false);
    showToast('Failed to get response', 'error');
  } finally {
    isLoading = false;
    btnSend.disabled = false;
    messageInput.focus();
  }
}

// ============ PDF ============
async function loadPDFs() {
  try {
    const res = await fetch(`${API}/pdfs`);
    const pdfs = await res.json();
    renderPDFs(pdfs);

    const active = pdfs.find(p => p.is_active);
    if (active) {
      activePDFId = active.id;
      activePDFName = active.filename;
      updatePDFBadge();
    }
  } catch (e) {
    pdfList.innerHTML = '<div class="loading-pdfs">Failed to load PDFs</div>';
  }
}

function renderPDFs(pdfs) {
  if (!pdfs.length) {
    pdfList.innerHTML = '<div class="loading-pdfs">No PDFs uploaded yet</div>';
    return;
  }

  pdfList.innerHTML = pdfs.map(p => `
    <div class="pdf-item ${p.is_active ? 'active-pdf' : ''}" data-id="${p.id}">
      <span class="pdf-icon">📄</span>
      <span class="pdf-name" title="${escapeHtml(p.filename)}">${escapeHtml(p.filename)}</span>
      <div class="pdf-actions">
        ${!p.is_active
          ? `<button class="pdf-action-btn activate-btn" onclick="activatePDF(${p.id})" title="Use this PDF">▶</button>`
          : `<button class="pdf-action-btn activate-btn" onclick="deactivatePDF()" title="Deactivate PDF" style="color:var(--orange)">■</button>`
        }
        <button class="pdf-action-btn delete-btn" onclick="deletePDF(${p.id})" title="Delete PDF">✕</button>
      </div>
    </div>
  `).join('');
}

async function handlePDFUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  if (!file.name.endsWith('.pdf')) {
    showToast('Only PDF files allowed', 'error');
    return;
  }

  const formData = new FormData();
  formData.append('file', file);

  const btn = document.getElementById('btnUploadPDF');
  btn.disabled = true;
  btn.innerHTML = '<span>⏳</span> Uploading...';

  try {
    const res = await fetch(`${API}/upload-pdf`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Upload failed');
    }

    showToast('PDF uploaded successfully!', 'success');
    loadPDFs();
  } catch (e) {
    showToast(`Upload failed: ${e.message}`, 'error');
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span class="upload-icon">↑</span><span>Upload PDF</span>';
    e.target.value = '';
  }
}

async function activatePDF(id) {
  try {
    const res = await fetch(`${API}/activate-pdf/${id}`, { method: 'POST' });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to activate PDF');
    }
    const pdf = await res.json();
    activePDFId = pdf.id;
    activePDFName = pdf.filename;
    updatePDFBadge();
    loadPDFs();
    showToast(`PDF activated: ${pdf.filename}`, 'success');
  } catch (e) {
    showToast(`Failed to activate: ${e.message}`, 'error');
  }
}

async function deactivatePDF() {
  try {
    await fetch(`${API}/deactivate-pdf`, { method: 'POST' });
    activePDFId = null;
    activePDFName = null;
    updatePDFBadge();
    loadPDFs();
    showToast('PDF deactivated', 'success');
  } catch (e) {
    showToast('Failed to deactivate PDF', 'error');
  }
}

async function deletePDF(id) {
  if (!confirm('Delete this PDF?')) return;
  try {
    await fetch(`${API}/pdf/${id}`, { method: 'DELETE' });
    if (activePDFId === id) {
      activePDFId = null;
      activePDFName = null;
      updatePDFBadge();
    }
    loadPDFs();
    showToast('PDF deleted', 'success');
  } catch (e) {
    showToast('Failed to delete PDF', 'error');
  }
}

function updatePDFBadge() {
  if (activePDFId && activePDFName) {
    activePdfBadge.style.display = 'inline-flex';
    const shortName = activePDFName.length > 20 ? activePDFName.substring(0, 20) + '…' : activePDFName;
    activePdfBadge.textContent = `📄 ${shortName}`;
    pdfHint.textContent = `PDF active: ${shortName}`;
  } else {
    activePdfBadge.style.display = 'none';
    pdfHint.textContent = '';
  }
}

// ============ UTILS ============
function scrollToBottom() {
  const chatArea = document.getElementById('chatArea');
  requestAnimationFrame(() => {
    chatArea.scrollTop = chatArea.scrollHeight;
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function showToast(message, type = '') {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  const toggle = document.getElementById('sidebarToggle');
  sidebar.classList.toggle('collapsed');
  toggle.textContent = sidebar.classList.contains('collapsed') ? '›' : '‹';
}
