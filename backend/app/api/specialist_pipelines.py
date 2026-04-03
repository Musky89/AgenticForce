"""API endpoints for specialist pipelines — print production and virtual garment."""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Project, GeneratedImage, LoRAModel
from app.services.print_production import (
    get_templates, prepare_for_print, generate_print_spec_sheet,
)
from app.services.garment_pipeline import (
    analyze_fabric, run_garment_pipeline,
)
from app.services.pipeline import build_context

router = APIRouter(prefix="/pipelines", tags=["specialist-pipelines"])

IMAGES_DIR = Path(__file__).parent.parent.parent / "generated_images"
EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports"


# --- Print Production ---

@router.get("/print/templates")
async def list_print_templates():
    return get_templates()


class PrintPrepRequest(BaseModel):
    image_id: str
    template_name: str


@router.post("/print/prepare")
async def prepare_print(payload: PrintPrepRequest, db: AsyncSession = Depends(get_db)):
    """Prepare an image for print: resize, CMYK conversion, bleed marks."""
    img = await db.get(GeneratedImage, payload.image_id)
    if not img:
        raise HTTPException(404, "Image not found")

    result = prepare_for_print(img.filename, payload.template_name)
    return result


class PrintSpecRequest(BaseModel):
    project_id: str
    template_name: str
    notes: str = ""


@router.post("/print/spec-sheet")
async def create_spec_sheet(payload: PrintSpecRequest, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    filename = generate_print_spec_sheet(project.name, payload.template_name, payload.notes)
    return FileResponse(EXPORTS_DIR / filename, media_type="application/pdf", filename=filename)


# --- Virtual Garment Pipeline ---

class FabricAnalyzeRequest(BaseModel):
    image_path: str  # filename in generated_images/


@router.post("/garment/analyze-fabric")
async def api_analyze_fabric(payload: FabricAnalyzeRequest):
    """Analyze a fabric swatch image using GPT-4o Vision."""
    result = await analyze_fabric(payload.image_path)
    return result


class GarmentPipelineRequest(BaseModel):
    project_id: str
    fabric_image_path: str
    garment_types: list[str] | None = None
    num_concepts: int = 4
    provider: str | None = None


@router.post("/garment/run")
async def run_garment(payload: GarmentPipelineRequest, db: AsyncSession = Depends(get_db)):
    """Run the full garment pipeline: analyze → concepts → generate images."""
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    context = await build_context(db, payload.project_id)
    lora_url = context["lora"]["weights_url"] if context.get("lora") else None

    result = await run_garment_pipeline(
        fabric_image_path=payload.fabric_image_path,
        brand_context=context,
        lora_url=lora_url,
        garment_types=payload.garment_types,
        num_concepts=payload.num_concepts,
        provider=payload.provider,
    )

    # Persist generated images
    for img_data in result.get("images", []):
        if "error" in img_data:
            continue
        img = GeneratedImage(
            project_id=payload.project_id,
            filename=img_data["filename"],
            prompt=img_data["prompt"],
            label=img_data.get("label", "Garment"),
            size=f"{img_data.get('width', 1024)}x{img_data.get('height', 1344)}",
            provider=img_data.get("provider", "flux"),
            lora_model_id=context["lora"]["model_id"] if context.get("lora") else None,
        )
        db.add(img)
    await db.flush()

    return {
        "fabric_analysis": result["fabric_analysis"],
        "concepts_count": len(result["concepts"]),
        "images_generated": result["successful_count"],
        "images_failed": result["failed_count"],
    }
