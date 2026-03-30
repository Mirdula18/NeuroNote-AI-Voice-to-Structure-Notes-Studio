# NeuroNote AI v2

NeuroNote AI turns voice and text into structured notes.
It records or uploads content, transcribes with Whisper, structures notes with Ollama, stores results in SQLite, and exports Markdown/JSON.

## Features
- Voice recording in browser and upload to backend for transcription.
- Text and DOCX upload support (`.txt`, `.docx`).
- LLM note structuring (title, summary, bullets, headings, tags, mind map).
- Full note CRUD with SQLite persistence.
- Export note as Markdown or JSON.
- Health endpoint with DB + Ollama status.

## Tech Stack
- Backend: FastAPI, Async SQLAlchemy, SQLite
- ASR: faster-whisper
- LLM: Ollama (`llama3:latest` by default)
- Frontend: Vanilla JavaScript

## Prerequisites
- Python 3.10+
- Ollama installed and available on your PATH
- A modern browser (Chrome/Edge/Firefox) for microphone recording

## Quick Start (Windows)
```bash
# 1) From repo root, create and activate venv
python -m venv .venv
.venv\Scripts\activate

# 2) Install dependencies
pip install -r backend/requirements.txt

# 3) Create local env file
copy .env.example .env

# 4) Start Ollama and pull the default model (first time only)
ollama serve
ollama pull llama3:latest

# 5) Start backend (new terminal)
.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# 6) Start frontend static server (new terminal)
.venv\Scripts\python.exe -m http.server 8080 --directory frontend
```

Open:
- Frontend: http://127.0.0.1:8080
- API docs: http://127.0.0.1:8000/docs

## Quick Start (macOS/Linux)
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
cp .env.example .env

ollama serve
ollama pull llama3:latest

python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
python -m http.server 8080 --directory frontend
```

## Configuration
Create `.env` from `.env.example`.

```env
WHISPER_MODEL=base
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest
DATABASE_URL=sqlite+aiosqlite:///./neuronote.db
CORS_ORIGINS=["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:5000", "http://127.0.0.1:8080"]
```

Notes:
- Upload size limit for `POST /api/notes/upload` is currently 5 MB.
- Frontend is configured to call backend at `http://127.0.0.1:8000/api`.

## API Endpoints
- `GET /api/health` - Service, database, and Ollama health
- `POST /api/transcribe` - Multipart audio upload (`audio`)
- `POST /api/notes/structure` - Structure transcript text
- `POST /api/notes` - Create note
- `GET /api/notes` - List notes (`skip`, `limit`)
- `GET /api/notes/{id}` - Get note details
- `PUT /api/notes/{id}` - Update note
- `DELETE /api/notes/{id}` - Delete note
- `POST /api/notes/upload` - Upload and structure `.txt` or `.docx`
- `GET /api/export/{id}/markdown` - Export Markdown
- `GET /api/export/{id}/json` - Export JSON

## Makefile Commands (Optional)
```bash
make fmt           # black + isort + ruff format (backend)
make lint          # ruff check (backend)
make test          # pytest (backend)
make frontend-fmt  # prettier (frontend)
make frontend-lint # eslint (frontend)
make dev-backend   # uvicorn with reload
make dev-frontend  # python http.server on 8080
```

## Troubleshooting
- `Backend issue` in UI: ensure backend is running on `127.0.0.1:8000`.
- `Ollama unavailable` in health check: start Ollama (`ollama serve`) and verify model exists (`ollama list`).
- Recording fails in browser: allow microphone permission and use a supported browser.
- Slow first transcription: Whisper and model warm-up may take longer on first run.

## License
This project is licensed under the MIT License. See `LICENSE`.
