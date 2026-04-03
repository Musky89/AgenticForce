# AgenticForce — Agent Instructions

## Cursor Cloud specific instructions

### Services

| Service | Command | Port | Notes |
|---------|---------|------|-------|
| FastAPI Backend | `cd backend && source venv/bin/activate && uvicorn app.main:app --reload --port 8000` | 8000 | Auto-creates SQLite DB on first start |
| Next.js Frontend | `cd frontend && npm run dev` | 3000 | Proxies API calls to backend at `localhost:8000/api` |

### Caveats

- The backend requires `python3.12-venv` system package to create a virtualenv. The update script handles this.
- Backend `.env` must exist before starting uvicorn. Copy from `.env.example` if missing: `cp backend/.env.example backend/.env`
- `OPENAI_API_KEY` in `backend/.env` is needed only for running the AI agent pipeline. The app starts and CRUD operations work without it.
- SQLite database (`agenticforce.db`) is auto-created in `backend/` on first startup via the FastAPI lifespan handler — no migrations needed.
- Frontend uses `package-lock.json` → use `npm install` (not pnpm/yarn).

### Lint / Type-check / Build

See `frontend/package.json` scripts. Key commands:
- **Lint**: `cd frontend && npx eslint .`
- **Type-check**: `cd frontend && npx tsc --noEmit`
- **Build**: `cd frontend && npm run build`

No backend linter is configured in the repo.
