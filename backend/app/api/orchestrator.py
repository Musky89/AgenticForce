from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.database import get_db
from app.models.models import Task, TaskStatus
from app.services.orchestrator import (
    decompose_brief, get_task_graph, execute_next_task,
    approve_task, request_revision,
)

router = APIRouter(prefix="/orchestrator", tags=["orchestrator"])


class TaskOut(BaseModel):
    id: str
    project_id: str
    agent_role: str
    pipeline_stage: str | None
    title: str
    description: str | None
    status: str
    sort_order: int
    depends_on: list[str] | None
    requires_review: bool
    agent_run_id: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None

    model_config = {"from_attributes": True}


class DecomposeResponse(BaseModel):
    project_id: str
    tasks: list[TaskOut]


class ReviewAction(BaseModel):
    feedback: str | None = None


@router.post("/decompose/{project_id}", response_model=DecomposeResponse)
async def decompose(project_id: str, db: AsyncSession = Depends(get_db)):
    """Decompose a brief into an orchestrated task graph."""
    tasks = await decompose_brief(db, project_id)
    return DecomposeResponse(
        project_id=project_id,
        tasks=[TaskOut.model_validate(t) for t in tasks],
    )


@router.get("/tasks/{project_id}", response_model=list[TaskOut])
async def list_tasks(project_id: str, db: AsyncSession = Depends(get_db)):
    tasks = await get_task_graph(db, project_id)
    return [TaskOut.model_validate(t) for t in tasks]


@router.post("/execute/{project_id}", response_model=TaskOut | None)
async def execute_next(project_id: str, db: AsyncSession = Depends(get_db)):
    """Execute the next ready task in the pipeline."""
    task = await execute_next_task(db, project_id)
    if not task:
        return None
    return TaskOut.model_validate(task)


@router.post("/execute-all/{project_id}", response_model=list[TaskOut])
async def execute_all_ready(project_id: str, db: AsyncSession = Depends(get_db)):
    """Execute all currently ready tasks (respects dependencies and review gates)."""
    executed = []
    for _ in range(20):
        task = await execute_next_task(db, project_id)
        if not task:
            break
        executed.append(TaskOut.model_validate(task))
        if task.status.value == "awaiting_review":
            break
    return executed


@router.post("/approve/{task_id}", response_model=TaskOut)
async def approve(task_id: str, action: ReviewAction, db: AsyncSession = Depends(get_db)):
    """Approve a task, unblocking dependent tasks."""
    task = await approve_task(db, task_id, action.feedback)
    return TaskOut.model_validate(task)


@router.post("/revise/{task_id}", response_model=TaskOut)
async def revise(task_id: str, action: ReviewAction, db: AsyncSession = Depends(get_db)):
    """Request revision — re-queues the task for re-execution."""
    if not action.feedback:
        raise HTTPException(400, "Feedback is required for revision requests")
    task = await request_revision(db, task_id, action.feedback)
    return TaskOut.model_validate(task)
