"""Automated multi-dimensional quality scoring against the Brand Bible.

Evaluates generated images and copy against brand standards before
they enter the founder's review queue. Only work that passes all
quality gates gets presented.
"""
import logging
import base64
from pathlib import Path
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"


async def score_image(
    image_path: str,
    prompt: str,
    brand_bible: dict,
    brief: dict | None = None,
    thresholds: dict | None = None,
) -> dict:
    """Score a generated image against brand guidelines using LLM vision.

    Returns a structured quality assessment with per-dimension scores,
    a composite score, and a pass/fail determination.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    filepath = Path(image_path)
    if not filepath.exists():
        filepath = IMAGES_DIR / image_path
    if not filepath.exists():
        return {"composite_score": 0, "passed": False, "error": "Image file not found"}

    image_data = base64.b64encode(filepath.read_bytes()).decode("utf-8")

    brand_context = _format_brand_context(brand_bible)
    brief_context = _format_brief_context(brief) if brief else "No specific brief provided."

    thresholds = thresholds or {
        "color_compliance": 7,
        "composition_quality": 7,
        "brand_consistency": 7,
        "technical_quality": 7,
        "strategic_alignment": 7,
        "composite_minimum": 7,
    }

    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": """You are a brand quality control system for a premium creative agency. You evaluate generated images against brand guidelines with exacting standards.

Score each dimension from 1-10. Be rigorous — a 7 is acceptable, 8 is good, 9 is excellent, 10 is exceptional. Most images should score 6-8.

Respond with ONLY a JSON object (no markdown):
{
  "color_compliance": {"score": <1-10>, "notes": "<specific observation>"},
  "composition_quality": {"score": <1-10>, "notes": "<specific observation>"},
  "brand_consistency": {"score": <1-10>, "notes": "<how well it matches brand visual style>"},
  "technical_quality": {"score": <1-10>, "notes": "<resolution, artifacts, hands, faces, text distortion>"},
  "strategic_alignment": {"score": <1-10>, "notes": "<does it communicate the intended message?>"},
  "platform_readiness": {"score": <1-10>, "notes": "<production readiness assessment>"},
  "overall_impression": "<one sentence creative assessment>",
  "issues": ["<list of specific issues if any>"],
  "strengths": ["<list of what works well>"]
}""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"Evaluate this generated image against the brand guidelines.\n\nBRAND GUIDELINES:\n{brand_context}\n\nBRIEF:\n{brief_context}\n\nPROMPT USED:\n{prompt}",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}", "detail": "high"},
                    },
                ],
            },
        ],
        temperature=0.2,
        max_tokens=1500,
    )

    import json
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        scores = json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse quality scores: {raw[:200]}")
        return {"composite_score": 0, "passed": False, "error": "Score parsing failed", "raw": raw}

    dimensions = ["color_compliance", "composition_quality", "brand_consistency",
                   "technical_quality", "strategic_alignment", "platform_readiness"]

    dimension_scores = {}
    total = 0
    count = 0
    for dim in dimensions:
        if dim in scores and isinstance(scores[dim], dict):
            s = scores[dim].get("score", 0)
            dimension_scores[dim] = {"score": s, "notes": scores[dim].get("notes", "")}
            total += s
            count += 1

    composite = round(total / max(count, 1), 1)

    passed = composite >= thresholds.get("composite_minimum", 7)
    for dim in dimensions:
        dim_threshold = thresholds.get(dim, 7)
        if dimension_scores.get(dim, {}).get("score", 0) < dim_threshold:
            passed = False
            break

    return {
        "composite_score": composite,
        "passed": passed,
        "dimensions": dimension_scores,
        "overall_impression": scores.get("overall_impression", ""),
        "issues": scores.get("issues", []),
        "strengths": scores.get("strengths", []),
        "thresholds_used": thresholds,
    }


async def score_copy(
    copy_text: str,
    brand_bible: dict,
    brief: dict | None = None,
) -> dict:
    """Score generated copy against brand voice and guidelines."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    brand_context = _format_brand_context(brand_bible)
    brief_context = _format_brief_context(brief) if brief else ""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": """You are a brand voice quality control system. Evaluate copy against brand guidelines.

Score each dimension from 1-10. Respond with ONLY a JSON object:
{
  "voice_alignment": {"score": <1-10>, "notes": "<does it sound like the brand?>"},
  "message_clarity": {"score": <1-10>, "notes": "<is the key message clear?>"},
  "audience_fit": {"score": <1-10>, "notes": "<does it speak to the target audience?>"},
  "craft_quality": {"score": <1-10>, "notes": "<writing quality, rhythm, word choice>"},
  "strategic_alignment": {"score": <1-10>, "notes": "<does it ladder to the objective?>"},
  "overall_impression": "<one sentence assessment>",
  "suggested_improvements": ["<specific improvement if needed>"]
}""",
            },
            {
                "role": "user",
                "content": f"Evaluate this copy:\n\n{copy_text}\n\nBRAND GUIDELINES:\n{brand_context}\n\nBRIEF:\n{brief_context}",
            },
        ],
        temperature=0.2,
        max_tokens=1000,
    )

    import json
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        scores = json.loads(raw)
    except json.JSONDecodeError:
        return {"composite_score": 0, "error": "Parse failed"}

    dims = ["voice_alignment", "message_clarity", "audience_fit", "craft_quality", "strategic_alignment"]
    total = sum(scores.get(d, {}).get("score", 0) for d in dims if isinstance(scores.get(d), dict))
    count = sum(1 for d in dims if isinstance(scores.get(d), dict))
    composite = round(total / max(count, 1), 1)

    return {
        "composite_score": composite,
        "passed": composite >= 7,
        "dimensions": {d: scores[d] for d in dims if d in scores},
        "overall_impression": scores.get("overall_impression", ""),
        "suggested_improvements": scores.get("suggested_improvements", []),
    }


def _format_brand_context(bible: dict) -> str:
    parts = []
    field_labels = {
        "brand_essence": "Brand Essence",
        "positioning_statement": "Positioning",
        "unique_selling_proposition": "USP",
        "primary_audience": "Primary Audience",
        "tone_of_voice": "Tone of Voice",
        "photography_style": "Photography Style",
        "composition_rules": "Composition Rules",
        "visual_dos": "Visual Do's",
        "visual_donts": "Visual Don'ts",
        "headline_style": "Headline Style",
        "copy_style": "Copy Style",
        "vocabulary_preferences": "Preferred Vocabulary",
        "vocabulary_avoid": "Vocabulary to Avoid",
    }
    for field, label in field_labels.items():
        val = bible.get(field)
        if val:
            parts.append(f"{label}: {val}")

    palette = bible.get("color_palette")
    if palette and isinstance(palette, dict):
        parts.append(f"Color Palette: Primary {palette.get('primary', [])}, Secondary {palette.get('secondary', [])}, Accent {palette.get('accent', [])}")

    typography = bible.get("typography")
    if typography and isinstance(typography, dict):
        parts.append(f"Typography: {typography}")

    return "\n".join(parts) if parts else "No brand guidelines available."


def _format_brief_context(brief: dict) -> str:
    parts = []
    for key in ["objective", "target_audience", "key_messages", "tone", "desired_emotional_response"]:
        if brief.get(key):
            parts.append(f"{key.replace('_', ' ').title()}: {brief[key]}")
    return "\n".join(parts) if parts else ""
