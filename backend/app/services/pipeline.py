"""6-Stage Creative Pipeline — mirrors a real agency's process.

Stage 1: Strategic Framing (Strategist)
Stage 2: Concept Exploration (Creative Director — 10-20 concepts)
Stage 3: Art Direction (Art Director — detailed visual briefs for top concepts)
Stage 4: Visual Generation (Designer — Flux + LoRA image generation)
Stage 5: Refinement (Designer — compositing, finishing)
Stage 6: Quality Scoring (automated scoring against Brand Bible)
"""
import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.models import (
    AgentRole, AgentRun, Brief, BrandBible, Client, Deliverable,
    GeneratedImage, LoRAModel, Project, PipelineStage,
    ProjectStatus, RunStatus, ServiceBlueprint,
)
from app.agents.registry import get_agent
from app.services.creative_memory import get_client_memory_context, auto_capture_from_approval
from app.services.image_gen import generate_image, generate_images_from_art_direction
from app.services.quality_scoring import score_image, score_copy
from app.services.event_bus import event_bus
from app.services.finishing import batch_finish
from app.services.agent_protocol import create_handoff_message, send_message

logger = logging.getLogger(__name__)

FULL_PIPELINE = [
    (PipelineStage.STRATEGIC_FRAMING, AgentRole.STRATEGIST),
    (PipelineStage.CONCEPT_EXPLORATION, AgentRole.CREATIVE_DIRECTOR),
    (PipelineStage.ART_DIRECTION, AgentRole.ART_DIRECTOR),
    (PipelineStage.VISUAL_GENERATION, AgentRole.DESIGNER),
    (PipelineStage.REFINEMENT, AgentRole.COPYWRITER),
    (PipelineStage.QUALITY_SCORING, AgentRole.QUALITY_SCORER),
]

# Backward-compatible flat list for individual agent runs
DEFAULT_AGENT_ORDER = [
    AgentRole.RESEARCHER,
    AgentRole.STRATEGIST,
    AgentRole.BRAND_VOICE,
    AgentRole.CREATIVE_DIRECTOR,
    AgentRole.ART_DIRECTOR,
    AgentRole.COPYWRITER,
    AgentRole.DESIGNER,
]


async def build_context(db: AsyncSession, project_id: str) -> dict:
    """Build the full context dict for agents from the database, including Brand Bible and creative memory."""
    project = await db.get(Project, project_id, options=[selectinload(Project.client)])
    if not project:
        raise ValueError(f"Project {project_id} not found")

    brief_result = await db.execute(select(Brief).where(Brief.project_id == project_id))
    brief = brief_result.scalar_one_or_none()
    if not brief:
        raise ValueError(f"No brief found for project {project_id}")

    client = project.client

    # Load Brand Bible
    bible_result = await db.execute(select(BrandBible).where(BrandBible.client_id == client.id))
    bible = bible_result.scalar_one_or_none()

    # Load Service Blueprint
    bp_result = await db.execute(select(ServiceBlueprint).where(ServiceBlueprint.client_id == client.id))
    blueprint = bp_result.scalar_one_or_none()

    # Load active LoRA
    lora_result = await db.execute(
        select(LoRAModel)
        .where(LoRAModel.client_id == client.id, LoRAModel.status == "ready")
        .order_by(LoRAModel.version.desc())
    )
    active_lora = lora_result.scalars().first()

    # Load creative memory
    memory_context = await get_client_memory_context(db, client.id)

    context = {
        "client": {
            "id": client.id,
            "name": client.name,
            "industry": client.industry,
        },
        "brand_bible": _serialize_brand_bible(bible) if bible else {},
        "brief": {
            "objective": brief.objective,
            "deliverables_description": brief.deliverables_description,
            "target_audience": brief.target_audience,
            "key_messages": brief.key_messages,
            "tone": brief.tone,
            "constraints": brief.constraints,
            "inspiration": brief.inspiration,
            "additional_context": brief.additional_context,
            "desired_emotional_response": brief.desired_emotional_response,
            "mandatory_inclusions": brief.mandatory_inclusions,
            "competitive_differentiation": brief.competitive_differentiation,
            "output_formats": brief.output_formats,
        },
        "service_blueprint": {
            "template_type": blueprint.template_type.value if blueprint else None,
            "active_services": blueprint.active_services if blueprint else None,
            "quality_thresholds": blueprint.quality_thresholds if blueprint else None,
        } if blueprint else {},
        "lora": {
            "model_id": active_lora.id,
            "weights_url": active_lora.weights_url,
            "trigger_word": active_lora.trigger_word,
        } if active_lora else None,
        "creative_memory": memory_context,
        "prior_outputs": {},
    }

    return context


def _serialize_brand_bible(bible: BrandBible) -> dict:
    return {
        "brand_essence": bible.brand_essence,
        "mission": bible.mission,
        "vision": bible.vision,
        "values": bible.values,
        "positioning_statement": bible.positioning_statement,
        "unique_selling_proposition": bible.unique_selling_proposition,
        "primary_audience": bible.primary_audience,
        "secondary_audience": bible.secondary_audience,
        "audience_personas": bible.audience_personas,
        "color_palette": bible.color_palette,
        "typography": bible.typography,
        "photography_style": bible.photography_style,
        "illustration_style": bible.illustration_style,
        "composition_rules": bible.composition_rules,
        "logo_usage": bible.logo_usage,
        "visual_dos": bible.visual_dos,
        "visual_donts": bible.visual_donts,
        "tone_of_voice": bible.tone_of_voice,
        "voice_attributes": bible.voice_attributes,
        "vocabulary_preferences": bible.vocabulary_preferences,
        "vocabulary_avoid": bible.vocabulary_avoid,
        "headline_style": bible.headline_style,
        "copy_style": bible.copy_style,
        "competitors": bible.competitors,
        "differentiation": bible.differentiation,
        "social_guidelines": bible.social_guidelines,
        "email_guidelines": bible.email_guidelines,
        "print_guidelines": bible.print_guidelines,
        "web_guidelines": bible.web_guidelines,
    }


async def run_single_agent(
    db: AsyncSession,
    project_id: str,
    agent_role: AgentRole,
    input_data: dict | None = None,
    pipeline_stage: PipelineStage | None = None,
) -> AgentRun:
    """Run a single agent against a project with full Brand Bible context."""
    context = await build_context(db, project_id)
    if input_data:
        context["input_data"] = input_data

    # Load prior outputs from completed runs
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
        pipeline_stage=pipeline_stage,
        status=RunStatus.RUNNING,
        input_data=input_data,
    )
    db.add(agent_run)
    await db.flush()

    await event_bus.publish_task_started(project_id, agent_run.id, agent_role.value)

    try:
        result = await agent.run(context)
        agent_run.status = RunStatus.COMPLETED
        agent_run.output_data = {"content": result["content"]}
        agent_run.tokens_used = result.get("tokens_used")
        agent_run.duration_seconds = result.get("duration_seconds")
        agent_run.completed_at = datetime.utcnow()

        stage_label = pipeline_stage.value.replace("_", " ").title() if pipeline_stage else agent_role.value.replace("_", " ").title()
        deliverable = Deliverable(
            project_id=project_id,
            agent_run_id=agent_run.id,
            title=f"{stage_label} — {agent_role.value.replace('_', ' ').title()}",
            content_type=agent_role.value,
            content=result["content"],
            pipeline_stage=pipeline_stage.value if pipeline_stage else None,
        )
        db.add(deliverable)

        await event_bus.publish_task_completed(project_id, agent_run.id, result["content"][:300])

    except Exception as e:
        logger.exception(f"Agent {agent_role.value} failed")
        agent_run.status = RunStatus.FAILED
        agent_run.error_message = str(e)
        agent_run.completed_at = datetime.utcnow()
        await event_bus.publish(project_id, {"type": "task_failed", "agent_role": agent_role.value, "error": str(e)[:200]})

    await db.flush()
    return agent_run


async def run_creative_pipeline(
    db: AsyncSession,
    project_id: str,
    generate_images: bool = True,
    run_quality_scoring: bool = True,
) -> list[AgentRun]:
    """Execute the full 6-stage creative pipeline."""
    project = await db.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    project.status = ProjectStatus.IN_PROGRESS
    await db.flush()

    runs: list[AgentRun] = []

    # Stage 1: Strategic Framing
    logger.info("Pipeline Stage 1: Strategic Framing")
    run = await run_single_agent(db, project_id, AgentRole.STRATEGIST, pipeline_stage=PipelineStage.STRATEGIC_FRAMING)
    runs.append(run)
    if run.status == RunStatus.FAILED:
        return runs
    await send_message(db, create_handoff_message("strategist", "creative_director", project_id, "Strategy complete", run.output_data.get("content", "")[:500] if run.output_data else ""))

    # Stage 2: Concept Exploration (Creative Director generates 10-20 concepts)
    logger.info("Pipeline Stage 2: Concept Exploration")
    run = await run_single_agent(
        db, project_id, AgentRole.CREATIVE_DIRECTOR,
        input_data={"mode": "concept_exploration", "num_concepts": 15},
        pipeline_stage=PipelineStage.CONCEPT_EXPLORATION,
    )
    runs.append(run)
    if run.status == RunStatus.FAILED:
        return runs
    await send_message(db, create_handoff_message("creative_director", "art_director", project_id, "Concepts ready — top 5 selected", run.output_data.get("content", "")[:500] if run.output_data else ""))

    # Stage 3: Art Direction (detailed visual briefs for top concepts)
    logger.info("Pipeline Stage 3: Art Direction")
    run = await run_single_agent(
        db, project_id, AgentRole.ART_DIRECTOR,
        pipeline_stage=PipelineStage.ART_DIRECTION,
    )
    runs.append(run)
    if run.status == RunStatus.FAILED:
        return runs
    await send_message(db, create_handoff_message("art_director", "designer", project_id, "Art direction briefs ready for visual generation", run.output_data.get("content", "")[:500] if run.output_data else ""))

    # Stage 4: Visual Generation (Designer + Flux + LoRA)
    if generate_images:
        logger.info("Pipeline Stage 4: Visual Generation")
        context = await build_context(db, project_id)
        art_direction_text = run.output_data.get("content", "") if run.output_data else ""
        lora_url = context["lora"]["weights_url"] if context.get("lora") else None

        try:
            image_results = await generate_images_from_art_direction(art_direction_text, lora_url=lora_url)

            for r in image_results:
                if "error" in r:
                    continue
                img = GeneratedImage(
                    project_id=project_id,
                    agent_run_id=run.id,
                    filename=r["filename"],
                    prompt=r["prompt"],
                    label=r.get("label", "Pipeline Image"),
                    size=f"{r.get('width', 1024)}x{r.get('height', 1024)}",
                    lora_model_id=context["lora"]["model_id"] if context.get("lora") else None,
                )
                db.add(img)
            await db.flush()

            # Run finishing pipeline on generated images
            finished_count = 0
            bible = context.get("brand_bible", {})
            for r in image_results:
                if "error" in r:
                    continue
                try:
                    batch_finish(r["filename"], bible)
                    finished_count += 1
                    await event_bus.publish_image_generated(project_id, r["filename"], r.get("label", ""))
                except Exception as fe:
                    logger.warning(f"Finishing failed for {r.get('filename')}: {fe}")

            successful_count = len([r for r in image_results if "error" not in r])
            designer_run = AgentRun(
                project_id=project_id,
                agent_role=AgentRole.DESIGNER,
                pipeline_stage=PipelineStage.VISUAL_GENERATION,
                status=RunStatus.COMPLETED,
                output_data={"content": f"Generated {successful_count} images, finished {finished_count}.", "image_count": successful_count, "finished_count": finished_count},
                completed_at=datetime.utcnow(),
            )
            db.add(designer_run)
            runs.append(designer_run)
            await db.flush()
        except Exception as e:
            logger.error(f"Visual generation failed: {e}")
            designer_run = AgentRun(
                project_id=project_id,
                agent_role=AgentRole.DESIGNER,
                pipeline_stage=PipelineStage.VISUAL_GENERATION,
                status=RunStatus.FAILED,
                error_message=str(e),
                completed_at=datetime.utcnow(),
            )
            db.add(designer_run)
            runs.append(designer_run)
            await db.flush()

    # Stage 5: Refinement (Copywriter for headlines, CTAs, channel-specific copy)
    logger.info("Pipeline Stage 5: Refinement — Copy")
    run = await run_single_agent(
        db, project_id, AgentRole.COPYWRITER,
        pipeline_stage=PipelineStage.REFINEMENT,
    )
    runs.append(run)

    if run.status == RunStatus.COMPLETED and run.output_data:
        copy_text = run.output_data.get("content", "")
        if copy_text:
            try:
                context = await build_context(db, project_id)
                copy_scores = await score_copy(
                    copy_text,
                    context.get("brand_bible", {}),
                    context.get("brief"),
                )
                copy_deliverables = await db.execute(
                    select(Deliverable).where(
                        Deliverable.agent_run_id == run.id,
                    )
                )
                for deliv in copy_deliverables.scalars():
                    deliv.metadata_json = {**(deliv.metadata_json or {}), "copy_score": copy_scores}
                await db.flush()
                logger.info("Copy scored: composite=%.1f", copy_scores.get("composite_score", 0))
            except Exception as e:
                logger.error("Copy scoring failed: %s", e)

    # Stage 6: Quality Scoring
    if run_quality_scoring:
        logger.info("Pipeline Stage 6: Quality Scoring")
        context = await build_context(db, project_id)
        bible = context.get("brand_bible", {})
        brief_ctx = context.get("brief", {})
        thresholds = context.get("service_blueprint", {}).get("quality_thresholds")

        image_results = await db.execute(
            select(GeneratedImage)
            .where(GeneratedImage.project_id == project_id, GeneratedImage.quality_score.is_(None))
        )
        scored_count = 0
        for img in image_results.scalars():
            try:
                scores = await score_image(img.filename, img.prompt, bible, brief_ctx, thresholds)
                img.quality_score = scores.get("composite_score", 0)
                img.quality_breakdown = scores
                if not scores.get("passed", False):
                    img.is_rejected = True
                    img.rejection_reason = "; ".join(scores.get("issues", ["Below threshold"]))
                scored_count += 1
                await event_bus.publish_quality_scored(project_id, img.id, img.quality_score)
            except Exception as e:
                logger.error(f"Scoring failed for image {img.id}: {e}")

        scorer_run = AgentRun(
            project_id=project_id,
            agent_role=AgentRole.QUALITY_SCORER,
            pipeline_stage=PipelineStage.QUALITY_SCORING,
            status=RunStatus.COMPLETED,
            output_data={"content": f"Scored {scored_count} images against Brand Bible.", "scored_count": scored_count},
            completed_at=datetime.utcnow(),
        )
        db.add(scorer_run)
        runs.append(scorer_run)
        await db.flush()

    all_succeeded = all(r.status == RunStatus.COMPLETED for r in runs)
    project.status = ProjectStatus.REVIEW if all_succeeded else ProjectStatus.IN_PROGRESS
    await db.flush()

    return runs


async def run_agent_pipeline(
    db: AsyncSession,
    project_id: str,
    agents: list[AgentRole] | None = None,
    generate_images: bool = False,
) -> list[AgentRun]:
    """Run a list of agents sequentially (simpler than the full 6-stage pipeline)."""
    if agents is None:
        agents = DEFAULT_AGENT_ORDER

    project = await db.get(Project, project_id)
    if not project:
        raise ValueError(f"Project {project_id} not found")

    project.status = ProjectStatus.IN_PROGRESS
    await db.flush()

    runs: list[AgentRun] = []
    for role in agents:
        if role == AgentRole.DESIGNER and generate_images:
            # For Designer, trigger image generation instead of text
            context = await build_context(db, project_id)
            lora_url = context["lora"]["weights_url"] if context.get("lora") else None

            # Get art direction from prior runs
            art_text = context["prior_outputs"].get("art_director", "")
            if art_text:
                try:
                    image_results = await generate_images_from_art_direction(art_text, lora_url=lora_url)
                    for r in image_results:
                        if "error" not in r:
                            img = GeneratedImage(
                                project_id=project_id, filename=r["filename"],
                                prompt=r["prompt"], label=r.get("label"),
                                size=f"{r.get('width', 1024)}x{r.get('height', 1024)}",
                            )
                            db.add(img)
                    await db.flush()
                except Exception as e:
                    logger.error(f"Image generation failed: {e}")
            continue

        if role == AgentRole.QUALITY_SCORER:
            continue  # Handled separately

        run = await run_single_agent(db, project_id, role)
        runs.append(run)
        if run.status == RunStatus.FAILED:
            break

    all_succeeded = all(r.status == RunStatus.COMPLETED for r in runs)
    project.status = ProjectStatus.REVIEW if all_succeeded else ProjectStatus.IN_PROGRESS
    await db.flush()

    return runs
