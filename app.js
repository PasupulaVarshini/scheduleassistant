/**
 * ChronosAI Agentic RAG Schedule Assistant
 * Handles dynamic chat, tool execution tracing, ChromaDB sync, and 30-day calendar explorer.
 */

// Application State
const state = {
  events: [],
  filteredEvents: [],
  selectedCategory: 'all',
  searchQuery: '',
  baseDate: '2026-10-13',
  isSending: false
};

// DOM References
const dom = {
  // Stats
  statTotal: document.getElementById('statTotal'),
  statMeetings: document.getElementById('statMeetings'),
  statWorkshops: document.getElementById('statWorkshops'),
  statTasks: document.getElementById('statTasks'),
  statAppointments: document.getElementById('statAppointments'),
  vectorStatus: document.getElementById('vectorStatus'),
  scheduleScope: document.getElementById('scheduleScope'),
  
  // Category Counts
  countAll: document.getElementById('countAll'),
  countMeeting: document.getElementById('countMeeting'),
  countWorkshop: document.getElementById('countWorkshop'),
  countTask: document.getElementById('countTask'),
  countAppointment: document.getElementById('countAppointment'),
  
  // Timeline
  timelineContainer: document.getElementById('timelineContainer'),
  scheduleFilterInput: document.getElementById('scheduleFilterInput'),
  categoryTabs: document.querySelectorAll('.cat-tab'),
  
  // Chat & Trace
  chatFeed: document.getElementById('chatFeed'),
  chatForm: document.getElementById('chatForm'),
  chatInput: document.getElementById('chatInput'),
  tracePanel: document.getElementById('tracePanel'),
  traceHeaderToggle: document.getElementById('traceHeaderToggle'),
  traceToolBadge: document.getElementById('traceToolBadge'),
  traceThought: document.getElementById('traceThought'),
  traceTool: document.getElementById('traceTool'),
  traceArgs: document.getElementById('traceArgs'),
  traceRAG: document.getElementById('traceRAG'),
  queryChips: document.querySelectorAll('.chip-btn'),
  
  // Modal
  eventModal: document.getElementById('eventModal'),
  eventForm: document.getElementById('eventForm'),
  modalTitle: document.getElementById('modalTitle'),
  btnCloseModal: document.getElementById('btnCloseModal'),
  btnCancelModal: document.getElementById('btnCancelModal'),
  btnOpenAddModal: document.getElementById('btnOpenAddModal'),
  btnResetData: document.getElementById('btnResetData'),
  
  // Form fields
  formEventId: document.getElementById('formEventId'),
  formTitle: document.getElementById('formTitle'),
  formCategory: document.getElementById('formCategory'),
  formDate: document.getElementById('formDate'),
  formStartTime: document.getElementById('formStartTime'),
  formEndTime: document.getElementById('formEndTime'),
  formLocation: document.getElementById('formLocation'),
  formParticipants: document.getElementById('formParticipants'),
  formDescription: document.getElementById('formDescription')
};

// --- INITIALIZATION ---
document.addEventListener('DOMContentLoaded', async () => {
  initEventListeners();
  await loadStats();
  await loadSchedule();
});

function initEventListeners() {
  // Category filter tabs
  dom.categoryTabs.forEach(tab => {
    tab.addEventListener('click', () => {
      dom.categoryTabs.forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      state.selectedCategory = tab.dataset.category;
      applyFilters();
    });
  });

  // Search input filter
  dom.scheduleFilterInput.addEventListener('input', (e) => {
    state.searchQuery = e.target.value.toLowerCase().trim();
    applyFilters();
  });

  // Quick Prompt Chips
  dom.queryChips.forEach(chip => {
    chip.addEventListener('click', () => {
      const query = chip.dataset.query;
      dom.chatInput.value = query;
      submitUserMessage(query);
    });
  });

  // Chat Form Submit
  dom.chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const query = dom.chatInput.value.trim();
    if (query) {
      submitUserMessage(query);
    }
  });

  // Trace Drawer Toggle
  dom.traceHeaderToggle.addEventListener('click', () => {
    dom.tracePanel.classList.toggle('collapsed');
  });

  // Modal open/close
  dom.btnOpenAddModal.addEventListener('click', () => openModal());
  dom.btnCloseModal.addEventListener('click', () => closeModal());
  dom.btnCancelModal.addEventListener('click', () => closeModal());
  dom.eventModal.addEventListener('click', (e) => {
    if (e.target === dom.eventModal) closeModal();
  });

  // Save Event from Modal
  dom.eventForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    await saveEventFromForm();
  });

  // Reset 30-Day Data
  dom.btnResetData.addEventListener('click', async () => {
    if (confirm('Reset schedule to the default 30-day realistic sample dataset?')) {
      await resetScheduleData();
    }
  });
}

// --- DATA FETCHING ---

async function loadStats() {
  try {
    const res = await fetch('/api/stats');
    if (res.ok) {
      const data = await res.json();
      state.baseDate = data.base_date;
      dom.statTotal.textContent = data.total_events;
      dom.statMeetings.textContent = data.categories.meeting || 0;
      dom.statWorkshops.textContent = data.categories.workshop || 0;
      dom.statTasks.textContent = data.categories.task || 0;
      dom.statAppointments.textContent = data.categories.appointment || 0;
      
      dom.countAll.textContent = data.total_events;
      dom.countMeeting.textContent = data.categories.meeting || 0;
      dom.countWorkshop.textContent = data.categories.workshop || 0;
      dom.countTask.textContent = data.categories.task || 0;
      dom.countAppointment.textContent = data.categories.appointment || 0;

      if (data.date_range && data.date_range.start) {
        dom.scheduleScope.textContent = `${data.date_range.start} to ${data.date_range.end}`;
      }
    }
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

async function loadSchedule() {
  try {
    const res = await fetch('/api/schedule');
    if (res.ok) {
      const data = await res.json();
      state.events = data.events;
      applyFilters();
    }
  } catch (err) {
    dom.timelineContainer.innerHTML = `<div class="loading-state"><p>Error connecting to backend API: ${err.message}</p></div>`;
  }
}

async function resetScheduleData() {
  try {
    const res = await fetch('/api/reset', { method: 'POST' });
    if (res.ok) {
      await loadStats();
      await loadSchedule();
      addAgentMessage("🔄 **System Reset Complete**: Schedule has been repopulated with 30 days of sample meetings, workshops, tasks, and appointments.");
    }
  } catch (err) {
    alert('Failed to reset schedule: ' + err.message);
  }
}

// --- FILTERING & RENDERING ---

function applyFilters() {
  let list = [...state.events];

  if (state.selectedCategory !== 'all') {
    list = list.filter(e => e.category === state.selectedCategory);
  }

  if (state.searchQuery) {
    const q = state.searchQuery;
    list = list.filter(e => 
      e.title.toLowerCase().includes(q) ||
      (e.description && e.description.toLowerCase().includes(q)) ||
      (e.location && e.location.toLowerCase().includes(q)) ||
      (e.participants && e.participants.some(p => p.toLowerCase().includes(q)))
    );
  }

  state.filteredEvents = list;
  renderTimeline(list);
}

function renderTimeline(events) {
  if (!events || events.length === 0) {
    dom.timelineContainer.innerHTML = `
      <div class="loading-state">
        <p>No events match your current filter criteria.</p>
      </div>
    `;
    return;
  }

  // Group events by date
  const grouped = {};
  events.forEach(evt => {
    if (!grouped[evt.date]) {
      grouped[evt.date] = [];
    }
    grouped[evt.date].push(evt);
  });

  const sortedDates = Object.keys(grouped).sort();
  let html = '';

  sortedDates.forEach(dateStr => {
    const dayEvents = grouped[dateStr];
    const relativeTag = getRelativeDateLabel(dateStr, state.baseDate);

    html += `
      <div class="date-group">
        <div class="date-group-header">
          <span class="date-tag">${dateStr}</span>
          <span>(${dayEvents[0].day_of_week || 'Weekday'})</span>
          ${relativeTag ? `<span class="relative-badge">${relativeTag}</span>` : ''}
        </div>
        ${dayEvents.map(e => createEventCardHTML(e)).join('')}
      </div>
    `;
  });

  dom.timelineContainer.innerHTML = html;

  // Attach card edit / delete listeners
  dom.timelineContainer.querySelectorAll('.btn-card-action.edit').forEach(btn => {
    btn.addEventListener('click', () => {
      const evtId = btn.dataset.id;
      const target = state.events.find(e => e.id === evtId);
      if (target) openModal(target);
    });
  });

  dom.timelineContainer.querySelectorAll('.btn-card-action.delete').forEach(btn => {
    btn.addEventListener('click', async () => {
      const evtId = btn.dataset.id;
      const target = state.events.find(e => e.id === evtId);
      if (confirm(`Are you sure you want to delete '${target ? target.title : evtId}'?`)) {
        await deleteEvent(evtId);
      }
    });
  });
}

function createEventCardHTML(e) {
  const catClass = `cat-${e.category || 'meeting'}`;
  const participantsStr = Array.isArray(e.participants) ? e.participants.join(', ') : (e.participants || 'None');

  return `
    <div class="event-card ${catClass}" id="card-${e.id}">
      <div class="event-main">
        <div class="event-topline">
          <span class="category-pill">${e.category}</span>
          <span class="time-slot">${e.start_time} – ${e.end_time}</span>
        </div>
        <h4 class="event-title">${escapeHTML(e.title)}</h4>
        <div class="event-meta">
          <span class="meta-item">📍 ${escapeHTML(e.location || 'Online')}</span>
          ${participantsStr ? `<span class="meta-item">👥 ${escapeHTML(participantsStr)}</span>` : ''}
        </div>
        ${e.description ? `<p class="event-desc">${escapeHTML(e.description)}</p>` : ''}
      </div>
      <div class="event-actions">
        <button class="btn-card-action edit" data-id="${e.id}" title="Edit event">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
        </button>
        <button class="btn-card-action delete" data-id="${e.id}" title="Delete event">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
        </button>
      </div>
    </div>
  `;
}

function getRelativeDateLabel(dateStr, baseDateStr) {
  if (!dateStr || !baseDateStr) return '';
  const d = new Date(dateStr + 'T00:00:00');
  const b = new Date(baseDateStr + 'T00:00:00');
  const diffDays = Math.round((d - b) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Tomorrow';
  if (diffDays === 2) return 'In 2 Days';
  if (diffDays === 3 && d.getDay() === 5) return 'This Friday';
  return '';
}

// --- CHAT & AGENTIC INTERACTION ---

async function submitUserMessage(userPrompt) {
  if (state.isSending || !userPrompt.trim()) return;
  state.isSending = true;

  // 1. Add User bubble
  addUserMessage(userPrompt);
  dom.chatInput.value = '';

  // 2. Add temporary Thinking indicator
  const loadingBubble = addLoadingIndicator();

  // 3. Update Trace Drawer to "Thinking"
  dom.tracePanel.classList.remove('collapsed');
  dom.traceToolBadge.textContent = "Analyzing Intent...";
  dom.traceThought.textContent = `Analyzing user request: "${userPrompt}"`;
  dom.traceTool.textContent = "Selecting tool (get_schedule vs update_schedule)...";
  dom.traceArgs.textContent = "Pending parameter resolution...";
  dom.traceRAG.textContent = "Waiting for vector database query...";

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: userPrompt,
        reference_date: state.baseDate
      })
    });

    loadingBubble.remove();

    if (res.ok) {
      const data = await res.json();
      
      // Update Agent Execution Trace Inspector
      updateTraceInspector(data.trace);

      // Render Agent Response
      addAgentMessage(data.reply);

      // If calendar was mutated by update_schedule, refresh schedule view
      if (data.events_updated) {
        await loadStats();
        await loadSchedule();
      }
    } else {
      const err = await res.json();
      addAgentMessage(`❌ **Error**: ${err.detail || 'Failed to process request.'}`);
    }
  } catch (err) {
    loadingBubble.remove();
    addAgentMessage(`❌ **Connection Error**: ${err.message}`);
  } finally {
    state.isSending = false;
  }
}

function updateTraceInspector(trace) {
  if (!trace) return;

  dom.traceToolBadge.textContent = trace.tool_called || 'Direct Response';
  dom.traceThought.textContent = trace.thought || 'N/A';
  dom.traceTool.textContent = trace.tool_called ? `Tool: ${trace.tool_called}` : 'None';
  dom.traceArgs.textContent = trace.tool_arguments ? JSON.stringify(trace.tool_arguments, null, 2) : '{}';

  if (trace.rag_context && trace.rag_context.length > 0) {
    dom.traceRAG.textContent = trace.rag_context.join('\n\n---\n\n');
  } else {
    dom.traceRAG.textContent = 'No vector chunks matched or direct write operation performed.';
  }
}

function addUserMessage(text) {
  const row = document.createElement('div');
  row.className = 'message-row user-row';
  row.innerHTML = `
    <div class="avatar user-avatar">👤</div>
    <div class="message-content">
      <div class="message-meta">
        <span class="author-name">You</span>
        <span class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
      <div class="bubble user-bubble">${escapeHTML(text)}</div>
    </div>
  `;
  dom.chatFeed.appendChild(row);
  scrollChatToBottom();
}

function addAgentMessage(markdownText) {
  const row = document.createElement('div');
  row.className = 'message-row agent-row';
  row.innerHTML = `
    <div class="avatar agent-avatar">🤖</div>
    <div class="message-content">
      <div class="message-meta">
        <span class="author-name">ChronosAI Agent</span>
        <span class="timestamp">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
      </div>
      <div class="bubble agent-bubble">${formatMarkdown(markdownText)}</div>
    </div>
  `;
  dom.chatFeed.appendChild(row);
  scrollChatToBottom();
}

function addLoadingIndicator() {
  const row = document.createElement('div');
  row.className = 'message-row agent-row';
  row.innerHTML = `
    <div class="avatar agent-avatar">🤖</div>
    <div class="message-content">
      <div class="bubble agent-bubble" style="display: flex; align-items: center; gap: 8px;">
        <span class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></span>
        <span>Reasoning and querying ChromaDB vector store...</span>
      </div>
    </div>
  `;
  dom.chatFeed.appendChild(row);
  scrollChatToBottom();
  return row;
}

function scrollChatToBottom() {
  dom.chatFeed.scrollTop = dom.chatFeed.scrollHeight;
}

// Simple Markdown Formatter
function formatMarkdown(text) {
  if (!text) return '';
  let formatted = escapeHTML(text);

  // Bold **text**
  formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // Italic *text*
  formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
  // Inline code `code`
  formatted = formatted.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Bullet lists
  formatted = formatted.replace(/^\s*•\s+(.*)$/gm, '<li>$1</li>');
  formatted = formatted.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
  // Newlines to line breaks
  formatted = formatted.replace(/\n\n/g, '<br><br>');
  formatted = formatted.replace(/\n/g, '<br>');

  return formatted;
}

function escapeHTML(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

// --- MODAL & EVENT ACTIONS ---

function openModal(eventToEdit = null) {
  dom.eventModal.style.display = 'flex';
  if (eventToEdit) {
    dom.modalTitle.textContent = 'Edit Schedule Entry';
    dom.formEventId.value = eventToEdit.id;
    dom.formTitle.value = eventToEdit.title;
    dom.formCategory.value = eventToEdit.category;
    dom.formDate.value = eventToEdit.date;
    dom.formStartTime.value = eventToEdit.start_time;
    dom.formEndTime.value = eventToEdit.end_time;
    dom.formLocation.value = eventToEdit.location || '';
    dom.formParticipants.value = Array.isArray(eventToEdit.participants) ? eventToEdit.participants.join(', ') : '';
    dom.formDescription.value = eventToEdit.description || '';
  } else {
    dom.modalTitle.textContent = 'Schedule New Event';
    dom.formEventId.value = '';
    dom.formTitle.value = '';
    dom.formCategory.value = 'meeting';
    dom.formDate.value = state.baseDate;
    dom.formStartTime.value = '09:00';
    dom.formEndTime.value = '10:00';
    dom.formLocation.value = 'Online / Zoom';
    dom.formParticipants.value = '';
    dom.formDescription.value = '';
  }
}

function closeModal() {
  dom.eventModal.style.display = 'none';
}

async function saveEventFromForm() {
  const id = dom.formEventId.value;
  const participants = dom.formParticipants.value
    ? dom.formParticipants.value.split(',').map(s => s.trim()).filter(Boolean)
    : [];

  const payload = {
    title: dom.formTitle.value.trim(),
    category: dom.formCategory.value,
    date: dom.formDate.value,
    start_time: dom.formStartTime.value,
    end_time: dom.formEndTime.value,
    location: dom.formLocation.value.trim(),
    participants: participants,
    description: dom.formDescription.value.trim()
  };

  try {
    let res;
    if (id) {
      payload.id = id;
      res = await fetch(`/api/events/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    } else {
      res = await fetch('/api/events', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
    }

    if (res.ok) {
      closeModal();
      await loadStats();
      await loadSchedule();
    } else {
      const err = await res.json();
      alert('Error saving event: ' + (err.detail || 'Unknown error'));
    }
  } catch (err) {
    alert('Failed to connect: ' + err.message);
  }
}

async function deleteEvent(id) {
  try {
    const res = await fetch(`/api/events/${id}`, { method: 'DELETE' });
    if (res.ok) {
      await loadStats();
      await loadSchedule();
    } else {
      alert('Failed to delete event');
    }
  } catch (err) {
    alert('Error deleting event: ' + err.message);
  }
}
