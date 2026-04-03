from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session
from app.models.models import AgentRun, AgentRole, RunStatus
from app.schemas.schemas import AgentRunRequest, AgentRunOut, PipelineRunRequest, PipelineRunOut
from app.services.pipeline import run_single_agent, run_pipeline

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/roles")
async def list_roles():
    return [
        {"value": r.value, "label": r.value.replace("_", " ").title()}
        for r in AgentRole
    ]


@router.post("/run", response_model=AgentRunOut)
async def execute_agent(payload: AgentRunRequest, db: AsyncSession = Depends(get_db)):
    run = await run_single_agent(
        db, payload.project_id, payload.agent_role, payload.input_data
    )
    return run


@router.post("/pipeline", response_model=PipelineRunOut)
async def execute_pipeline(payload: PipelineRunRequest, db: AsyncSession = Depends(get_db)):
    runs = await run_pipeline(db, payload.project_id, payload.agents)
    return PipelineRunOut(
        project_id=payload.project_id,
        runs=[AgentRunOut.model_validate(r) for r in runs],
    )


@router.get("/runs", response_model=list[AgentRunOut])
async def list_runs(
    project_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(AgentRun).order_by(AgentRun.created_at.desc())
    if project_id:
        query = query.where(AgentRun.project_id == project_id)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=AgentRunOut)
async def get_run(run_id: str, db: AsyncSession = Depends(get_db)):
    run = await db.get(AgentRun, run_id)
    if not run:
        raise HTTPException(404, "Agent run not found")
    return run
