import logging
import uuid
import json
import httpx
from pathlib import Path
from datetime import datetime
from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"
IMAGES_DIR.mkdir(exist_ok=True)

FAL_API_BASE = "https://queue.fal.run"


async def _fal_request(model: str, payload: dict) -> dict:
    """Submit a request to fal.ai and poll for result."""
    settings = get_settings()
    headers = {"Authorization": f"Key {settings.fal_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=300) as http:
        submit = await http.post(f"{FAL_API_BASE}/{model}", json=payload, headers=headers)
        submit.raise_for_status()
        result_url = submit.json().get("response_url")
        if not result_url:
            return submit.json()

        # Poll for completion
        for _ in range(120):
            import asyncio
            await asyncio.sleep(2)
            resp = await http.get(result_url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code != 202:
                resp.raise_for_status()

        raise TimeoutError("fal.ai request timed out after 240s")


async def generate_image_flux(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    lora_url: str | None = None,
    lora_scale: float = 0.85,
    num_images: int = 1,
    guidance_scale: float = 3.5,
    num_inference_steps: int = 28,
    seed: int | None = None,
) -> list[dict]:
    """Generate images using Flux via fal.ai, optionally with a client LoRA."""
    settings = get_settings()

    payload: dict = {
        "prompt": prompt,
        "image_size": {"width": width, "height": height},
        "num_images": num_images,
        "guidance_scale": guidance_scale,
        "num_inference_steps": num_inference_steps,
        "enable_safety_checker": False,
    }
    if seed is not None:
        payload["seed"] = seed

    if lora_url:
        model = settings.image_model_lora
        payload["loras"] = [{"path": lora_url, "scale": lora_scale}]
    else:
        model = settings.image_model

    result = await _fal_request(model, payload)
    images_data = result.get("images", [])

    results = []
    async with httpx.AsyncClient(timeout=60) as http:
        for img_info in images_data:
            url = img_info.get("url", "")
            if not url:
                continue
            file_id = str(uuid.uuid4())
            filename = f"{file_id}.png"
            filepath = IMAGES_DIR / filename

            img_response = await http.get(url)
            img_response.raise_for_status()
            filepath.write_bytes(img_response.content)

            results.append({
                "filename": filename,
                "filepath": str(filepath),
                "prompt": prompt,
                "width": width,
                "height": height,
                "lora_url": lora_url,
                "seed": result.get("seed"),
                "created_at": datetime.utcnow().isoformat(),
            })

    logger.info(f"Generated {len(results)} image(s) via Flux for: {prompt[:80]}...")
    return results


async def generate_images_from_art_direction(
    art_direction_text: str,
    lora_url: str | None = None,
) -> list[dict]:
    """Extract visual concepts from art direction and generate images via Flux."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    extraction_response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at converting art direction briefs into Flux image generation prompts. "
                    "Extract 3-5 distinct visual concepts from the art direction and write a detailed, "
                    "specific prompt for each. Each prompt should be self-contained and produce a "
                    "professional, polished image.\n\n"
                    "For each prompt, also specify:\n"
                    "- width: image width (1024, 1792, or 1344)\n"
                    "- height: image height (1024, 1024, or 768)\n"
                    "- label: a short descriptive label (e.g. 'Hero Banner', 'Social Post', 'Brand Pattern')\n"
                    "- num_variants: how many variants to generate (1-3)\n\n"
                    "Write prompts that are extremely detailed about subject, composition, lighting, color palette, "
                    "mood, art style, textures, and atmosphere. Never include text/typography in the prompt.\n\n"
                    "Respond with ONLY a JSON array. No markdown, no explanation."
                ),
            },
            {"role": "user", "content": f"Extract image generation prompts from this art direction:\n\n{art_direction_text}"},
        ],
        temperature=0.4,
        max_tokens=3000,
    )

    raw = extraction_response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    try:
        prompt_specs = json.loads(raw)
    except json.JSONDecodeError:
        logger.error(f"Failed to parse prompt extraction: {raw[:200]}")
        prompt_specs = [{"prompt": art_direction_text[:1000], "width": 1024, "height": 1024, "label": "Key Visual", "num_variants": 1}]

    all_results = []
    for spec in prompt_specs:
        try:
            images = await generate_image_flux(
                prompt=spec["prompt"],
                width=spec.get("width", 1024),
                height=spec.get("height", 1024),
                lora_url=lora_url,
                num_images=min(spec.get("num_variants", 1), 3),
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
