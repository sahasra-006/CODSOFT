/**
 * Image Captioning — Frontend Application
 * Manages upload, inference requests, caption display, history, dark mode.
 */

/* ── State ───────────────────────────────────────────────────── */
const state = {
  currentFile:     null,   // File object
  currentCaption:  null,   // { id, caption, style, filename, device, created_at }
  selectedStyle:   'descriptive',
  isGenerating:    false,
};

/* ── DOM refs ────────────────────────────────────────────────── */
const $ = id => document.getElementById(id);

const els = {
  atmosphere:       $('atmosphere'),
  themeToggle:      $('themeToggle'),
  deviceBadge:      $('deviceBadge'),

  // Workspace
  dropZone:         $('dropZone'),
  fileInput:        $('fileInput'),
  browseBtn:        $('browseBtn'),
  imagePreview:     $('imagePreview'),
  previewImg:       $('previewImg'),
  replaceBtn:       $('replaceBtn'),
  thinkingOverlay:  $('thinkingOverlay'),
  thinkingText:     $('thinkingText'),
  styleBar:         $('styleBar'),
  generateBtn:      $('generateBtn'),

  // Caption panel
  panelStyleTag:    $('panelStyleTag'),
  captionEmpty:     $('captionEmpty'),
  captionSkeleton:  $('captionSkeleton'),
  captionResult:    $('captionResult'),
  captionText:      $('captionText'),
  captionMeta:      $('captionMeta'),
  panelActions:     $('panelActions'),
  captionError:     $('captionError'),
  errorText:        $('errorText'),
  copyBtn:          $('copyBtn'),
  downloadBtn:      $('downloadBtn'),
  regenerateBtn:    $('regenerateBtn'),

  // Sidebar
  historyList:      $('historyList'),
};

/* ── Theme ───────────────────────────────────────────────────── */
(function initTheme() {
  const saved = localStorage.getItem('ps-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

els.themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('ps-theme', next);
});

/* ── File Upload ─────────────────────────────────────────────── */
els.browseBtn.addEventListener('click', () => els.fileInput.click());
els.dropZone.addEventListener('click', () => els.fileInput.click());
els.replaceBtn.addEventListener('click', () => els.fileInput.click());

els.fileInput.addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) {
    const err = validateFile(file);
    if (err) { showUploadError(err); return; }
    handleFileSelected(file);
  }
  e.target.value = '';
});

// Drag and drop
els.dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  els.dropZone.classList.add('drag-over');
});
['dragleave', 'dragend'].forEach(ev =>
  els.dropZone.addEventListener(ev, () => els.dropZone.classList.remove('drag-over'))
);
els.dropZone.addEventListener('drop', e => {
  e.preventDefault();
  els.dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (!file) return;
  if (!file.type.startsWith('image/')) {
    showUploadError('Please drop an image file.');
    return;
  }
  const err = validateFile(file);
  if (err) { showUploadError(err); return; }
  handleFileSelected(file);
});

/* ── File validation (client-side guard) ─────────────────────── */
const MAX_SIZE_MB = 10;
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/bmp', 'image/gif', 'image/tiff'];

function validateFile(file) {
  if (file.size > MAX_SIZE_MB * 1024 * 1024) {
    return `File too large — maximum is ${MAX_SIZE_MB} MB. This file is ${(file.size / (1024*1024)).toFixed(1)} MB.`;
  }
  if (!ACCEPTED_TYPES.includes(file.type)) {
    return `Unsupported format. Please upload a JPEG, PNG, WebP, BMP, GIF, or TIFF.`;
  }
  return null;
}

function showUploadError(msg) {
  // Briefly show error in caption panel without navigating away
  showCaptionState('error');
  els.errorText.textContent = msg;
}

function handleFileSelected(file) {
  state.currentFile = file;
  state.currentCaption = null;

  const url = URL.createObjectURL(file);
  els.previewImg.src = url;

  // Show preview, update atmosphere
  els.dropZone.classList.add('hidden');
  els.imagePreview.classList.remove('hidden');
  els.styleBar.classList.remove('hidden');

  // Blurred atmosphere background
  els.atmosphere.style.backgroundImage = `url(${url})`;
  els.atmosphere.classList.add('active');

  // Reset caption panel
  showCaptionState('empty');
  els.panelStyleTag.textContent = '';
}

/* ── Style Pills ─────────────────────────────────────────────── */
document.querySelectorAll('.style-pill').forEach(pill => {
  pill.addEventListener('click', () => {
    document.querySelectorAll('.style-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');
    state.selectedStyle = pill.dataset.style;
  });
});

/* ── Generate Caption ────────────────────────────────────────── */
els.generateBtn.addEventListener('click', generateCaption);

async function generateCaption() {
  if (!state.currentFile || state.isGenerating) return;
  state.isGenerating = true;

  const thinkingMessages = [
    'Interpreting visual story…',
    'Analysing composition…',
    'Constructing narrative…',
    'Refining language…',
  ];
  let msgIdx = 0;
  els.thinkingText.textContent = thinkingMessages[0];

  const msgInterval = setInterval(() => {
    msgIdx = (msgIdx + 1) % thinkingMessages.length;
    els.thinkingText.textContent = thinkingMessages[msgIdx];
  }, 1800);

  // Show loading states
  els.thinkingOverlay.classList.remove('hidden');
  els.generateBtn.disabled = true;
  showCaptionState('skeleton');
  els.panelStyleTag.textContent = state.selectedStyle;

  try {
    const formData = new FormData();
    formData.append('file', state.currentFile);
    formData.append('style', state.selectedStyle);

    const response = await fetch('/api/caption', {
      method: 'POST',
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || `Server error ${response.status}`);
    }

    state.currentCaption = data;
    els.deviceBadge.textContent = `— ${data.device.toUpperCase()}`;

    showCaption(data);
    loadHistory(); // refresh sidebar

  } catch (err) {
    showError(err.message || 'Caption generation failed. Please try again.');
  } finally {
    clearInterval(msgInterval);
    els.thinkingOverlay.classList.add('hidden');
    els.generateBtn.disabled = false;
    state.isGenerating = false;
  }
}

/* ── Caption Display ─────────────────────────────────────────── */
function showCaptionState(state) {
  ['captionEmpty', 'captionSkeleton', 'captionResult', 'captionError', 'panelActions']
    .forEach(key => els[key].classList.add('hidden'));

  if (state === 'empty')    els.captionEmpty.classList.remove('hidden');
  if (state === 'skeleton') els.captionSkeleton.classList.remove('hidden');
  if (state === 'result') {
    els.captionResult.classList.remove('hidden');
    els.panelActions.classList.remove('hidden');
  }
  if (state === 'error') els.captionError.classList.remove('hidden');
}

function showCaption(data) {
  showCaptionState('result');
  els.panelStyleTag.textContent = data.style;

  // Progressive word-by-word reveal
  revealCaption(data.caption);

  // Meta info
  els.captionMeta.innerHTML = `
    <span>${data.filename}</span>
    <span>${formatDate(data.created_at)}</span>
  `;
}

function revealCaption(text) {
  // Staggered sentence fade-in — understated, not word-by-word gimmicky
  els.captionText.innerHTML = '';
  els.captionText.textContent = text;
  els.captionText.style.opacity = '0';
  els.captionText.style.transform = 'translateY(6px)';

  // Single smooth reveal after a brief settle delay
  requestAnimationFrame(() => {
    els.captionText.style.transition = 'opacity 0.55s ease, transform 0.55s ease';
    els.captionText.style.opacity = '1';
    els.captionText.style.transform = 'translateY(0)';
  });
}

function showError(msg) {
  showCaptionState('error');
  els.errorText.textContent = msg;
}

/* ── Copy ────────────────────────────────────────────────────── */
els.copyBtn.addEventListener('click', async () => {
  if (!state.currentCaption) return;
  try {
    await navigator.clipboard.writeText(state.currentCaption.caption);
    const orig = els.copyBtn.innerHTML;
    els.copyBtn.innerHTML = '<svg viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5" width="15"><path d="M4 10l4 4 8-8"/></svg> Copied!';
    els.copyBtn.classList.add('success');
    setTimeout(() => { els.copyBtn.innerHTML = orig; els.copyBtn.classList.remove('success'); }, 2000);
  } catch {
    alert(state.currentCaption.caption);
  }
});

/* ── Download ────────────────────────────────────────────────── */
els.downloadBtn.addEventListener('click', () => {
  if (!state.currentCaption) return;
  window.location.href = `/api/history/${state.currentCaption.id}/download`;
});

/* ── Regenerate ──────────────────────────────────────────────── */
els.regenerateBtn.addEventListener('click', generateCaption);

/* ── History ─────────────────────────────────────────────────── */
async function loadHistory() {
  try {
    const res = await fetch('/api/history?limit=30');
    const data = await res.json();
    renderHistory(data.items);
  } catch {
    // Silent fail — history is non-critical
  }
}

function renderHistory(items) {
  if (!items || items.length === 0) {
    els.historyList.innerHTML = '<li class="history-empty">No captions yet</li>';
    return;
  }

  els.historyList.innerHTML = items.map(item => `
    <li class="history-item" data-id="${item.id}" title="${escHtml(item.caption)}">
      <div class="hi-caption">${escHtml(item.caption)}</div>
      <div class="hi-meta">
        <span class="hi-style-tag">${escHtml(item.style)}</span>
        <span>${friendlyTime(item.created_at)}</span>
      </div>
    </li>
  `).join('');
}

/* ── Helpers ─────────────────────────────────────────────────── */
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function formatDate(iso) {
  try {
    return new Date(iso + 'Z').toLocaleString(undefined, {
      month: 'short', day: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return iso; }
}

function friendlyTime(iso) {
  try {
    const delta = (Date.now() - new Date(iso + 'Z').getTime()) / 1000;
    if (delta < 60)    return 'just now';
    if (delta < 3600)  return `${Math.floor(delta/60)}m ago`;
    if (delta < 86400) return `${Math.floor(delta/3600)}h ago`;
    return `${Math.floor(delta/86400)}d ago`;
  } catch { return ''; }
}

/* ── Init ────────────────────────────────────────────────────── */
loadHistory();
