import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import GeneratedImage, AgentRun, AgentRole, RunStatus
from app.schemas.schemas import (
    ImageGenerateRequest,
    ImageFromArtDirectionRequest,
    GeneratedImageOut,
)
from app.services.image_gen import generate_image, generate_images_from_art_direction

logger = logging.getLogger(__name__)

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"

router = APIRouter(prefix="/images", tags=["images"])


@router.post("/generate", response_model=list[GeneratedImageOut], status_code=201)
async def generate(payload: ImageGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate an image from a freeform prompt using DALL-E 3."""
    results = await generate_image(
        prompt=payload.prompt,
        size=payload.size,
        quality=payload.quality,
        style=payload.style,
    )

    images = []
    for r in results:
        img = GeneratedImage(
            project_id=payload.project_id,
            filename=r["filename"],
            prompt=r["prompt"],
            revised_prompt=r.get("revised_prompt"),
            label="Custom Generation",
            size=r["size"],
            quality=r["quality"],
            style=r["style"],
        )
        db.add(img)
        await db.flush()
        await db.refresh(img)
        images.append(img)

    return images


@router.post(
    "/from-art-direction",
    response_model=list[GeneratedImageOut],
    status_code=201,
)
async def generate_from_art_direction(
    payload: ImageFromArtDirectionRequest,
    db: AsyncSession = Depends(get_db),
):
    """Extract visual concepts from the Art Director's output and generate images."""
    result = await db.execute(
        select(AgentRun)
        .where(
            AgentRun.project_id == payload.project_id,
            AgentRun.agent_role == AgentRole.ART_DIRECTOR,
            AgentRun.status == RunStatus.COMPLETED,
        )
        .order_by(AgentRun.created_at.desc())
    )
    art_run = result.scalars().first()
    if not art_run or not art_run.output_data:
        raise HTTPException(
            404,
            "No completed Art Director run found for this project. Run the Art Director agent first.",
        )

    art_text = art_run.output_data.get("content", "")
    if not art_text:
        raise HTTPException(400, "Art Director output is empty.")

    gen_results = await generate_images_from_art_direction(art_text)

    images = []
    for r in gen_results:
        if "error" in r:
            logger.warning(f"Skipping failed image: {r.get('label')}: {r['error']}")
            continue
        img = GeneratedImage(
            project_id=payload.project_id,
            agent_run_id=art_run.id,
            filename=r["filename"],
            prompt=r["prompt"],
            revised_prompt=r.get("revised_prompt"),
            label=r.get("label", "Art Direction Image"),
            size=r["size"],
            quality=r["quality"],
            style=r["style"],
        )
        db.add(img)
        await db.flush()
        await db.refresh(img)
        images.append(img)

    if not images:
        raise HTTPException(500, "All image generations failed.")

    return images


@router.get("", response_model=list[GeneratedImageOut])
async def list_images(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(GeneratedImage).order_by(GeneratedImage.created_at.desc())
    if project_id:
        query = query.where(GeneratedImage.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{image_id}", response_model=GeneratedImageOut)
async def get_image(image_id: str, db: AsyncSession = Depends(get_db)):
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    return img


@router.get("/{image_id}/file")
async def serve_image_file(image_id: str, db: AsyncSession = Depends(get_db)):
    """Serve the actual image file."""
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")

    filepath = IMAGES_DIR / img.filename
    if not filepath.exists():
        raise HTTPException(404, "Image file not found on disk")

    return FileResponse(filepath, media_type="image/png", filename=img.filename)


@router.delete("/{image_id}", status_code=204)
async def delete_image(image_id: str, db: AsyncSession = Depends(get_db)):
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")

    filepath = IMAGES_DIR / img.filename
    if filepath.exists():
        filepath.unlink()

    await db.delete(img)
    await db.flush()
