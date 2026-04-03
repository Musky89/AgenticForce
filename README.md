# AgenticForce

A full-stack AI-powered creative agency platform. Six specialized AI agents work as your creative team — from research to final creative direction — producing client-ready deliverables you review and refine.

## Architecture

```
┌─────────────────────────────────────────────┐
│                  Frontend                    │
│         Next.js 16 + shadcn/ui              │
│    Dashboard │ Clients │ Projects │ Review   │
└────────────────────┬────────────────────────┘
                     │ REST API
┌────────────────────▼────────────────────────┐
│                  Backend                     │
│              FastAPI (async)                 │
├──────────────────────────────────────────────┤
│           Agent Pipeline Engine              │
│  Researcher → Strategist → Brand Voice →    │
│  Copywriter → Art Director → Creative Dir   │
├──────────────────────────────────────────────┤
│          SQLite + SQLAlchemy (async)         │
└──────────────────────────────────────────────┘
```

## Agent Team

| Agent | Role | Output |
|-------|------|--------|
| **Researcher** | Market research, competitive analysis, audience insights | Research report with opportunities |
| **Strategist** | Creative strategy, positioning, campaign frameworks | Strategic brief with message hierarchy |
| **Brand Voice** | Voice architecture, language guidelines, tone system | Voice framework with examples |
| **Copywriter** | Headlines, body copy, social, email, ad copy | Multi-format copy deliverables |
| **Art Director** | Visual direction, design systems, asset specs | Visual brief with color/type/layout |
| **Creative Director** | Reviews all outputs, synthesizes, elevates | Client-ready creative package |

Each agent builds on the previous agents' outputs, creating a coherent creative pipeline.

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- OpenAI API key

### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Start the server (auto-creates database)
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install

# Start development server
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

## Workflow

1. **Add a Client** — Enter client details, brand guidelines, tone keywords, target audience
2. **Create a Project** — Associate it with a client
3. **Write the Brief** — Define objective, deliverables, audience, key messages, tone, constraints
4. **Run the Pipeline** — Execute all 6 agents sequentially, or run them individually
5. **Review Deliverables** — Read agent outputs, approve or provide feedback
6. **Deliver** — Use the Creative Director's final package for client presentation

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/health` | Health check |
| `GET` | `/api/dashboard/stats` | Dashboard statistics |
| `GET/POST` | `/api/clients` | List / create clients |
| `GET/PATCH/DELETE` | `/api/clients/:id` | Get / update / delete client |
| `GET/POST` | `/api/projects` | List / create projects |
| `GET/PATCH/DELETE` | `/api/projects/:id` | Get / update / delete project |
| `POST` | `/api/briefs` | Create brief |
| `GET` | `/api/briefs/project/:id` | Get brief by project |
| `PATCH` | `/api/briefs/:id` | Update brief |
| `GET` | `/api/agents/roles` | List agent roles |
| `POST` | `/api/agents/run` | Run single agent |
| `POST` | `/api/agents/pipeline` | Run full pipeline |
| `GET` | `/api/agents/runs` | List agent runs |
| `GET/POST` | `/api/deliverables` | List / create deliverables |
| `GET/PATCH/DELETE` | `/api/deliverables/:id` | Get / update / delete deliverable |

## Tech Stack

**Backend:** FastAPI, SQLAlchemy (async), SQLite, OpenAI API, Pydantic v2

**Frontend:** Next.js 16, TypeScript, Tailwind CSS v4, shadcn/ui, Lucide Icons
