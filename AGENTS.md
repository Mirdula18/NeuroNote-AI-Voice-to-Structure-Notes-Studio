# AGENTS.md — NeuroNote AI Audit Tasks

Generated from full codebase audit on 2026-07-15.
Last updated: 2026-07-15 (all tasks completed).

---

## CRITICAL — Security

- [x] **#1 XSS via `marked.parse`** — `frontend/app.js:426` renders LLM output as raw HTML. A malicious transcript could inject `<script>` tags. `sanitizeHTML()` exists at line 352 but is never used for structured notes. Sidebar titles at line 378 also use unsanitized `.innerHTML`. Fix: run all `marked.parse` output through a DOMPurify or equivalent sanitizer before setting `innerHTML`.

- [x] **#2 Prompt injection** — `backend/app/services/llm_service.py:74` injects user transcript directly into the system prompt via f-string. The `custom_prompt` field lets any caller override the entire system prompt. Fix: wrap user input in clear delimiters (`<TRANSCRIPT>...</TRANSCRIPT>`) and validate/reject `custom_prompt` overrides from untrusted callers.

- [x] **#3 `.env` files present** — Both `./.env` and `./backend/.env` exist on disk. While `.gitignore` lists `.env`, these may have been committed before the rule existed. Fix: verify git history, ensure both are untracked.

- [x] **#4 Inconsistent `.env` files** — Root `.env` has `OLLAMA_MODEL=llama3.2`, backend `.env` has `llama3:latest`. Root `.env` has CORS origins including `:5000`, backend has `:8080`. The backend only reads `backend/.env`. Fix: align both files to the same values, remove the root `.env` or make it a symlink/copy.

---

## HIGH — Bugs

- [x] **#5 Double commit on write routes** — `get_db()` in `database.py:30` commits after the route yields. But `routes/notes.py` also calls `await db.commit()` at lines 52, 99, 155, 173. Fix: remove all explicit `await db.commit()` calls from routes and let the dependency handle it.

- [x] **#6 Total count is O(n)** — `routes/notes.py:117-119` fetches all note IDs then counts in Python. Fix: use `select(func.count(Note.id))` with `select_from(Note)`.

- [x] **#7 `updated_at` never updates** — `models/note.py:23` uses `onupdate=func.now()` which does not fire with async SQLAlchemy `setattr` patterns. Fix: explicitly set `updated_at` in update routes using `datetime.now(timezone.utc)` or use SQLAlchemy event listeners.

- [x] **#8 Malformed SVG tag** — `frontend/index.html:117` has `< x1="12" ...` missing the `line` tag name. Fix: change to `<line x1="12" x2="12" y1="19" y2="22"/>`.

---

## MEDIUM — Security & Reliability

- [x] **#9 Error messages leak internals** — Multiple routes return raw `str(exc)` to clients: `routes/notes.py:32,76,84`, `main.py:59,70`. Fix: return generic error messages to clients, log details server-side only.

- [x] **#10 No upload size limit on `/api/transcribe`** — `routes/transcribe.py` accepts arbitrary audio bytes. Fix: add a size check (e.g., 25 MB) before processing.

- [x] **#11 Whisper model blocks event loop** — `services/whisper_service.py:23-28` loads `WhisperModel()` synchronously during the first request. Fix: preload the model during app startup in the lifespan context manager.

- [x] **#12 Overly permissive CORS** — `main.py:34` regex allows any port on localhost with `allow_credentials=True`. Fix: make CORS origins strictly configurable via env var, disable regex in production.

---

## LOW — Code Quality

- [x] **#13 `import re` inside function** — `services/llm_service.py:123` imports `re` inside `_parse_llm_json()`. Fix: move to module-level import.

- [x] **#14 Unused `MindMapNode` schema** — `schemas.py:23-26` defines `MindMapNode` but it is never referenced. Fix: remove the class.

- [x] **#15 Unused `transcribe_audio_stream`** — `services/whisper_service.py:91-96` is defined but never called. Fix: remove the function.

- [x] **#16 Hardcoded API URL** — `frontend/app.js:2` hardcodes `http://127.0.0.1:8000/api`. Fix: make configurable via a global or config element in HTML.

- [x] **#17 `confirm()` for error UX** — `frontend/app.js:343` uses `confirm()` dialog. Fix: replace with a toast/notification component (lower priority).

- [x] **#18 `numpy<2.0.0` pin** — `requirements.txt:18` may conflict with newer packages. Fix: relax to `numpy>=1.24.0,<3.0.0` or remove if not directly used.

- [x] **#19 Zero test files** — Makefile references `pytest` but no tests exist. Fix: add at least smoke tests for health, CRUD, and export endpoints (lower priority, out of scope for this pass).

- [x] **#20 No logging configuration** — Backend uses `logging.getLogger` but never configures level/format. Fix: add basic logging setup in `main.py` lifespan.

- [x] **#21 Makefile `fmt` redundancy** — `make fmt` runs black, isort, AND ruff format (ruff format subsumes black). Fix: keep only ruff.

---

## Agent Workflow

When fixing, follow this order:
1. Security-critical items first (#1, #2)
2. Environment/config alignment (#3, #4)
3. Backend bugs (#5, #6, #7)
4. Frontend bugs (#8)
5. Medium reliability (#9, #10, #11, #12)
6. Code quality cleanups (#13–#21)

All 21 tasks completed.
