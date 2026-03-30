// Configuration
const API_BASE_URL = 'http://127.0.0.1:8000/api';

// UI Elements
const viewWelcome = document.getElementById('welcome-view');
const viewProcessing = document.getElementById('processing-view');
const viewNote = document.getElementById('note-view');
const notesListEl = document.getElementById('notes-list');

// Buttons & Actions
const btnNewNote = document.getElementById('new-note-btn');
const btnRecord = document.getElementById('record-btn');
const recordText = document.getElementById('record-text');
const recordingStatus = document.getElementById('recording-status');
const recordingTimeEl = document.getElementById('recording-time');
const btnDelete = document.getElementById('delete-btn');
const btnExportMd = document.getElementById('export-md-btn');
const btnUpload = document.getElementById('upload-btn');
const uploadInput = document.getElementById('upload-input');
const backendStatusChip = document.getElementById('backend-status');
const ollamaStatusChip = document.getElementById('ollama-status');

// Note Content Elements
const noteTitle = document.getElementById('note-title');
const noteTags = document.getElementById('note-tags');
const noteSummary = document.getElementById('note-summary');
const noteContent = document.getElementById('note-content');
const rawTranscript = document.getElementById('raw-transcript');
const mindmapContainer = document.getElementById('mindmap-container');
const processingStatusText = document.getElementById('processing-text');
const processingSubstatusText = document.getElementById('processing-subtext');
const fallbackBadge = document.getElementById('fallback-badge');
const mindmapGraph = document.getElementById('mindmap-graph');

// State
let selectedNoteId = null;
let mediaRecorder = null;
let audioChunks = [];
let recordingInterval = null;
let recordingSeconds = 0;
let pendingFallbackFlag = false;
const noteFallbackFlags = {};

// Init
async function init() {
  await checkBackendConnection();
  await fetchNotes();
}

// --- Health & Connection Checks ---

async function checkBackendConnection() {
  try {
    const res = await fetch(`${API_BASE_URL}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();
    setStatusChip(backendStatusChip, 'ok', 'API reachable');

    const ollamaStatus = data.components?.ollama;
    if (ollamaStatus === 'ok') {
      setStatusChip(ollamaStatusChip, 'ok', 'Ollama responding');
    } else if (ollamaStatus === 'error') {
      setStatusChip(ollamaStatusChip, 'warn', data.ollama_error || 'Ollama unavailable');
    } else {
      setStatusChip(ollamaStatusChip, 'warn', 'Ollama status unknown');
    }
  } catch (error) {
    console.warn("Backend connection warning:", error);
    setStatusChip(backendStatusChip, 'error', `Backend issue: ${error.message}`);
    setStatusChip(ollamaStatusChip, 'error', 'Waiting for backend');
  }
}

function setStatusChip(el, state, tooltip) {
  const base = 'status-chip';
  const cls = {
    ok: 'status-ok',
    warn: 'status-warn',
    error: 'status-error',
    pending: 'status-pending'
  }[state] || 'status-pending';
  el.className = `${base} ${cls}`;
  if (tooltip) el.title = tooltip;
}

// --- API Calls ---

async function fetchNotes() {
  try {
    const res = await fetch(`${API_BASE_URL}/notes`);
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    const data = await res.json();
    renderSidebarNotes(data.notes || []);
  } catch (error) {
    console.error("Failed to fetch notes:", error);
    renderSidebarNotes([]);
    showErrorNotification("Could not load notes. Backend may be offline.");
  }
}

async function fetchNoteDetails(id) {
  try {
    showView(viewProcessing);
    processingStatusText.innerText = "Loading Note...";
    processingSubstatusText.innerText = "Retrieving from database...";
    
    const res = await fetch(`${API_BASE_URL}/notes/${id}`);
    if (!res.ok) {
      throw new Error(`Failed to load note: HTTP ${res.status}`);
    }
    
    const note = await res.json();
    
    selectedNoteId = note.id;
    noteFallbackFlags[note.id] = note.used_fallback;
    renderNote(note);
    showView(viewNote);
  } catch (error) {
    console.error("Failed to fetch note:", error);
    showErrorNotification(`Could not load note: ${error.message}`);
    showView(viewWelcome);
  }
}

// --- Recording Logic ---

btnRecord.addEventListener('click', async () => {
  if (mediaRecorder && mediaRecorder.state === 'recording') {
    stopRecording();
  } else {
    await startRecording();
  }
});

async function startRecording() {
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error("Microphone API not supported in this browser. Use Chrome, Firefox, or Edge.");
    }
    
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Use WebM implementation for browser compatibility
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm;codecs=opus' });
    audioChunks = [];

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = processAudioBlob;

    mediaRecorder.start();
    
    // UI Updates
    btnRecord.classList.add('recording');
    recordText.innerText = "Stop Recording";
    recordingStatus.classList.remove('hidden');
    recordingSeconds = 0;
    
    recordingInterval = setInterval(() => {
      recordingSeconds++;
      const mins = Math.floor(recordingSeconds / 60).toString().padStart(2, '0');
      const secs = (recordingSeconds % 60).toString().padStart(2, '0');
      recordingTimeEl.innerText = `${mins}:${secs}`;
    }, 1000);

  } catch (err) {
    console.error("Could not start recording:", err);
    
    let errorMsg = "Microphone access required to record notes.";
    if (err.name === 'NotAllowedError') {
      errorMsg = "Microphone access denied. Please allow access and try again.";
    } else if (err.name === 'NotFoundError') {
      errorMsg = "No microphone found. Please connect a microphone.";
    } else if (err.name === 'NotSupportedError') {
      errorMsg = "Your browser doesn't support audio recording. Use Chrome, Firefox, or Edge.";
    }
    
    showErrorNotification(errorMsg);
  }
}

// --- File Upload Logic ---

btnUpload.addEventListener('click', () => uploadInput.click());

uploadInput.addEventListener('change', async (event) => {
  const file = event.target.files?.[0];
  if (!file) return;
  await handleFileUpload(file);
  uploadInput.value = '';
});

async function handleFileUpload(file) {
  showView(viewProcessing);
  processingStatusText.innerText = "Processing File...";
  processingSubstatusText.innerText = "Extracting text and structuring notes...";

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE_URL}/notes/upload`, {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      let detail = `HTTP ${res.status}`;
      try {
        const errData = await res.json();
        detail = errData.detail || detail;
      } catch (_) {
        // ignore JSON parse errors
      }
      throw new Error(detail);
    }

    const note = await res.json();
    await fetchNotes();
    await fetchNoteDetails(note.id);
  } catch (err) {
    console.error("File upload failed:", err);
    showErrorNotification(`Could not process file: ${err.message}`);
    showView(viewWelcome);
  }
}

function stopRecording() {
  if (mediaRecorder) {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(track => track.stop());
    
    clearInterval(recordingInterval);
    btnRecord.classList.remove('recording');
    recordText.innerText = "Start Recording";
    recordingStatus.classList.add('hidden');
    recordingTimeEl.innerText = "00:00";
  }
}

async function processAudioBlob() {
    showView(viewProcessing);
    processingStatusText.innerText = "Transcribing Audio...";
    processingSubstatusText.innerText = "Running local Whisper model...";

    const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
    const formData = new FormData();
    formData.append('audio', audioBlob, 'recording.webm');

    try {
        // Check backend connection first
        try {
          const healthRes = await fetch(`${API_BASE_URL}/health`);
            if (!healthRes.ok) throw new Error("Backend not responding");
        } catch (e) {
            throw new Error(`Backend error: ${e.message}. Make sure it's running on http://127.0.0.1:8000`);
        }

        // Step 1: Transcribe
        processingStatusText.innerText = "Transcribing Audio...";
        processingSubstatusText.innerText = "Running local Whisper model (this may take ~10-30 seconds)...";
        
        const transcribeRes = await fetch(`${API_BASE_URL}/transcribe`, {
            method: 'POST',
            body: formData
        });
        
        if (!transcribeRes.ok) {
            const errData = await transcribeRes.json();
            throw new Error(`Transcription failed: ${errData.detail || transcribeRes.statusText}`);
        }
        
        const transcribeData = await transcribeRes.json();
        const transcriptText = transcribeData.text;

        if (!transcriptText || transcriptText.trim() === '') {
            throw new Error("No speech detected in audio. Please record a longer audio sample.");
        }

        // Step 2: Structure with LLM
        processingStatusText.innerText = "Structuring Notes...";
        processingSubstatusText.innerText = "Analyzing with Ollama LLM. Make sure Ollama is running: ollama serve";

        const structureRes = await fetch(`${API_BASE_URL}/notes/structure`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ transcript: transcriptText })
        });
        
        if (!structureRes.ok) {
            const errData = await structureRes.json();
            throw new Error(`Structuring failed: ${errData.detail || structureRes.statusText}`);
        }
        
        const structuredData = await structureRes.json();
        pendingFallbackFlag = Boolean(structuredData.used_fallback);

        // Step 3: Save to DB
        processingStatusText.innerText = "Saving to Database...";
        processingSubstatusText.innerText = "Finalizing note...";
        
        const saveRes = await fetch(`${API_BASE_URL}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: structuredData.title || "Untitled Note",
                raw_transcript: transcriptText,
                structured_notes: structuredData.structured_notes || "",
                summary: structuredData.summary || "",
                bullet_points: structuredData.bullet_points || [],
                headings: structuredData.headings || [],
                mind_map: structuredData.mind_map || {},
            tags: structuredData.tags || [],
            used_fallback: pendingFallbackFlag
            })
        });

        if (!saveRes.ok) {
            const errData = await saveRes.json();
            throw new Error(`Failed to save note: ${errData.detail || saveRes.statusText}`);
        }

        const newNoteData = await saveRes.json();
  noteFallbackFlags[newNoteData.id] = pendingFallbackFlag;
  pendingFallbackFlag = false;
        
        // Step 4: Refresh UI
        await fetchNotes();
        await fetchNoteDetails(newNoteData.id);

    } catch (err) {
        console.error("Processing error:", err);
        showErrorNotification(`Error: ${err.message}`);
        showView(viewWelcome);
    }
}

function showErrorNotification(message) {
    // Show error in console and as alert for now
    console.error(message);
    if (confirm(`${message}\n\nOpen browser console (F12) for more details?`)) {
        // Attempt to open dev tools (most browsers will ignore this for security)
        console.log("Error details visible in console.");
    }
}

// --- UI Rendering ---

// Simple HTML sanitizer to prevent XSS
function sanitizeHTML(html) {
  const div = document.createElement('div');
  div.textContent = html;
  return div.innerHTML;
}

function showView(viewEl) {
  viewWelcome.classList.add('hidden');
  viewProcessing.classList.add('hidden');
  viewNote.classList.add('hidden');
  viewEl.classList.remove('hidden');
}

function renderSidebarNotes(notes) {
  notesListEl.innerHTML = '';
  notes.forEach(note => {
    const li = document.createElement('li');
    li.className = `note-item ${note.id === selectedNoteId ? 'active' : ''}`;
    
    // Format date
    const dateObj = new Date(note.created_at || Date.now());
    const dateStr = dateObj.toLocaleDateString();

    li.innerHTML = `
      <div class="note-item-main">
        <div>
          <div class="note-item-title">${note.title || 'Untitled Note'}</div>
          <div class="note-item-date">${dateStr}</div>
        </div>
        <button class="delete-note-btn" aria-label="Delete note" title="Delete note">×</button>
      </div>
    `;
    
    const deleteBtn = li.querySelector('.delete-note-btn');
    deleteBtn.addEventListener('click', async (event) => {
      event.stopPropagation();
      if (!confirm('Delete this note? This cannot be undone.')) return;
      try {
        const res = await fetch(`${API_BASE_URL}/notes/${note.id}`, { method: 'DELETE' });
        if (!res.ok) throw new Error(`Delete failed: HTTP ${res.status}`);
        if (selectedNoteId === note.id) selectedNoteId = null;
        await fetchNotes();
        showView(viewWelcome);
      } catch (err) {
        console.error('Delete failed:', err);
        showErrorNotification(`Could not delete note: ${err.message}`);
      }
    });

    li.addEventListener('click', () => {
      // update active class
      document.querySelectorAll('.note-item').forEach(el => el.classList.remove('active'));
      li.classList.add('active');
      fetchNoteDetails(note.id);
    });
    
    notesListEl.appendChild(li);
  });
}

function renderNote(note) {
  noteTitle.innerText = note.title;
  noteSummary.innerText = note.summary || "No summary available.";
  rawTranscript.innerText = note.raw_transcript;

  const usedFallback = noteFallbackFlags[note.id] || note.used_fallback;
  if (usedFallback) {
    fallbackBadge.classList.remove('hidden');
  } else {
    fallbackBadge.classList.add('hidden');
  }
  
  // Parse Markdown to HTML
  if (note.structured_notes) {
    noteContent.innerHTML = marked.parse(note.structured_notes);
  } else {
    noteContent.innerHTML = "<p>No structured notes generated.</p>";
  }

  // Tags
  noteTags.innerHTML = '';
  const tags = note.tags || [];
  tags.forEach(tag => {
    const t = document.createElement('span');
    t.className = 'tag';
    t.innerText = tag;
    noteTags.appendChild(t);
  });

  // Render Mindmap
  mindmapContainer.innerHTML = '';
  if (note.mind_map) {
     renderMindMapNode(note.mind_map, mindmapContainer);
      renderMindMapGraph(note.mind_map);
    } else {
      renderMindMapGraph(null);
  }
}

function renderMindMapNode(node, containerElement) {
    if (!node || !node.label) return;
    
    const li = document.createElement('li');
    const labelSpan = document.createElement('span');
    labelSpan.className = 'mindmap-node-label';
    labelSpan.innerText = node.label;
    li.appendChild(labelSpan);
    
    if (node.children && node.children.length > 0) {
        const ul = document.createElement('ul');
        ul.className = 'mindmap-children';
        node.children.forEach(child => {
            renderMindMapNode(child, ul);
        });
        li.appendChild(ul);
    }
    
    containerElement.appendChild(li);
}

function renderMindMapGraph(mindMap) {
  if (!mindmapGraph) return;
  mindmapGraph.innerHTML = '';

  if (!mindMap || !window.d3) {
    const empty = document.createElement('div');
    empty.className = 'graph-empty';
    empty.innerText = mindMap ? 'Mind map ready, but D3 not loaded.' : 'No mind map data.';
    mindmapGraph.appendChild(empty);
    return;
  }

  const { nodes, links } = buildGraphData(mindMap);
  const width = mindmapGraph.clientWidth || 320;
  const height = mindmapGraph.clientHeight || 240;

  const svg = d3.select(mindmapGraph)
    .append('svg')
    .attr('width', width)
    .attr('height', height);

  const simulation = d3.forceSimulation(nodes)
    .force('link', d3.forceLink(links).id(d => d.id).distance(70))
    .force('charge', d3.forceManyBody().strength(-120))
    .force('center', d3.forceCenter(width / 2, height / 2))
    .force('collision', d3.forceCollide(28));

  const link = svg.append('g')
    .attr('stroke', '#334155')
    .attr('stroke-width', 1.2)
    .selectAll('line')
    .data(links)
    .enter()
    .append('line');

  const node = svg.append('g')
    .selectAll('g')
    .data(nodes)
    .enter()
    .append('g')
    .call(drag(simulation));

  node.append('circle')
    .attr('r', 14)
    .attr('fill', d => d.level === 0 ? '#6366f1' : '#1f2937')
    .attr('stroke', '#94a3b8')
    .attr('stroke-width', 1.2);

  node.append('text')
    .text(d => d.label)
    .attr('x', 18)
    .attr('y', 4)
    .attr('fill', '#e2e8f0')
    .attr('font-size', 12)
    .attr('font-family', 'Inter, sans-serif');

  simulation.on('tick', () => {
    link
      .attr('x1', d => d.source.x)
      .attr('y1', d => d.source.y)
      .attr('x2', d => d.target.x)
      .attr('y2', d => d.target.y);

    node.attr('transform', d => `translate(${d.x},${d.y})`);
  });
}

function buildGraphData(root) {
  const nodes = [];
  const links = [];

  function walk(node, parentId = null, level = 0) {
    if (!node) return;
    const id = node.id || `${node.label}-${nodes.length}`;
    nodes.push({ id, label: node.label || 'Node', level });
    if (parentId) {
      links.push({ source: parentId, target: id });
    }
    (node.children || []).forEach(child => walk(child, id, level + 1));
  }

  walk(root, null, 0);
  return { nodes, links };
}

function drag(simulation) {
  function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
  }

  function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
  }

  function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
  }

  return d3.drag()
    .on('start', dragstarted)
    .on('drag', dragged)
    .on('end', dragended);
}

// --- Other Actions ---

btnNewNote.addEventListener('click', () => {
  selectedNoteId = null;
  document.querySelectorAll('.note-item').forEach(el => el.classList.remove('active'));
  showView(viewWelcome);
});

btnDelete.addEventListener('click', async () => {
    if (!selectedNoteId) return;
    if (confirm("Are you sure you want to delete this note? This cannot be undone.")) {
        try {
            const res = await fetch(`${API_BASE_URL}/notes/${selectedNoteId}`, { method: 'DELETE' });
            if (!res.ok) throw new Error(`Delete failed: HTTP ${res.status}`);
            
            selectedNoteId = null;
            await fetchNotes();
            showView(viewWelcome);
        } catch(err) {
            console.error("Delete failed:", err);
            showErrorNotification(`Could not delete note: ${err.message}`);
        }
    }
});

btnExportMd.addEventListener('click', async () => {
    if (!selectedNoteId) return;
    try {
        window.location.href = `${API_BASE_URL}/export/${selectedNoteId}/markdown`;
    } catch(err) {
        console.error("Export failed:", err);
        showErrorNotification(`Could not export note: ${err.message}`);
    }
});

// Title update (auto save)
noteTitle.addEventListener('blur', async () => {
    if (!selectedNoteId) return;
    
    const newTitle = noteTitle.innerText.trim();
    if (!newTitle) {
        noteTitle.innerText = "Untitled Note";
        return;
    }
    
    try {
        const res = await fetch(`${API_BASE_URL}/notes/${selectedNoteId}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ title: newTitle })
        });
        if (!res.ok) throw new Error(`Save failed: HTTP ${res.status}`);
        
        await fetchNotes(); // Update sidebar list
    } catch(err) {
        console.error("Title save failed:", err);
        showErrorNotification(`Could not save title: ${err.message}`);
    }
});

// Run Init
init();
