# NeuroNote AI v2

Voice-to-structured-notes: record or upload audio/txt/docx, transcribe with Whisper, structure with Ollama, store in SQLite, and export Markdown/JSON.

## Stack
- Backend: FastAPI, Async SQLAlchemy, SQLite
- LLM: Ollama (default `llama3:latest`)
- ASR: faster-whisper
- Frontend: Vanilla JS + marked, served via simple HTTP

## Quickstart
```bash
# 0) From repo root
# 1) Python env
python -m venv .venv
.venv/Scripts/activate  # win
pip install -r backend/requirements.txt

# 2) Config
copy .env.example .env  # adjust if needed

# 3) Run Ollama
ollama serve
ollama pull llama3:latest

# 4) Backend (from repo root)
.venv/Scripts/python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
# or: (cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload)

# 5) Frontend (from repo root)
.venv/Scripts/python.exe -m http.server 8080 --directory frontend
# open http://127.0.0.1:8080
```

## Makefile targets (optional)
```
make fmt           # black + isort + ruff (backend)
make lint          # ruff
make test          # pytest
make frontend-fmt  # prettier
make frontend-lint # eslint
make dev-backend   # uvicorn with reload
make dev-frontend  # http.server 8080
```

## Key endpoints
- GET  /api/health – backend health
- POST /api/transcribe – multipart `audio`
- POST /api/notes/structure – { transcript, custom_prompt? }
- POST /api/notes – create structured note
- GET  /api/notes – list (supports `skip`, `limit`)
- GET  /api/notes/{id} – detail
- PUT  /api/notes/{id} – update
- DELETE /api/notes/{id} – delete
- POST /api/notes/upload – multipart `file` (txt/docx)
- GET /api/export/{id}/markdown – download Markdown
- GET /api/export/{id}/json – download JSON

## Environment
```
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
DATABASE_URL=sqlite+aiosqlite:///./neuronote.db
CORS_ORIGINS=["*"]
UPLOAD_MAX_MB=10   # (documented; enforce via server/client if added)
LLM_TIMEOUT=120
```

## Developer notes
- API docs: http://127.0.0.1:8000/docs
- Frontend expects backend at http://127.0.0.1:8000
- Upload field name: `file`; oversized uploads should return 413 (add limit if desired).
- Fallback structuring runs when Ollama is unreachable; surface a badge in UI if you extend it.

## Suggested improvements (tracked from planning)
- Status indicator for backend/Ollama; retry-once LLM with explicit fallback badge.
- Upload size limit + progress UI; chunk/stream for >10MB.
- Tag search/filter; pagination or lazy-load in sidebar.
- Copy Markdown + Download JSON buttons inline.
- Collapse/expand mind map; empty state handling.
- Better error messages for missing Ollama/Whisper and timeouts.

## License
Add MIT or Apache-2.0 (not yet included).
