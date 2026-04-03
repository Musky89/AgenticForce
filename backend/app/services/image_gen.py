import logging
import uuid
import httpx
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)


async def generate_image(
    prompt: str,
    size: str = "1024x1024",
    quality: str = "standard",
    style: str = "vivid",
    n: int = 1,
) -> list[dict]:
    """Generate images using DALL-E 3 and save them to disk.

    Returns a list of dicts with: filename, filepath, prompt, revised_prompt, size, quality, style
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    response = await client.images.generate(
        model="dall-e-3",
        prompt=prompt,
        size=size,
        quality=quality,
        style=style,
        n=n,
    )

    results = []
    async with httpx.AsyncClient() as http:
        for img_data in response.data:
            file_id = str(uuid.uuid4())
            filename = f"{file_id}.png"
            filepath = IMAGES_DIR / filename

            img_response = await http.get(img_data.url)
            img_response.raise_for_status()
            filepath.write_bytes(img_response.content)

            results.append({
                "filename": filename,
                "filepath": str(filepath),
                "prompt": prompt,
                "revised_prompt": img_data.revised_prompt,
                "size": size,
                "quality": quality,
                "style": style,
                "created_at": datetime.utcnow().isoformat(),
            })

    logger.info(f"Generated {len(results)} image(s) for prompt: {prompt[:80]}...")
    return results


async def generate_images_from_art_direction(art_direction_text: str) -> list[dict]:
    """Extract image prompts from art direction output and generate images.

    Uses GPT to parse the art direction text into optimal DALL-E prompts,
    then generates images for each.
    """
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    extraction_response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at converting art direction briefs into DALL-E 3 image generation prompts. "
                    "Extract 2-4 distinct visual concepts from the art direction and write a detailed, "
                    "specific DALL-E prompt for each. Each prompt should be self-contained and produce a "
                    "professional, polished image.\n\n"
                    "For each prompt, also specify:\n"
                    "- size: one of '1024x1024', '1792x1024' (landscape), '1024x1792' (portrait)\n"
                    "- style: 'vivid' or 'natural'\n"
                    "- label: a short descriptive label for the image (e.g. 'Hero Banner', 'Social Post', 'Brand Pattern')\n\n"
                    "Respond with ONLY a JSON array of objects, each with keys: prompt, size, style, label\n"
                    "No markdown, no explanation, just the JSON array."
                ),
            },
            {
                "role": "user",
                "content": f"Extract image generation prompts from this art direction:\n\n{art_direction_text}",
            },
        ],
        temperature=0.4,
        max_tokens=2048,
    )

    import json
    raw = extraction_response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        prompt_specs = json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse prompt extraction: {raw[:200]}")
        prompt_specs = [{"prompt": art_direction_text[:1000], "size": "1024x1024", "style": "vivid", "label": "Key Visual"}]

    all_results = []
    for spec in prompt_specs:
        try:
            images = await generate_image(
                prompt=spec["prompt"],
                size=spec.get("size", "1024x1024"),
                style=spec.get("style", "vivid"),
            )
            for img in images:
                img["label"] = spec.get("label", "Generated Image")
            all_results.extend(images)
        except Exception as e:
            logger.error(f"Image generation failed for '{spec.get('label', 'unknown')}': {e}")
            all_results.append({
                "error": str(e),
                "label": spec.get("label", "Failed Image"),
                "prompt": spec["prompt"],
            })

    return all_results
