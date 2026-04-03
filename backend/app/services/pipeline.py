import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AgentRole, AgentRun, Brief, Client, Deliverable, Project,
    ProjectStatus, RunStatus,
)
from app.agents.registry import get_agent

logger = logging.getLogger(__name__)

DEFAULT_PIPELINE = [
    AgentRole.RESEARCHER,
    AgentRole.STRATEGIST,
    AgentRole.BRAND_VOICE,
    AgentRole.COPYWRITER,
    AgentRole.ART_DIRECTOR,
    AgentRole.CREATIVE_DIRECTOR,
]


async def _build_context(db: AsyncSession, project_id: str) -> dict:
    """Build the full context dict for agents from the database."""
    project = await db.get(Project, project_id, options=[selectinload(Project.client)])
    if not project:
        raise ValueError(f"Project {project_id} not found")

    brief_result = await db.execute(
        select(Brief).where(Brief.project_id == project_id)
    )
    brief = brief_result.scalar_one_or_none()
    if not brief:
        raise ValueError(f"No brief found for project {project_id}")

    client = project.client
    return {
        "client": {
            "name": client.name,
            "industry": client.industry,
            "brand_guidelines": client.brand_guidelines,
            "tone_keywords": client.tone_keywords,
            "target_audience": client.target_audience,
        },
        "brief": {
            "objective": brief.objective,
            "deliverables_description": brief.deliverables_description,
            "target_audience": brief.target_audience,
            "key_messages": brief.key_messages,
            "tone": brief.tone,
            "constraints": brief.constraints,
            "inspiration": brief.inspiration,
            "additional_context": brief.additional_context,
        },
        "prior_outputs": {},
    }


async def run_single_agent(
    db: AsyncSession,
    project_id: str,
    agent_role: AgentRole,
    input_data: dict | None = None,
) -> AgentRun:
    """Run a single agent against a project."""
    context = await _build_context(db, project_id)
    if input_data:
        context["input_data"] = input_data

    # Load prior outputs from completed runs on this project
    prior_runs = await db.execute(
        select(AgentRun)
        .where(AgentRun.project_id == project_id, AgentRun.status == RunStatus.COMPLETED)
        .order_by(AgentRun.created_at)
    )
    for run in prior_runs.scalars():
        if run.output_data:
            context["prior_outputs"][run.agent_role.value] = run.output_data.get("content", "")

    agent = get_agent(agent_role)

    agent_run = AgentRun(
        project_id=project_id,
        agent_role=agent_role,
        status=RunStatus.RUNNING,
        input_data=input_data,
    )
    db.add(agent_run)
    await db.flush()

    try:
        result = await agent.run(context)
        agent_run.status = RunStatus.COMPLETED
        agent_run.output_data = {"content": result["content"]}
        agent_run.tokens_used = result.get("tokens_used")
        agent_run.duration_seconds = result.get("duration_seconds")
        agent_run.completed_at = datetime.utcnow()

        deliverable = Deliverable(
            project_id=project_id,
            agent_run_id=agent_run.id,
            title=f"{agent_role.value.replace('_', ' ').title()} Output",
            content_type=agent_role.value,
            content=result["content"],
        )
        db.add(deliverable)

    except Exception as e:
        logger.exception(f"Agent {agent_role.value} failed")
        agent_run.status = RunStatus.FAILED
        agent_run.error_message = str(e)
        agent_run.completed_at = datetime.utcnow()

    await db.flush()
    return agent_run


async def run_pipeline(
    db: AsyncSession,
    project_id: str,
    agents: list[AgentRole] | None = None,
) -> list[AgentRun]:
    """Run a full pipeline of agents sequentially, each building on prior outputs."""
    if agents is None:
        agents = DEFAULT_PIPELINE

    project = await db.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    project.status = ProjectStatus.IN_PROGRESS
    await db.flush()

    runs: list[AgentRun] = []
    for role in agents:
        run = await run_single_agent(db, project_id, role)
        runs.append(run)
        if run.status == RunStatus.FAILED:
            logger.warning(f"Pipeline stopping: {role.value} failed")
            break

    all_succeeded = all(r.status == RunStatus.COMPLETED for r in runs)
    project.status = ProjectStatus.REVIEW if all_succeeded else ProjectStatus.IN_PROGRESS
    await db.flush()

    return runs
