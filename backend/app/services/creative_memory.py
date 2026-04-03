"""Creative Memory — compounds over time to make output better with every engagement.

Tracks: effective prompts, style patterns that work, performance data,
cross-client patterns. Feeds insights back into agent context.
"""
import logging
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CreativeMemory, GeneratedImage, Deliverable

logger = logging.getLogger(__name__)


async def store_memory(
    db: AsyncSession,
    client_id: str,
    memory_type: str,
    content: str,
    category: str | None = None,
    metadata: dict | None = None,
    effectiveness_score: float | None = None,
) -> CreativeMemory:
    """Store a creative memory entry."""
    memory = CreativeMemory(
        client_id=client_id,
        memory_type=memory_type,
        category=category,
        content=content,
        metadata_json=metadata,
        effectiveness_score=effectiveness_score,
    )
    db.add(memory)
    await db.flush()
    return memory


async def store_effective_prompt(
    db: AsyncSession,
    client_id: str,
    prompt: str,
    category: str,
    quality_score: float | None = None,
    metadata: dict | None = None,
) -> CreativeMemory:
    """Store a prompt that produced high-quality output."""
    return await store_memory(
        db, client_id, "prompt", prompt,
        category=category,
        metadata=metadata,
        effectiveness_score=quality_score,
    )


async def get_effective_prompts(
    db: AsyncSession,
    client_id: str,
    category: str | None = None,
    limit: int = 10,
) -> list[CreativeMemory]:
    """Retrieve the most effective prompts for a client."""
    query = (
        select(CreativeMemory)
        .where(CreativeMemory.client_id == client_id, CreativeMemory.memory_type == "prompt")
        .order_by(desc(CreativeMemory.effectiveness_score))
        .limit(limit)
    )
    if category:
        query = query.where(CreativeMemory.category == category)
    result = await db.execute(query)
    return list(result.scalars().all())


async def store_style_insight(
    db: AsyncSession,
    client_id: str,
    insight: str,
    category: str,
    metadata: dict | None = None,
) -> CreativeMemory:
    """Store a learned style insight (what works for this client)."""
    return await store_memory(db, client_id, "style", insight, category=category, metadata=metadata)


async def store_performance_data(
    db: AsyncSession,
    client_id: str,
    content: str,
    performance_metrics: dict,
    category: str | None = None,
) -> CreativeMemory:
    """Store performance data linked to creative attributes."""
    return await store_memory(
        db, client_id, "performance", content,
        category=category,
        metadata=performance_metrics,
    )


async def get_client_memory_context(
    db: AsyncSession,
    client_id: str,
    limit: int = 20,
) -> str:
    """Build a context string from creative memory for agent injection."""
    memories = await db.execute(
        select(CreativeMemory)
        .where(CreativeMemory.client_id == client_id)
        .order_by(desc(CreativeMemory.effectiveness_score))
        .limit(limit)
    )

    entries = memories.scalars().all()
    if not entries:
        return ""

    parts = ["=== Creative Memory (What Works for This Client) ==="]

    prompts = [m for m in entries if m.memory_type == "prompt"]
    if prompts:
        parts.append("\n--- Effective Prompts ---")
        for p in prompts[:5]:
            parts.append(f"- [{p.category or 'general'}] {p.content[:200]}...")

    styles = [m for m in entries if m.memory_type == "style"]
    if styles:
        parts.append("\n--- Style Insights ---")
        for s in styles[:5]:
            parts.append(f"- {s.content}")

    perfs = [m for m in entries if m.memory_type == "performance"]
    if perfs:
        parts.append("\n--- Performance Patterns ---")
        for p in perfs[:5]:
            parts.append(f"- {p.content}")

    patterns = [m for m in entries if m.memory_type == "pattern"]
    if patterns:
        parts.append("\n--- Cross-Client Patterns ---")
        for p in patterns[:3]:
            parts.append(f"- {p.content}")

    return "\n".join(parts)


async def auto_capture_from_approval(
    db: AsyncSession,
    client_id: str,
    image: GeneratedImage | None = None,
    deliverable: Deliverable | None = None,
):
    """Auto-capture learnings when the founder approves work."""
    if image and image.prompt:
        score = image.quality_score or 8.0
        await store_effective_prompt(
            db, client_id, image.prompt,
            category="visual",
            quality_score=score,
            metadata={"label": image.label, "size": image.size},
        )

    if deliverable and deliverable.content:
        await store_memory(
            db, client_id, "style",
            f"Approved {deliverable.content_type}: {deliverable.content[:300]}",
            category=deliverable.content_type,
            effectiveness_score=8.0,
        )
