# AGENTS.md

## Cursor Cloud specific instructions

### Architecture

AgenticForce is a two-service app: a **Python/FastAPI backend** (port 8000) and a **Next.js frontend** (port 3000). Data is stored in SQLite (auto-created on startup, no external DB needed).

### Running services

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

### Key dev gotchas

- **passlib + bcrypt incompatibility**: `passlib` does not work with `bcrypt>=5`. The `requirements.txt` pins `bcrypt>=4,<5` to avoid a `ValueError` on password hashing. Do not remove this pin.
- **Backend .env**: Copy `backend/.env.example` to `backend/.env` before starting the backend. The app runs without API keys but AI features (agents, image generation) require `OPENAI_API_KEY` at minimum.
- **First user setup**: POST to `/api/auth/setup` with `{"email": "...", "password": "..."}` to create the first user. This endpoint only works when no users exist. After that, use `/api/auth/login`.
- **No automated test suite**: The repo currently has no test files. Validation is done via API calls and manual UI testing.

### Lint / Build

```bash
# Frontend lint (eslint, 0 errors expected, warnings OK)
cd frontend && npx eslint .

# Frontend build (validates TypeScript + Next.js compilation)
cd frontend && npm run build

# Backend import check
cd backend && source venv/bin/activate && python -c "from app.main import app"
```
