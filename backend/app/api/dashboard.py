from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Client, Project, AgentRun, Deliverable, ProjectStatus
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    clients = await db.execute(select(func.count(Client.id)))
    projects = await db.execute(select(func.count(Project.id)))
    in_progress = await db.execute(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.IN_PROGRESS)
    )
    delivered = await db.execute(
        select(func.count(Project.id)).where(Project.status == ProjectStatus.DELIVERED)
    )
    runs = await db.execute(select(func.count(AgentRun.id)))
    deliverables_count = await db.execute(select(func.count(Deliverable.id)))

    return DashboardStats(
        total_clients=clients.scalar() or 0,
        total_projects=projects.scalar() or 0,
        projects_in_progress=in_progress.scalar() or 0,
        projects_delivered=delivered.scalar() or 0,
        total_agent_runs=runs.scalar() or 0,
        total_deliverables=deliverables_count.scalar() or 0,
    )
