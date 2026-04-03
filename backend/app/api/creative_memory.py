"""Creative Memory REST API — CRUD + performance ingestion + client insights."""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import CreativeMemory, GeneratedImage, Deliverable
from app.schemas.schemas import CreativeMemoryCreate, CreativeMemoryOut
from app.services.creative_memory import store_memory, store_performance_data

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/creative-memory", tags=["creative-memory"])


class CreativeMemoryUpdate(BaseModel):
    memory_type: str | None = None
    content: str | None = None
    category: str | None = None
    metadata_json: dict | None = None
    effectiveness_score: float | None = None


class PerformanceIngestRequest(BaseModel):
    client_id: str
    deliverable_id: str | None = None
    image_id: str | None = None
    platform: str
    metrics: dict


# --- CRUD ---

@router.get("", response_model=list[CreativeMemoryOut])
async def list_memories(
    client_id: str | None = None,
    type: str | None = Query(None, alias="type"),
    category: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    query = select(CreativeMemory).order_by(CreativeMemory.created_at.desc())
    if client_id:
        query = query.where(CreativeMemory.client_id == client_id)
    if type:
        query = query.where(CreativeMemory.memory_type == type)
    if category:
        query = query.where(CreativeMemory.category == category)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=CreativeMemoryOut, status_code=201)
async def create_memory(payload: CreativeMemoryCreate, db: AsyncSession = Depends(get_db)):
    memory = await store_memory(
        db,
        client_id=payload.client_id,
        memory_type=payload.memory_type,
        content=payload.content,
        category=payload.category,
        metadata=payload.metadata_json,
        effectiveness_score=payload.effectiveness_score,
    )
    return memory


@router.get("/client/{client_id}/insights")
async def get_client_insights(client_id: str, db: AsyncSession = Depends(get_db)):
    """Aggregate insights from creative memory for a specific client."""
    result = await db.execute(
        select(CreativeMemory).where(CreativeMemory.client_id == client_id)
    )
    memories = result.scalars().all()

    if not memories:
        return {"client_id": client_id, "total_memories": 0, "insights": {}}

    by_type: dict[str, list] = {}
    for m in memories:
        by_type.setdefault(m.memory_type, []).append(m)

    top_prompts = sorted(
        by_type.get("prompt", []),
        key=lambda m: m.effectiveness_score or 0,
        reverse=True,
    )[:10]

    performance_entries = by_type.get("performance", [])
    platform_perf: dict[str, list[float]] = {}
    for p in performance_entries:
        cat = p.category or "unknown"
        if p.effectiveness_score is not None:
            platform_perf.setdefault(cat, []).append(p.effectiveness_score)

    platform_averages = {
        platform: round(sum(scores) / len(scores), 1)
        for platform, scores in platform_perf.items()
    }

    style_insights = [m.content for m in by_type.get("style", [])]
    pattern_insights = [m.content for m in by_type.get("pattern", [])]

    return {
        "client_id": client_id,
        "total_memories": len(memories),
        "insights": {
            "top_prompts": [
                {"content": p.content[:200], "score": p.effectiveness_score, "category": p.category}
                for p in top_prompts
            ],
            "platform_performance": platform_averages,
            "style_insights": style_insights[:10],
            "cross_client_patterns": pattern_insights[:5],
            "memory_breakdown": {t: len(entries) for t, entries in by_type.items()},
        },
    }


@router.post("/ingest-performance", response_model=CreativeMemoryOut)
async def ingest_performance(
    payload: PerformanceIngestRequest,
    db: AsyncSession = Depends(get_db),
):
    """Ingest performance data, link to creative attributes, store as performance memory."""
    creative_desc_parts: list[str] = []
    metadata: dict = {
        "platform": payload.platform,
        "metrics": payload.metrics,
    }

    if payload.deliverable_id:
        deliverable = await db.get(Deliverable, payload.deliverable_id)
        if deliverable:
            creative_desc_parts.append(
                f"[{deliverable.content_type}] {deliverable.title}: {deliverable.content[:300]}"
            )
            metadata["deliverable_id"] = deliverable.id
            metadata["content_type"] = deliverable.content_type

    if payload.image_id:
        image = await db.get(GeneratedImage, payload.image_id)
        if image:
            creative_desc_parts.append(f"[image] prompt: {image.prompt[:200]}")
            metadata["image_id"] = image.id
            metadata["prompt"] = image.prompt

    if not creative_desc_parts:
        creative_desc_parts.append(f"Performance data for {payload.platform}")

    content = " | ".join(creative_desc_parts)
    effectiveness = _derive_effectiveness(payload.metrics)

    memory = await store_performance_data(
        db,
        client_id=payload.client_id,
        content=content,
        performance_metrics=metadata,
        category=payload.platform,
    )
    memory.effectiveness_score = effectiveness
    await db.flush()
    return memory


@router.get("/{memory_id}", response_model=CreativeMemoryOut)
async def get_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    memory = await db.get(CreativeMemory, memory_id)
    if not memory:
        raise HTTPException(404, "Creative memory not found")
    return memory


@router.patch("/{memory_id}", response_model=CreativeMemoryOut)
async def update_memory(memory_id: str, payload: CreativeMemoryUpdate, db: AsyncSession = Depends(get_db)):
    memory = await db.get(CreativeMemory, memory_id)
    if not memory:
        raise HTTPException(404, "Creative memory not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(memory, key, value)
    memory.updated_at = datetime.utcnow()
    await db.flush()
    return memory


@router.delete("/{memory_id}", status_code=204)
async def delete_memory(memory_id: str, db: AsyncSession = Depends(get_db)):
    memory = await db.get(CreativeMemory, memory_id)
    if not memory:
        raise HTTPException(404, "Creative memory not found")
    await db.delete(memory)
    await db.flush()


def _derive_effectiveness(metrics: dict) -> float:
    """Derive a 0-10 effectiveness score from raw performance metrics."""
    scores: list[float] = []
    er = metrics.get("engagement_rate")
    if er is not None:
        scores.append(min(er * 100, 10.0))
    ctr = metrics.get("ctr")
    if ctr is not None:
        scores.append(min(ctr * 50, 10.0))
    sentiment = metrics.get("sentiment")
    if sentiment is not None:
        scores.append(sentiment * 10 if sentiment <= 1 else min(sentiment, 10.0))
    if not scores:
        return 5.0
    return round(sum(scores) / len(scores), 1)
