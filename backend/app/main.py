from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.api import (
    clients, projects, briefs, agents, deliverables, dashboard,
    images, brand_bible, blueprints, lora, orchestrator, review, export,
    auth, events, creative_memory,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="AgenticForce",
    description="Agentic Creative Agency — AI-powered creative production platform with Brand Bible, LoRA, and 6-stage pipeline",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(brand_bible.router, prefix="/api")
app.include_router(blueprints.router, prefix="/api")
app.include_router(lora.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(briefs.router, prefix="/api")
app.include_router(agents.router, prefix="/api")
app.include_router(deliverables.router, prefix="/api")
app.include_router(images.router, prefix="/api")
app.include_router(orchestrator.router, prefix="/api")
app.include_router(review.router, prefix="/api")
app.include_router(export.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(creative_memory.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "AgenticForce", "version": "2.0.0"}
