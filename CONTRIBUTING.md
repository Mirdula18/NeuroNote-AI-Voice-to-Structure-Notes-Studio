# Contributing to NeuroNote AI v2

## Setup
1) Clone repo and create venv
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r backend/requirements.txt
```
2) Copy env
```bash
copy .env.example .env  # adjust if needed
```
3) Start services (separate terminals)
```bash
ollama serve
ollama pull llama3:latest
cd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
cd frontend && python -m http.server 8080
```

## Commands
```bash
make fmt           # black + isort + ruff (backend)
make lint          # ruff
make test          # pytest
make frontend-fmt  # prettier
make frontend-lint # eslint
```
(Use scripts directly if make is unavailable.)

## Style
- Python: black, isort, ruff (no unused imports, keep async/await clean).
- JS/CSS/HTML: prettier; eslint for basic checks.
- Keep comments minimal and meaningful.

## Testing
- Add/extend pytest cases for API routes (health, notes CRUD, upload, export, structure with mocked LLM).
- Use httpx AsyncClient + pytest-asyncio for FastAPI tests.

## PR guidelines
- Small, focused changes; include tests when adding behavior.
- Update README/CONTRIBUTING if commands or flows change.
- Note any new env vars or limits (upload size, timeouts).

## Troubleshooting
- Ollama missing: ensure `ollama serve` and model pulled; verify `OLLAMA_BASE_URL`.
- Whisper errors: check model availability and audio format; confirm dependencies installed (torch, soundfile).
- CORS: backend allows localhost/127.0.0.1 by default; adjust CORS_ORIGINS if serving elsewhere.
