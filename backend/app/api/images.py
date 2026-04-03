import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import GeneratedImage, AgentRun, AgentRole, RunStatus, LoRAModel, BrandBible, Brief
from app.schemas.schemas import ImageGenerateRequest, ImageFromArtDirectionRequest, GeneratedImageOut
from app.services.image_gen import generate_image, generate_images_from_art_direction, select_provider
from app.services.quality_scoring import score_image

logger = logging.getLogger(__name__)
IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"

router = APIRouter(prefix="/images", tags=["images"])


@router.get("/providers")
async def list_providers():
    """List available image generation providers and which is currently active."""
    from app.config import get_settings
    settings = get_settings()
    providers = []
    if settings.fal_key:
        providers.append({"id": "flux", "name": "Flux (fal.ai)", "supports_lora": True, "status": "available"})
    if settings.gemini_api_key:
        providers.append({"id": "imagen", "name": "Gemini Imagen 4", "supports_lora": False, "status": "available"})
    return {"providers": providers, "default": settings.default_image_provider}


@router.post("/generate", response_model=list[GeneratedImageOut], status_code=201)
async def generate(payload: ImageGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate images. Auto-selects Flux (LoRA) or Imagen (raw quality) based on context."""
    lora_url = None
    lora_id = None

    if payload.use_client_lora and payload.project_id:
        from app.models.models import Project
        project = await db.get(Project, payload.project_id)
        if project:
            lora_result = await db.execute(
                select(LoRAModel)
                .where(LoRAModel.client_id == project.client_id, LoRAModel.status == "ready")
                .order_by(LoRAModel.version.desc())
            )
            lora = lora_result.scalars().first()
            if lora:
                lora_url = lora.weights_url
                lora_id = lora.id

    selected = select_provider(lora_url=lora_url, preferred=payload.provider)

    results = await generate_image(
        prompt=payload.prompt,
        width=payload.width,
        height=payload.height,
        num_images=payload.num_images,
        lora_url=lora_url,
        provider=payload.provider,
        aspect_ratio=payload.aspect_ratio,
    )

    images = []
    for r in results:
        img = GeneratedImage(
            project_id=payload.project_id,
            filename=r["filename"],
            prompt=r["prompt"],
            label="Custom Generation",
            size=f"{r.get('width', payload.width)}x{r.get('height', payload.height)}",
            provider=selected,
            lora_model_id=lora_id,
        )
        db.add(img)
        await db.flush()
        await db.refresh(img)
        images.append(img)

    return images


@router.post("/from-art-direction", response_model=list[GeneratedImageOut], status_code=201)
async def generate_from_art_direction(payload: ImageFromArtDirectionRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.project_id == payload.project_id, AgentRun.agent_role == AgentRole.ART_DIRECTOR, AgentRun.status == RunStatus.COMPLETED)
        .order_by(AgentRun.created_at.desc())
    )
    art_run = result.scalars().first()
    if not art_run or not art_run.output_data:
        raise HTTPException(404, "No completed Art Director run found. Run the Art Director agent first.")

    art_text = art_run.output_data.get("content", "")
    if not art_text:
        raise HTTPException(400, "Art Director output is empty.")

    # Check for client LoRA
    from app.models.models import Project
    project = await db.get(Project, payload.project_id)
    lora_url = None
    lora_id = None
    if project:
        lora_result = await db.execute(
            select(LoRAModel).where(LoRAModel.client_id == project.client_id, LoRAModel.status == "ready").order_by(LoRAModel.version.desc())
        )
        lora = lora_result.scalars().first()
        if lora:
            lora_url = lora.weights_url
            lora_id = lora.id

    selected = select_provider(lora_url=lora_url, preferred=payload.provider)
    gen_results = await generate_images_from_art_direction(art_text, lora_url=lora_url, provider=payload.provider)

    images = []
    for r in gen_results:
        if "error" in r:
            continue
        img = GeneratedImage(
            project_id=payload.project_id,
            agent_run_id=art_run.id,
            filename=r["filename"],
            prompt=r["prompt"],
            label=r.get("label", "Art Direction Image"),
            size=f"{r.get('width', 1024)}x{r.get('height', 1024)}",
            provider=selected,
            lora_model_id=lora_id,
        )
        db.add(img)
        await db.flush()
        await db.refresh(img)
        images.append(img)

    if not images:
        raise HTTPException(500, "All image generations failed.")
    return images


@router.post("/{image_id}/score", response_model=GeneratedImageOut)
async def score_single_image(image_id: str, db: AsyncSession = Depends(get_db)):
    """Run quality scoring on a single image against the client's Brand Bible."""
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")

    from app.models.models import Project
    project = await db.get(Project, img.project_id) if img.project_id else None
    bible_dict = {}
    brief_dict = {}
    thresholds = None

    if project:
        bible_r = await db.execute(select(BrandBible).where(BrandBible.client_id == project.client_id))
        bible = bible_r.scalar_one_or_none()
        if bible:
            from app.services.pipeline import _serialize_brand_bible
            bible_dict = _serialize_brand_bible(bible)

        brief_r = await db.execute(select(Brief).where(Brief.project_id == project.id))
        brief = brief_r.scalar_one_or_none()
        if brief:
            brief_dict = {"objective": brief.objective, "target_audience": brief.target_audience, "key_messages": brief.key_messages, "tone": brief.tone}

    scores = await score_image(img.filename, img.prompt, bible_dict, brief_dict, thresholds)
    img.quality_score = scores.get("composite_score", 0)
    img.quality_breakdown = scores
    if not scores.get("passed", False):
        img.is_rejected = True
        img.rejection_reason = "; ".join(scores.get("issues", ["Below threshold"]))
    await db.flush()
    await db.refresh(img)
    return img


@router.get("", response_model=list[GeneratedImageOut])
async def list_images(project_id: str | None = None, db: AsyncSession = Depends(get_db)):
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
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    filepath = IMAGES_DIR / img.filename
    if not filepath.exists():
        raise HTTPException(404, "Image file not found on disk")
    return FileResponse(filepath, media_type="image/png", filename=img.filename)


@router.patch("/{image_id}/approve", response_model=GeneratedImageOut)
async def approve_image(image_id: str, db: AsyncSession = Depends(get_db)):
    img = await db.get(GeneratedImage, image_id)
    if not img:
        raise HTTPException(404, "Image not found")
    img.is_approved = True
    img.is_rejected = False

    # Auto-capture to creative memory
    if img.project_id:
        from app.models.models import Project
        project = await db.get(Project, img.project_id)
        if project:
            from app.services.creative_memory import auto_capture_from_approval
            await auto_capture_from_approval(db, project.client_id, image=img)

    await db.flush()
    await db.refresh(img)
    return img


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
