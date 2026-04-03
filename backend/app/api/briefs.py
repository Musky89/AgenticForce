from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Brief, Project, ProjectStatus
from app.schemas.schemas import BriefCreate, BriefUpdate, BriefOut

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.post("", response_model=BriefOut, status_code=201)
async def create_brief(payload: BriefCreate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, payload.project_id)
    if not project:
        raise HTTPException(404, "Project not found")

    existing = await db.execute(
        select(Brief).where(Brief.project_id == payload.project_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Brief already exists for this project. Use PATCH to update.")

    brief = Brief(**payload.model_dump())
    db.add(brief)

    project.status = ProjectStatus.BRIEFED
    await db.flush()
    await db.refresh(brief)
    return brief


@router.get("/{brief_id}", response_model=BriefOut)
async def get_brief(brief_id: str, db: AsyncSession = Depends(get_db)):
    brief = await db.get(Brief, brief_id)
    if not brief:
        raise HTTPException(404, "Brief not found")
    return brief


@router.get("/project/{project_id}", response_model=BriefOut)
async def get_brief_by_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Brief).where(Brief.project_id == project_id)
    )
    brief = result.scalar_one_or_none()
    if not brief:
        raise HTTPException(404, "Brief not found for this project")
    return brief


@router.patch("/{brief_id}", response_model=BriefOut)
async def update_brief(brief_id: str, payload: BriefUpdate, db: AsyncSession = Depends(get_db)):
    brief = await db.get(Brief, brief_id)
    if not brief:
        raise HTTPException(404, "Brief not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(brief, k, v)
    await db.flush()
    await db.refresh(brief)
    return brief
