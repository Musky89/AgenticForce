"""Cross-Client Pattern Recognition — finds what works across ALL clients.

Analyzes creative memory entries with performance data to identify
reusable patterns by industry, platform, visual style, and copy structure.
Stores findings as "pattern" type memories for agent consumption.
"""
import logging
from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import CreativeMemory, Client

logger = logging.getLogger(__name__)


async def analyze_cross_client_patterns(db: AsyncSession) -> list[dict]:
    """Analyze performance-linked memories across ALL clients to find universal patterns.

    Groups by category/platform, computes averages, identifies top performers,
    and stores discovered patterns back as "pattern" type memories.
    """
    result = await db.execute(
        select(CreativeMemory).where(
            CreativeMemory.memory_type.in_(["performance", "prompt", "style"]),
            CreativeMemory.effectiveness_score.isnot(None),
        )
    )
    memories = result.scalars().all()

    if not memories:
        return []

    client_result = await db.execute(select(Client))
    clients = {c.id: c for c in client_result.scalars().all()}

    by_platform: dict[str, list] = defaultdict(list)
    by_industry: dict[str, list] = defaultdict(list)
    by_type: dict[str, list] = defaultdict(list)

    for m in memories:
        if m.category:
            by_platform[m.category].append(m)
        client = clients.get(m.client_id)
        if client and client.industry:
            by_industry[client.industry].append(m)
        by_type[m.memory_type].append(m)

    patterns: list[dict] = []

    for platform, entries in by_platform.items():
        if len(entries) < 2:
            continue
        sorted_entries = sorted(entries, key=lambda m: m.effectiveness_score or 0, reverse=True)
        top = sorted_entries[:5]
        avg_score = sum(m.effectiveness_score for m in entries) / len(entries)
        pattern = {
            "scope": "platform",
            "key": platform,
            "sample_size": len(entries),
            "avg_effectiveness": round(avg_score, 1),
            "top_performing": [
                {"content": m.content[:200], "score": m.effectiveness_score, "client_id": m.client_id}
                for m in top
            ],
        }
        patterns.append(pattern)

    for industry, entries in by_industry.items():
        if len(entries) < 2:
            continue
        sorted_entries = sorted(entries, key=lambda m: m.effectiveness_score or 0, reverse=True)
        top = sorted_entries[:5]
        avg_score = sum(m.effectiveness_score for m in entries) / len(entries)
        pattern = {
            "scope": "industry",
            "key": industry,
            "sample_size": len(entries),
            "avg_effectiveness": round(avg_score, 1),
            "top_performing": [
                {"content": m.content[:200], "score": m.effectiveness_score, "client_id": m.client_id}
                for m in top
            ],
        }
        patterns.append(pattern)

    for pattern in patterns:
        top_items = pattern["top_performing"]
        if not top_items:
            continue
        summary = (
            f"[{pattern['scope']}:{pattern['key']}] "
            f"Avg effectiveness {pattern['avg_effectiveness']}/10 across {pattern['sample_size']} entries. "
            f"Top pattern: {top_items[0]['content'][:150]}"
        )
        existing = await db.execute(
            select(CreativeMemory).where(
                CreativeMemory.memory_type == "pattern",
                CreativeMemory.category == f"{pattern['scope']}:{pattern['key']}",
            ).limit(1)
        )
        existing_mem = existing.scalar_one_or_none()

        if existing_mem:
            existing_mem.content = summary
            existing_mem.metadata_json = pattern
            existing_mem.effectiveness_score = pattern["avg_effectiveness"]
        else:
            client_id = top_items[0]["client_id"]
            mem = CreativeMemory(
                client_id=client_id,
                memory_type="pattern",
                category=f"{pattern['scope']}:{pattern['key']}",
                content=summary,
                metadata_json=pattern,
                effectiveness_score=pattern["avg_effectiveness"],
            )
            db.add(mem)

    await db.flush()
    return patterns


async def get_industry_insights(db: AsyncSession, industry: str) -> dict:
    """Get cross-client patterns for a specific industry."""
    client_result = await db.execute(
        select(Client).where(Client.industry == industry)
    )
    industry_clients = client_result.scalars().all()
    client_ids = [c.id for c in industry_clients]

    if not client_ids:
        return {"industry": industry, "clients": 0, "insights": []}

    result = await db.execute(
        select(CreativeMemory).where(
            CreativeMemory.client_id.in_(client_ids),
            CreativeMemory.effectiveness_score.isnot(None),
        ).order_by(CreativeMemory.effectiveness_score.desc())
    )
    memories = result.scalars().all()

    by_platform: dict[str, list[float]] = defaultdict(list)
    top_prompts: list[dict] = []
    top_styles: list[str] = []

    for m in memories:
        if m.category and m.effectiveness_score is not None:
            by_platform[m.category].append(m.effectiveness_score)
        if m.memory_type == "prompt" and m.effectiveness_score and m.effectiveness_score >= 7:
            top_prompts.append({"content": m.content[:200], "score": m.effectiveness_score})
        if m.memory_type == "style":
            top_styles.append(m.content)

    platform_averages = {
        p: round(sum(s) / len(s), 1) for p, s in by_platform.items()
    }

    return {
        "industry": industry,
        "clients": len(industry_clients),
        "total_memories": len(memories),
        "platform_performance": platform_averages,
        "top_prompts": top_prompts[:10],
        "style_insights": top_styles[:10],
    }


async def get_platform_insights(db: AsyncSession, platform: str) -> dict:
    """Get cross-client patterns for a specific platform (e.g. instagram, linkedin)."""
    result = await db.execute(
        select(CreativeMemory).where(
            CreativeMemory.category == platform,
            CreativeMemory.effectiveness_score.isnot(None),
        ).order_by(CreativeMemory.effectiveness_score.desc())
    )
    memories = result.scalars().all()

    if not memories:
        return {"platform": platform, "total_entries": 0, "insights": []}

    client_result = await db.execute(select(Client))
    clients = {c.id: c for c in client_result.scalars().all()}

    by_industry: dict[str, list[float]] = defaultdict(list)
    top_performers: list[dict] = []

    for m in memories:
        client = clients.get(m.client_id)
        industry = client.industry if client else "unknown"
        if m.effectiveness_score is not None:
            by_industry[industry].append(m.effectiveness_score)
        if m.effectiveness_score and m.effectiveness_score >= 7:
            top_performers.append({
                "content": m.content[:200],
                "score": m.effectiveness_score,
                "industry": industry,
                "type": m.memory_type,
            })

    industry_averages = {
        ind: round(sum(s) / len(s), 1) for ind, s in by_industry.items()
    }

    avg_all = sum(m.effectiveness_score for m in memories) / len(memories)

    return {
        "platform": platform,
        "total_entries": len(memories),
        "avg_effectiveness": round(avg_all, 1),
        "by_industry": industry_averages,
        "top_performers": top_performers[:10],
    }
