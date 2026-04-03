from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.models import Project, Client
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectOut, ProjectDetail

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectOut])
async def list_projects(
    client_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Project).order_by(Project.created_at.desc())
    if client_id:
        query = query.where(Project.client_id == client_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(payload: ProjectCreate, db: AsyncSession = Depends(get_db)):
    client = await db.get(Client, payload.client_id)
    if not client:
        raise HTTPException(404, "Client not found")
    project = Project(**payload.model_dump())
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectDetail)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.client), selectinload(Project.brief))
    )
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(404, "Project not found")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, payload: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
    await db.flush()
    await db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    project = await db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Project not found")
    await db.delete(project)
    await db.flush()
