"""Orchestration Engine — decomposes briefs into task graphs, manages dependencies,
inserts founder review checkpoints, and drives agent execution.

The brief says: "When the founder creates a brief, the orchestration layer analyses
it and decomposes into agent-level tasks automatically."
"""
import logging
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import (
    AgentRole, Brief, Project, Task, TaskStatus, ReviewItem, ReviewStatus,
    PipelineStage, Deliverable, GeneratedImage, AgentRun, RunStatus,
)
from app.services.pipeline import run_single_agent, build_context
from app.services.image_gen import generate_image, generate_images_from_art_direction
from app.services.quality_scoring import score_image

logger = logging.getLogger(__name__)

PIPELINE_TASK_DEFS = [
    {
        "stage": PipelineStage.STRATEGIC_FRAMING,
        "role": AgentRole.STRATEGIST,
        "title": "Strategic Framing",
        "description": "Analyse brief → audience insight, key message, emotional response, competitive differentiation, tone",
        "requires_review": True,
        "depends_on_indices": [],
    },
    {
        "stage": PipelineStage.CONCEPT_EXPLORATION,
        "role": AgentRole.CREATIVE_DIRECTOR,
        "title": "Concept Exploration",
        "description": "Generate 10-20 conceptual directions spanning safe to provocative. Curate top 5.",
        "requires_review": True,
        "depends_on_indices": [0],
    },
    {
        "stage": PipelineStage.ART_DIRECTION,
        "role": AgentRole.ART_DIRECTOR,
        "title": "Art Direction",
        "description": "Develop detailed visual briefs + image generation prompts for top concepts.",
        "requires_review": True,
        "depends_on_indices": [1],
    },
    {
        "stage": PipelineStage.VISUAL_GENERATION,
        "role": AgentRole.DESIGNER,
        "title": "Visual Generation",
        "description": "Generate visuals via Flux/Imagen using art direction + client LoRA.",
        "requires_review": True,
        "depends_on_indices": [2],
    },
    {
        "stage": PipelineStage.REFINEMENT,
        "role": AgentRole.COPYWRITER,
        "title": "Copy & Refinement",
        "description": "Channel-specific headlines, body copy, CTAs, text overlay specs.",
        "requires_review": False,
        "depends_on_indices": [1],  # parallel with art direction output
    },
    {
        "stage": PipelineStage.QUALITY_SCORING,
        "role": AgentRole.QUALITY_SCORER,
        "title": "Quality Scoring",
        "description": "Automated brand quality evaluation on all generated visuals.",
        "requires_review": False,
        "depends_on_indices": [3],
    },
]


async def decompose_brief(db: AsyncSession, project_id: str) -> list[Task]:
    """Decompose a project brief into an ordered task graph with dependencies."""
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    brief_result = await db.execute(select(Brief).where(Brief.project_id == project_id))
    brief = brief_result.scalar_one_or_none()
    if not brief:
        raise ValueError("No brief found for this project")

    # Clear existing tasks for re-decomposition
    existing = await db.execute(select(Task).where(Task.project_id == project_id))
    for t in existing.scalars():
        await db.delete(t)
    await db.flush()

    tasks: list[Task] = []
    for i, defn in enumerate(PIPELINE_TASK_DEFS):
        task = Task(
            project_id=project_id,
            agent_role=defn["role"],
            pipeline_stage=defn["stage"],
            title=defn["title"],
            description=defn["description"],
            status=TaskStatus.READY if not defn["depends_on_indices"] else TaskStatus.BLOCKED,
            sort_order=i,
            requires_review=defn["requires_review"],
        )
        db.add(task)
        tasks.append(task)

    await db.flush()

    # Set dependency references now that tasks have IDs
    for i, defn in enumerate(PIPELINE_TASK_DEFS):
        dep_ids = [tasks[j].id for j in defn["depends_on_indices"]]
        if dep_ids:
            tasks[i].depends_on = dep_ids

    await db.flush()
    logger.info(f"Decomposed brief for project {project_id} into {len(tasks)} tasks")
    return tasks


async def get_task_graph(db: AsyncSession, project_id: str) -> list[Task]:
    """Get all tasks for a project, ordered."""
    result = await db.execute(
        select(Task).where(Task.project_id == project_id).order_by(Task.sort_order)
    )
    return list(result.scalars().all())


async def execute_next_task(db: AsyncSession, project_id: str) -> Task | None:
    """Find and execute the next READY task in the pipeline."""
    result = await db.execute(
        select(Task)
        .where(Task.project_id == project_id, Task.status == TaskStatus.READY)
        .order_by(Task.sort_order)
    )
    task = result.scalars().first()
    if not task:
        return None

    task.status = TaskStatus.IN_PROGRESS
    task.started_at = datetime.utcnow()
    await db.flush()

    try:
        if task.agent_role == AgentRole.DESIGNER:
            await _execute_visual_generation(db, task)
        elif task.agent_role == AgentRole.QUALITY_SCORER:
            await _execute_quality_scoring(db, task)
        else:
            input_data = None
            if task.agent_role == AgentRole.CREATIVE_DIRECTOR:
                input_data = {"mode": "concept_exploration", "num_concepts": 15}

            run = await run_single_agent(
                db, project_id, task.agent_role,
                input_data=input_data,
                pipeline_stage=task.pipeline_stage,
            )
            task.agent_run_id = run.id

            if run.status == RunStatus.FAILED:
                task.status = TaskStatus.FAILED
            elif task.requires_review:
                task.status = TaskStatus.AWAITING_REVIEW
                # Create review item
                deliverable_result = await db.execute(
                    select(Deliverable)
                    .where(Deliverable.agent_run_id == run.id)
                    .order_by(Deliverable.created_at.desc())
                )
                deliverable = deliverable_result.scalars().first()
                review = ReviewItem(
                    project_id=project_id,
                    task_id=task.id,
                    deliverable_id=deliverable.id if deliverable else None,
                    title=f"Review: {task.title}",
                    item_type=task.pipeline_stage.value if task.pipeline_stage else "general",
                )
                db.add(review)
            else:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.utcnow()
                await _unblock_dependents(db, project_id, task.id)

    except Exception as e:
        logger.exception(f"Task {task.id} ({task.title}) failed")
        task.status = TaskStatus.FAILED

    await db.flush()
    return task


async def approve_task(db: AsyncSession, task_id: str, feedback: str | None = None) -> Task:
    """Founder approves a task, unblocking dependents."""
    task = await db.get(Task, task_id)
    if not task:
        raise ValueError("Task not found")

    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    await db.flush()

    # Update associated review items
    reviews = await db.execute(
        select(ReviewItem).where(ReviewItem.task_id == task_id, ReviewItem.status == ReviewStatus.PENDING)
    )
    for review in reviews.scalars():
        review.status = ReviewStatus.APPROVED
        review.feedback = feedback
        review.reviewed_at = datetime.utcnow()

    await _unblock_dependents(db, task.project_id, task.id)
    await db.flush()
    return task


async def request_revision(db: AsyncSession, task_id: str, feedback: str) -> Task:
    """Founder requests revision, re-queuing the task."""
    task = await db.get(Task, task_id)
    if not task:
        raise ValueError("Task not found")

    task.status = TaskStatus.READY  # Will be re-executed
    await db.flush()

    reviews = await db.execute(
        select(ReviewItem).where(ReviewItem.task_id == task_id, ReviewItem.status == ReviewStatus.PENDING)
    )
    for review in reviews.scalars():
        review.status = ReviewStatus.REVISION_REQUESTED
        review.feedback = feedback
        review.reviewed_at = datetime.utcnow()

    await db.flush()
    return task


async def _unblock_dependents(db: AsyncSession, project_id: str, completed_task_id: str):
    """Unblock tasks that depend on the completed task."""
    all_tasks = await db.execute(
        select(Task).where(Task.project_id == project_id, Task.status == TaskStatus.BLOCKED)
    )
    for task in all_tasks.scalars():
        if not task.depends_on:
            continue
        if completed_task_id not in task.depends_on:
            continue

        # Check if ALL dependencies are completed
        deps_result = await db.execute(
            select(Task).where(Task.id.in_(task.depends_on))
        )
        all_deps_complete = all(
            d.status in (TaskStatus.COMPLETED, TaskStatus.APPROVED)
            for d in deps_result.scalars()
        )
        if all_deps_complete:
            task.status = TaskStatus.READY
            logger.info(f"Unblocked task: {task.title}")


async def _execute_visual_generation(db: AsyncSession, task: Task):
    """Handle visual generation task (Flux/Imagen + LoRA)."""
    context = await build_context(db, task.project_id)
    lora_url = context["lora"]["weights_url"] if context.get("lora") else None

    # Get art direction from prior completed runs
    art_text = context["prior_outputs"].get("art_director", "")
    if not art_text:
        task.status = TaskStatus.FAILED
        return

    try:
        results = await generate_images_from_art_direction(art_text, lora_url=lora_url)
        image_count = 0
        for r in results:
            if "error" in r:
                continue
            img = GeneratedImage(
                project_id=task.project_id,
                filename=r["filename"],
                prompt=r["prompt"],
                label=r.get("label", "Pipeline Image"),
                size=f"{r.get('width', 1024)}x{r.get('height', 1024)}",
                provider=r.get("provider", "flux"),
                lora_model_id=context["lora"]["model_id"] if context.get("lora") else None,
            )
            db.add(img)
            image_count += 1

        # Create synthetic agent run
        run = AgentRun(
            project_id=task.project_id,
            agent_role=AgentRole.DESIGNER,
            pipeline_stage=PipelineStage.VISUAL_GENERATION,
            status=RunStatus.COMPLETED,
            output_data={"content": f"Generated {image_count} images.", "image_count": image_count},
            completed_at=datetime.utcnow(),
        )
        db.add(run)
        await db.flush()
        task.agent_run_id = run.id

        if task.requires_review:
            task.status = TaskStatus.AWAITING_REVIEW
            # Add images to review queue
            images_result = await db.execute(
                select(GeneratedImage).where(GeneratedImage.project_id == task.project_id).order_by(GeneratedImage.created_at.desc()).limit(image_count)
            )
            for img in images_result.scalars():
                review = ReviewItem(
                    project_id=task.project_id,
                    task_id=task.id,
                    image_id=img.id,
                    title=f"Review: {img.label or 'Generated Image'}",
                    item_type="visual",
                )
                db.add(review)
        else:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            await _unblock_dependents(db, task.project_id, task.id)

    except Exception as e:
        logger.error(f"Visual generation failed: {e}")
        task.status = TaskStatus.FAILED


async def _execute_quality_scoring(db: AsyncSession, task: Task):
    """Score all unscored images for the project."""
    context = await build_context(db, task.project_id)
    bible = context.get("brand_bible", {})
    brief_ctx = context.get("brief", {})
    thresholds = context.get("service_blueprint", {}).get("quality_thresholds")

    results = await db.execute(
        select(GeneratedImage)
        .where(GeneratedImage.project_id == task.project_id, GeneratedImage.quality_score.is_(None))
    )
    scored = 0
    for img in results.scalars():
        try:
            scores = await score_image(img.filename, img.prompt, bible, brief_ctx, thresholds)
            img.quality_score = scores.get("composite_score", 0)
            img.quality_breakdown = scores
            if not scores.get("passed", False):
                img.is_rejected = True
                img.rejection_reason = "; ".join(scores.get("issues", ["Below threshold"]))
            scored += 1
        except Exception as e:
            logger.error(f"Scoring failed for image {img.id}: {e}")

    run = AgentRun(
        project_id=task.project_id,
        agent_role=AgentRole.QUALITY_SCORER,
        pipeline_stage=PipelineStage.QUALITY_SCORING,
        status=RunStatus.COMPLETED,
        output_data={"content": f"Scored {scored} images against Brand Bible.", "scored_count": scored},
        completed_at=datetime.utcnow(),
    )
    db.add(run)
    await db.flush()
    task.agent_run_id = run.id
    task.status = TaskStatus.COMPLETED
    task.completed_at = datetime.utcnow()
    await _unblock_dependents(db, task.project_id, task.id)
