from __future__ import annotations

import re
from pathlib import Path

from .models import VisionBlueprint


def _slice_between(text: str, start: str, end: str | None = None) -> str:
    start_idx = text.lower().find(start.lower())
    if start_idx < 0:
        return ""
    sub = text[start_idx:]
    if not end:
        return sub
    end_idx = sub.lower().find(end.lower())
    return sub[:end_idx] if end_idx >= 0 else sub


def _extract_bullets(block: str) -> list[str]:
    bullets = re.findall(r"(?:^|\n)\s*[•\-]\s+(.+)", block)
    return [b.strip() for b in bullets if b.strip()]


def _canonicalize_principles(candidates: list[str]) -> list[str]:
    lowered = [c.lower() for c in candidates]

    def has(*tokens: str) -> bool:
        return any(all(token in line for token in tokens) for line in lowered)

    ordered: list[str] = []
    if has("strategy", "creative"):
        ordered.append("Strategy before creative, always.")
    if has("ai first") or has("human where it matters"):
        ordered.append("AI first, human where it matters.")
    if has("brand bible"):
        ordered.append("The Brand Bible is law.")
    if has("speed") and has("quality"):
        ordered.append("Speed without sacrificing quality.")
    if has("compounds") or has("system compounds"):
        ordered.append("The system compounds with every engagement.")
    if has("value") and has("hours"):
        ordered.append("Charge for value, not hours.")

    if ordered:
        return ordered

    return [
        "Strategy before creative, always.",
        "AI first, human where it matters.",
        "The Brand Bible is law.",
        "Speed without sacrificing quality.",
        "The system compounds with every engagement.",
    ]


def build_vision_blueprint(doc_path: str | Path, raw_text: str) -> VisionBlueprint:
    principles_block = _slice_between(raw_text, "1.3 Core Principles", "PART TWO")
    core_principles = _canonicalize_principles(_extract_bullets(principles_block))

    strategy_outputs = [
        "Brand Positioning",
        "Campaign Strategy Deck",
        "Audience Personas",
        "Competitive Analysis",
        "Content Strategy",
        "Creative Brief",
    ]
    creative_outputs = [
        "Concept Presentation",
        "Mood Boards",
        "Creative Toolkit",
        "Key Visuals (spec-level only in Phase 1)",
    ]
    pipeline_stages = [
        "Brief Intake",
        "Research & Insights",
        "Strategy",
        "Creative Concepting",
        "Art Direction & Copy Direction",
        "Founder Quality Gate",
    ]
    quality_dimensions = [
        "Strategy-before-creative sequencing",
        "Voice and messaging consistency",
        "Territory-to-concept traceability",
        "Channel readiness",
        "Founder review efficiency",
    ]

    north_star_match = re.search(r"10\.3 The North Star(.+?)END OF BRIEF", raw_text, flags=re.S)
    north_star = (
        " ".join(north_star_match.group(1).split())[:600]
        if north_star_match
        else "One founder operating a fleet of AI agents to deliver world-class strategy and creative."
    )

    return VisionBlueprint(
        product_name="Agentic Force",
        north_star=north_star,
        core_principles=core_principles,
        phase_one_focus=[
            "Strategy development",
            "Creative concept development",
            "Founder quality gating",
        ],
        strategy_outputs=strategy_outputs,
        creative_outputs=creative_outputs,
        pipeline_stages=pipeline_stages,
        quality_dimensions=quality_dimensions,
        source_path=str(Path(doc_path)),
    )
