PYTHON := .venv/Scripts/python.exe
PIP := .venv/Scripts/pip.exe
BACKEND := backend
FRONTEND := frontend

fmt:
	$(PYTHON) -m ruff format $(BACKEND)
	$(PYTHON) -m ruff check --fix $(BACKEND)

lint:
	$(PYTHON) -m ruff check $(BACKEND)

test:
	cd $(BACKEND) && $(PYTHON) -m pytest

frontend-fmt:
	cd $(FRONTEND) && npx prettier --write "**/*.{js,css,html}"

frontend-lint:
	cd $(FRONTEND) && npx eslint "**/*.js"

dev-backend:
	cd $(BACKEND) && $(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

dev-frontend:
	$(PYTHON) -m http.server 8080 --directory $(FRONTEND)

.PHONY: fmt lint test frontend-fmt frontend-lint dev-backend dev-frontend
