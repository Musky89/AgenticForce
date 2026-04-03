"""Multi-provider image generation service.

Providers:
- Flux via fal.ai: LoRA support, photorealistic, brand-specific generation
- Gemini Imagen 4: Highest raw quality, text rendering, no LoRA

Auto-selection: Uses Flux when a client LoRA is available, Imagen otherwise.
Can be overridden per-request.
"""
import asyncio
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

ASPECT_RATIO_MAP = {
    "1:1": (1024, 1024),
    "4:3": (1344, 1024),
    "3:4": (1024, 1344),
    "16:9": (1792, 1024),
    "9:16": (1024, 1792),
}


def select_provider(lora_url: str | None = None, preferred: str | None = None) -> str:
    """Auto-select the best provider based on context."""
    settings = get_settings()

    if preferred and preferred in ("flux", "imagen"):
        if preferred == "imagen" and not settings.gemini_api_key:
            return "flux"
        if preferred == "flux" and not settings.fal_key:
            return "imagen"
        return preferred

    # If LoRA is specified, must use Flux
    if lora_url:
        return "flux"

    # Use configured default, falling back based on available keys
    default = settings.default_image_provider
    if default == "imagen" and settings.gemini_api_key:
        return "imagen"
    if default == "flux" and settings.fal_key:
        return "flux"

    # Fallback: use whichever has a key
    if settings.gemini_api_key:
        return "imagen"
    if settings.fal_key:
        return "flux"

    raise ValueError("No image generation provider configured. Set FAL_KEY or GEMINI_API_KEY.")


# --- Flux via fal.ai ---

async def _fal_request(model: str, payload: dict) -> dict:
    settings = get_settings()
    headers = {"Authorization": f"Key {settings.fal_key}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=300) as http:
        submit = await http.post(f"{FAL_API_BASE}/{model}", json=payload, headers=headers)
        submit.raise_for_status()
        result_url = submit.json().get("response_url")
        if not result_url:
            return submit.json()

        for _ in range(120):
            await asyncio.sleep(2)
            resp = await http.get(result_url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code != 202:
                resp.raise_for_status()

        raise TimeoutError("fal.ai request timed out after 240s")


async def _generate_flux(
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
        model = settings.flux_model_lora
        payload["loras"] = [{"path": lora_url, "scale": lora_scale}]
    else:
        model = settings.flux_model

    result = await _fal_request(model, payload)
    images_data = result.get("images", [])

    return await _download_images(images_data, prompt, width, height, "flux", lora_url=lora_url)


# --- Gemini Imagen ---

async def _generate_imagen(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_images: int = 1,
    aspect_ratio: str | None = None,
) -> list[dict]:
    settings = get_settings()

    if not aspect_ratio:
        ratio = f"{width}:{height}"
        closest = min(ASPECT_RATIO_MAP.keys(), key=lambda r: abs(ASPECT_RATIO_MAP[r][0] - width) + abs(ASPECT_RATIO_MAP[r][1] - height))
        aspect_ratio = closest

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.gemini_api_key)

    response = client.models.generate_images(
        model=settings.imagen_model,
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=min(num_images, 4),
            aspect_ratio=aspect_ratio,
            person_generation="allow_adult",
        ),
    )

    results = []
    for img_data in response.generated_images:
        file_id = str(uuid.uuid4())
        filename = f"{file_id}.png"
        filepath = IMAGES_DIR / filename
        filepath.write_bytes(img_data.image.image_bytes)

        results.append({
            "filename": filename,
            "filepath": str(filepath),
            "prompt": prompt,
            "width": width,
            "height": height,
            "provider": "imagen",
            "aspect_ratio": aspect_ratio,
            "created_at": datetime.utcnow().isoformat(),
        })

    logger.info(f"Generated {len(results)} image(s) via Imagen for: {prompt[:80]}...")
    return results


# --- Unified interface ---

async def generate_image(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    num_images: int = 1,
    lora_url: str | None = None,
    lora_scale: float = 0.85,
    provider: str | None = None,
    aspect_ratio: str | None = None,
    seed: int | None = None,
) -> list[dict]:
    """Generate images using the best available provider.

    Auto-selects Flux when LoRA is specified, Imagen for raw quality.
    Can be overridden with the `provider` parameter.
    """
    selected = select_provider(lora_url=lora_url, preferred=provider)
    logger.info(f"Image generation via {selected} | prompt: {prompt[:60]}...")

    if selected == "imagen":
        return await _generate_imagen(prompt, width, height, num_images, aspect_ratio)
    else:
        return await _generate_flux(prompt, width, height, lora_url, lora_scale, num_images, seed=seed)


async def generate_images_from_art_direction(
    art_direction_text: str,
    lora_url: str | None = None,
    provider: str | None = None,
) -> list[dict]:
    """Extract visual concepts from art direction and generate images."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    selected = select_provider(lora_url=lora_url, preferred=provider)

    extraction_response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert at converting art direction briefs into image generation prompts. "
                    f"The images will be generated using {'Flux' if selected == 'flux' else 'Google Imagen 4'}.\n\n"
                    "Extract 3-5 distinct visual concepts from the art direction and write a detailed prompt for each.\n\n"
                    "For each prompt, specify:\n"
                    "- prompt: detailed image generation prompt\n"
                    "- aspect_ratio: '1:1', '4:3', '3:4', '16:9', or '9:16'\n"
                    "- label: short descriptive label (e.g. 'Hero Banner', 'Social Post')\n"
                    "- num_variants: 1-3\n\n"
                    "Write extremely detailed prompts: subject, composition, lighting, color palette, "
                    "mood, art style, textures, atmosphere. Never include text/typography.\n\n"
                    "Respond with ONLY a JSON array."
                ),
            },
            {"role": "user", "content": f"Extract prompts from this art direction:\n\n{art_direction_text}"},
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
        prompt_specs = [{"prompt": art_direction_text[:1000], "aspect_ratio": "1:1", "label": "Key Visual", "num_variants": 1}]

    all_results = []
    for spec in prompt_specs:
        try:
            ar = spec.get("aspect_ratio", "1:1")
            dims = ASPECT_RATIO_MAP.get(ar, (1024, 1024))

            images = await generate_image(
                prompt=spec["prompt"],
                width=dims[0],
                height=dims[1],
                num_images=min(spec.get("num_variants", 1), 3),
                lora_url=lora_url,
                provider=provider,
                aspect_ratio=ar,
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


async def _download_images(
    images_data: list[dict],
    prompt: str,
    width: int,
    height: int,
    provider: str,
    lora_url: str | None = None,
) -> list[dict]:
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
                "provider": provider,
                "lora_url": lora_url,
                "created_at": datetime.utcnow().isoformat(),
            })

    logger.info(f"Generated {len(results)} image(s) via {provider} for: {prompt[:80]}...")
    return results
