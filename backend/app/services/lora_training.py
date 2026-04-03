"""LoRA training service via fal.ai Flux LoRA fast training.

Handles:
- Training image preparation (zipping)
- Auto-captioning via OpenAI Vision (GPT-4o)
- Submitting training jobs to fal.ai
- Polling for completion
- Storing resulting weights URL on the LoRAModel record
"""
import asyncio
import base64
import io
import logging
import zipfile
from datetime import datetime
from pathlib import Path

import httpx
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.models import LoRAModel

logger = logging.getLogger(__name__)

FAL_QUEUE_BASE = "https://queue.fal.run"
FAL_TRAINING_MODEL = "fal-ai/flux-lora-fast-training"


async def auto_caption_image(image_path: str) -> str:
    """Generate a detailed style description for a training image using GPT-4o vision."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    path = Path(image_path)
    img_bytes = path.read_bytes()
    b64 = base64.b64encode(img_bytes).decode("utf-8")

    suffix = path.suffix.lower().lstrip(".")
    media_type = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png", "webp": "image/webp", "gif": "image/gif",
    }.get(suffix, "image/png")

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert visual analyst for brand asset training. "
                    "Describe this image in rich detail for use as a LoRA training caption. "
                    "Focus on: subject matter, art style, color palette, lighting, composition, "
                    "textures, mood, and any distinctive visual patterns or techniques. "
                    "Be specific and descriptive. Output only the caption, no preamble."
                ),
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{b64}"},
                    },
                    {"type": "text", "text": "Describe this image in detail for LoRA training."},
                ],
            },
        ],
        max_tokens=300,
        temperature=0.3,
    )
    return response.choices[0].message.content.strip()


async def auto_caption_images(image_paths: list[str]) -> list[str]:
    """Auto-caption multiple images concurrently."""
    tasks = [auto_caption_image(p) for p in image_paths]
    return await asyncio.gather(*tasks)


def _create_training_zip(
    image_paths: list[str],
    captions: list[str] | None = None,
) -> bytes:
    """Create a ZIP archive of training images with optional caption text files."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i, img_path in enumerate(image_paths):
            path = Path(img_path)
            if not path.exists():
                logger.warning(f"Training image not found, skipping: {img_path}")
                continue
            zf.write(path, path.name)
            if captions and i < len(captions):
                caption_name = path.stem + ".txt"
                zf.writestr(caption_name, captions[i])
    buf.seek(0)
    return buf.read()


async def submit_training_job(
    image_paths: list[str],
    trigger_word: str = "brandx_style",
    steps: int = 1500,
    captions: list[str] | None = None,
    create_masks: bool = True,
) -> dict:
    """Submit a LoRA training job to fal.ai and return the queue response."""
    settings = get_settings()

    zip_bytes = _create_training_zip(image_paths, captions)
    zip_b64 = base64.b64encode(zip_bytes).decode("utf-8")
    data_url = f"data:application/zip;base64,{zip_b64}"

    payload = {
        "images_data_url": data_url,
        "trigger_word": trigger_word,
        "steps": steps,
        "create_masks": create_masks,
    }

    headers = {
        "Authorization": f"Key {settings.fal_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=120) as http:
        resp = await http.post(
            f"{FAL_QUEUE_BASE}/{FAL_TRAINING_MODEL}",
            json=payload,
            headers=headers,
        )
        resp.raise_for_status()
        return resp.json()


async def poll_training_result(response_url: str, max_wait: int = 1800) -> dict:
    """Poll fal.ai for training job completion. Waits up to max_wait seconds."""
    settings = get_settings()
    headers = {"Authorization": f"Key {settings.fal_key}"}

    async with httpx.AsyncClient(timeout=60) as http:
        elapsed = 0
        interval = 10
        while elapsed < max_wait:
            await asyncio.sleep(interval)
            elapsed += interval
            resp = await http.get(response_url, headers=headers)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code != 202:
                resp.raise_for_status()

    raise TimeoutError(f"LoRA training timed out after {max_wait}s")


async def train_lora(
    db: AsyncSession,
    lora_id: str,
    image_paths: list[str],
    captions: list[str] | None = None,
    trigger_word: str = "brandx_style",
    steps: int = 1500,
) -> LoRAModel:
    """Full LoRA training workflow: submit, poll, and update the database record."""
    lora = await db.get(LoRAModel, lora_id)
    if not lora:
        raise ValueError(f"LoRA model {lora_id} not found")

    lora.status = "training"
    lora.training_images_count = len(image_paths)
    lora.training_steps = steps
    lora.trigger_word = trigger_word
    lora.training_config = {
        "steps": steps,
        "trigger_word": trigger_word,
        "create_masks": True,
        "image_count": len(image_paths),
    }
    await db.flush()

    try:
        if not captions:
            logger.info(f"Auto-captioning {len(image_paths)} training images...")
            captions = await auto_caption_images(image_paths)

        logger.info(f"Submitting LoRA training job: {len(image_paths)} images, {steps} steps")
        queue_resp = await submit_training_job(
            image_paths=image_paths,
            trigger_word=trigger_word,
            steps=steps,
            captions=captions,
        )

        response_url = queue_resp.get("response_url")
        if not response_url:
            result = queue_resp
        else:
            logger.info(f"Polling for training completion: {response_url}")
            result = await poll_training_result(response_url)

        weights_url = result.get("diffusers_lora_file", {}).get("url", "")
        if not weights_url:
            weights_url = result.get("config_file", {}).get("url", "")

        lora.weights_url = weights_url
        lora.status = "ready"
        lora.last_trained_at = datetime.utcnow()
        await db.flush()
        await db.refresh(lora)

        logger.info(f"LoRA training complete: {lora.name} -> {weights_url[:80]}...")
        return lora

    except Exception as e:
        lora.status = "failed"
        await db.flush()
        logger.error(f"LoRA training failed for {lora_id}: {e}")
        raise
