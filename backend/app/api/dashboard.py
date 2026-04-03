from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import Client, Project, AgentRun, Deliverable, GeneratedImage, LoRAModel, ProjectStatus
from app.schemas.schemas import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    clients = (await db.execute(select(func.count(Client.id)))).scalar() or 0
    projects = (await db.execute(select(func.count(Project.id)))).scalar() or 0
    in_progress = (await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.IN_PROGRESS))).scalar() or 0
    delivered = (await db.execute(select(func.count(Project.id)).where(Project.status == ProjectStatus.DELIVERED))).scalar() or 0
    runs = (await db.execute(select(func.count(AgentRun.id)))).scalar() or 0
    deliverables_count = (await db.execute(select(func.count(Deliverable.id)))).scalar() or 0
    images_count = (await db.execute(select(func.count(GeneratedImage.id)))).scalar() or 0
    lora_count = (await db.execute(select(func.count(LoRAModel.id)))).scalar() or 0

    return DashboardStats(
        total_clients=clients,
        total_projects=projects,
        projects_in_progress=in_progress,
        projects_delivered=delivered,
        total_agent_runs=runs,
        total_deliverables=deliverables_count,
        total_images=images_count,
        total_lora_models=lora_count,
    )
