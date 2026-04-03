from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Project, Client, Deliverable, AgentRun, RunStatus
from app.services.export import export_strategy_pdf, export_concept_pptx, export_deliverables_pdf

router = APIRouter(prefix="/export", tags=["export"])

EXPORTS_DIR = Path(__file__).parent.parent.parent / "exports"


@router.post("/strategy/{project_id}")
async def export_strategy(project_id: str, db: AsyncSession = Depends(get_db)):
    """Export strategy deliverables as a polished PDF."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    client = await db.get(Client, project.client_id)

    # Get strategy + research content
    runs = await db.execute(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.status == RunStatus.COMPLETED)
        .order_by(AgentRun.created_at)
    )
    strategy_text = ""
    research_text = None
    for run in runs.scalars():
        if run.agent_role.value == "strategist" and run.output_data:
            strategy_text = run.output_data.get("content", "")
        elif run.agent_role.value == "researcher" and run.output_data:
            research_text = run.output_data.get("content", "")

    if not strategy_text:
        raise HTTPException(404, "No strategy output found. Run the Strategist agent first.")

    filename = export_strategy_pdf(client.name, project.name, strategy_text, research_text)
    return FileResponse(EXPORTS_DIR / filename, media_type="application/pdf", filename=filename)


@router.post("/concepts/{project_id}")
async def export_concepts(project_id: str, db: AsyncSession = Depends(get_db)):
    """Export creative concepts as a PPTX presentation."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    client = await db.get(Client, project.client_id)

    runs = await db.execute(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.status == RunStatus.COMPLETED)
        .order_by(AgentRun.created_at)
    )
    concepts_text = ""
    art_direction_text = None
    for run in runs.scalars():
        if run.agent_role.value == "creative_director" and run.output_data:
            concepts_text = run.output_data.get("content", "")
        elif run.agent_role.value == "art_director" and run.output_data:
            art_direction_text = run.output_data.get("content", "")

    if not concepts_text:
        raise HTTPException(404, "No concept output found. Run the Creative Director agent first.")

    filename = export_concept_pptx(client.name, project.name, concepts_text, art_direction_text)
    return FileResponse(
        EXPORTS_DIR / filename,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )


@router.post("/deliverables/{project_id}")
async def export_all_deliverables(project_id: str, db: AsyncSession = Depends(get_db)):
    """Export all approved deliverables as a consolidated PDF."""
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    client = await db.get(Client, project.client_id)

    result = await db.execute(
        select(Deliverable)
        .where(Deliverable.project_id == project_id)
        .order_by(Deliverable.created_at)
    )
    deliverables = [
        {"title": d.title, "content": d.content, "pipeline_stage": d.pipeline_stage}
        for d in result.scalars()
    ]

    if not deliverables:
        raise HTTPException(404, "No deliverables found.")

    filename = export_deliverables_pdf(client.name, project.name, deliverables)
    return FileResponse(EXPORTS_DIR / filename, media_type="application/pdf", filename=filename)
