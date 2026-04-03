from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.models import AgentRun, AgentRole, RunStatus, PipelineStage
from app.schemas.schemas import AgentRunRequest, AgentRunOut, PipelineRunRequest, AgentListRunRequest, PipelineRunOut
from app.services.pipeline import run_single_agent, run_creative_pipeline, run_agent_pipeline

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/roles")
async def list_roles():
    return [{"value": r.value, "label": r.value.replace("_", " ").title()} for r in AgentRole]


@router.get("/pipeline-stages")
async def list_pipeline_stages():
    return [{"value": s.value, "label": s.value.replace("_", " ").title()} for s in PipelineStage]


@router.post("/run", response_model=AgentRunOut)
async def execute_agent(payload: AgentRunRequest, db: AsyncSession = Depends(get_db)):
    run = await run_single_agent(db, payload.project_id, payload.agent_role, payload.input_data)
    return run


@router.post("/pipeline", response_model=PipelineRunOut)
async def execute_creative_pipeline(payload: PipelineRunRequest, db: AsyncSession = Depends(get_db)):
    """Execute the full 6-stage creative pipeline: Strategy → Concepts → Art Direction → Visuals → Copy → Scoring."""
    runs = await run_creative_pipeline(
        db, payload.project_id, payload.generate_images, payload.run_quality_scoring
    )
    return PipelineRunOut(
        project_id=payload.project_id,
        runs=[AgentRunOut.model_validate(r) for r in runs],
    )


@router.post("/agent-list", response_model=PipelineRunOut)
async def execute_agent_list(payload: AgentListRunRequest, db: AsyncSession = Depends(get_db)):
    """Run a custom list of agents sequentially."""
    runs = await run_agent_pipeline(db, payload.project_id, payload.agents, payload.generate_images)
    return PipelineRunOut(
        project_id=payload.project_id,
        runs=[AgentRunOut.model_validate(r) for r in runs],
    )


@router.get("/runs", response_model=list[AgentRunOut])
async def list_runs(project_id: str | None = None, db: AsyncSession = Depends(get_db)):
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
