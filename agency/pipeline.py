from __future__ import annotations

from .agents import BrandGuardianAgent, CreativeDirectorAgent, StrategistAgent, format_bullets
from .models import ClientBrief, PhaseOnePackage, StrategyOutput, utc_now_iso
from .vision import build_vision_blueprint


class PhaseOneOrchestrator:
    def __init__(self) -> None:
        self.strategist = StrategistAgent()
        self.creative_director = CreativeDirectorAgent()
        self.brand_guardian = BrandGuardianAgent()

    def run(self, vision_doc_path: str, vision_doc_text: str, brief: ClientBrief) -> PhaseOnePackage:
        vision = build_vision_blueprint(vision_doc_path, vision_doc_text)
        strategy = self.strategist.run(vision, brief)
        creative = self.creative_director.run(brief, strategy, routes=3)
        quality = self.brand_guardian.run(vision, brief, strategy, creative)
        return PhaseOnePackage(
            generated_at=utc_now_iso(),
            vision=vision,
            brief=brief,
            strategy=strategy,
            creative=creative,
            quality_gate=quality,
        )


def strategy_markdown(strategy: StrategyOutput) -> str:
    personas_md = []
    for persona in strategy.personas:
        personas_md.append(
            "\n".join(
                [
                    f"### {persona.name} ({persona.role})",
                    "",
                    "Pains:",
                    format_bullets(persona.pains),
                    "",
                    "Motivations:",
                    format_bullets(persona.motivations),
                    "",
                    "Decision Triggers:",
                    format_bullets(persona.decision_triggers),
                ]
            )
        )

    territories_md = []
    for territory in strategy.territories:
        territories_md.append(
            "\n".join(
                [
                    f"### {territory.name}",
                    f"**Insight:** {territory.insight}",
                    f"**Proposition:** {territory.proposition}",
                    f"**Emotional Outcome:** {territory.emotional_outcome}",
                    "",
                    "Proof Points:",
                    format_bullets(territory.proof_points),
                ]
            )
        )

    return "\n\n".join(
        [
            "# Phase 1 Strategy Output",
            "",
            "## Positioning Statement",
            strategy.positioning_statement,
            "",
            "## Messaging Pillars",
            format_bullets(strategy.messaging_pillars),
            "",
            "## Competitive Gaps",
            format_bullets(strategy.competitor_gaps),
            "",
            "## Personas",
            "\n\n".join(personas_md),
            "",
            "## Strategic Territories",
            "\n\n".join(territories_md),
            "",
            "## Campaign Brief",
            "```text",
            strategy.campaign_brief,
            "```",
        ]
    )


def creative_markdown(package: PhaseOnePackage) -> str:
    route_sections = []
    for route in package.creative.concept_presentations:
        channel_lines = "\n".join(f"- **{k}**: {v}" for k, v in route.channel_expressions.items())
        route_sections.append(
            "\n".join(
                [
                    f"## {route.route_name}",
                    f"**Strategic Territory:** {route.strategic_territory}",
                    f"**Big Idea:** {route.big_idea}",
                    "",
                    "### Taglines",
                    format_bullets(route.taglines),
                    "",
                    "### Visual Direction",
                    format_bullets(route.visual_direction),
                    "",
                    "### Copy Direction",
                    format_bullets(route.copy_direction),
                    "",
                    "### Channel Expressions",
                    channel_lines,
                ]
            )
        )

    return "\n\n".join(
        [
            "# Phase 1 Creative Development",
            "",
            "## Concept Routes",
            "\n\n".join(route_sections),
            "",
            "## Moodboard Prompts",
            format_bullets(package.creative.moodboard_prompts),
            "",
            "## Art Direction Notes",
            format_bullets(package.creative.art_direction_notes),
            "",
            "## Quality Gate",
            f"- **Approved:** {package.quality_gate.approved}",
            f"- **Score:** {package.quality_gate.score}",
            "- **Checks:**",
            "\n".join(f"  - {k}: {v}" for k, v in package.quality_gate.checks.items()),
            "",
            "### Strengths",
            format_bullets(package.quality_gate.strengths),
            "",
            "### Issues",
            format_bullets(package.quality_gate.issues or ["None"]),
            "",
            "### Next Actions",
            format_bullets(package.quality_gate.next_actions),
        ]
    )
